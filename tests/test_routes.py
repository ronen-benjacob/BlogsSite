"""
Tests for blog routes:
- Home page
- Individual post pages
- About and Contact pages
- Admin-only routes
"""
import pytest
from main import db, BlogPost


class TestPublicRoutes:
    """Test publicly accessible routes."""
    
    def test_home_page_loads(self, client):
        """Test that the home page loads successfully."""
        response = client.get('/')
        assert response.status_code == 200
    
    def test_home_page_shows_blog_posts(self, client, test_blog_post):
        """Test that blog posts are displayed on home page."""
        response = client.get('/')
        assert response.status_code == 200
        assert test_blog_post['title'].encode() in response.data
    
    def test_about_page_loads(self, client):
        """Test that the about page loads successfully."""
        response = client.get('/about')
        assert response.status_code == 200
        assert b'About' in response.data or b'about' in response.data
    
    def test_contact_page_loads(self, client):
        """Test that the contact page loads successfully."""
        response = client.get('/contact')
        assert response.status_code == 200
        assert b'Contact' in response.data or b'contact' in response.data
    
    def test_individual_post_page_loads(self, client, test_blog_post):
        """Test that individual blog post pages load correctly."""
        response = client.get(f'/{test_blog_post["id"]}')
        assert response.status_code == 200
        assert test_blog_post['title'].encode() in response.data
        assert test_blog_post['body'].encode() in response.data
    
    def test_nonexistent_post_returns_404(self, client):
        """Test that accessing non-existent post returns 404."""
        response = client.get('/99999')
        assert response.status_code == 404


class TestAdminRoutes:
    """Test admin-only routes and permissions."""
    
    def test_new_post_page_requires_admin(self, client, test_user):
        """Test that non-admin users cannot access new post page."""
        # Login as regular user (not admin)
        client.post('/login', data={
            'email': test_user['email'],
            'password': test_user['password']
        })
        
        response = client.get('/new-post')
        assert response.status_code == 403  # Forbidden
    
    def test_admin_can_access_new_post_page(self, authenticated_admin_client):
        """Test that admin user can access new post page."""
        response = authenticated_admin_client.get('/new-post')
        assert response.status_code == 200
        assert b'Create Post' in response.data or b'New Post' in response.data
    
    def test_edit_post_requires_admin(self, client, test_user, test_blog_post):
        """Test that non-admin users cannot edit posts."""
        # Login as regular user
        client.post('/login', data={
            'email': test_user['email'],
            'password': test_user['password']
        })
        
        response = client.get(f'/edit-post/{test_blog_post["id"]}')
        assert response.status_code == 403
    
    def test_admin_can_access_edit_post_page(self, authenticated_admin_client, test_blog_post):
        """Test that admin user can access edit post page."""
        response = authenticated_admin_client.get(f'/edit-post/{test_blog_post["id"]}')
        assert response.status_code == 200
        assert test_blog_post['title'].encode() in response.data
    
    def test_delete_post_requires_admin(self, client, test_user, test_blog_post):
        """Test that non-admin users cannot delete posts."""
        # Login as regular user
        client.post('/login', data={
            'email': test_user['email'],
            'password': test_user['password']
        })
        
        response = client.get(f'/delete-post/{test_blog_post["id"]}')
        assert response.status_code == 403
    
    def test_unauthenticated_user_cannot_access_admin_routes(self, client):
        """Test that unauthenticated users get 403 on admin routes."""
        assert client.get('/new-post').status_code == 403
        assert client.get('/edit-post/1').status_code in [403, 404]
        assert client.get('/delete-post/1').status_code in [403, 404]


class TestComments:
    """Test comment functionality."""
    
    def test_authenticated_user_can_view_comment_form(self, authenticated_client, test_blog_post):
        """Test that logged-in users see the comment form."""
        response = authenticated_client.get(f'/{test_blog_post["id"]}')
        assert response.status_code == 200
        # Should show comment form or textarea
        assert b'comment' in response.data.lower() or b'textarea' in response.data.lower()
    
    def test_authenticated_user_can_post_comment(self, authenticated_client, test_blog_post, app):
        """Test that authenticated users can post comments."""
        response = authenticated_client.post(f'/{test_blog_post["id"]}', data={
            'text': 'This is a test comment!'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'test comment' in response.data
    
    def test_unauthenticated_user_cannot_post_comment(self, client, test_blog_post):
        """Test that unauthenticated users cannot post comments."""
        response = client.post(f'/{test_blog_post["id"]}', data={
            'text': 'This should not work!'
        }, follow_redirects=True)
        
        # Should redirect to login or show error
        assert b'log in' in response.data.lower() or b'login' in response.data.lower()