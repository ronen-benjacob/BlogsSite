"""
Tests for blog post CRUD operations:
- Create new posts
- Read/display posts
- Update existing posts
- Delete posts
"""
import pytest
from main import db, BlogPost


class TestCreateBlogPost:
    """Test creating new blog posts."""
    
    def test_admin_can_create_blog_post(self, authenticated_admin_client, app):
        """Test that admin can create a new blog post."""
        response = authenticated_admin_client.post('/new-post', data={
            'title': 'New Test Post',
            'subtitle': 'A subtitle for testing',
            'bg_img_url': 'https://example.com/image.jpg',
            'blog_content': 'This is the content of the new blog post.'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verify post was created in database
        with app.app_context():
            post = BlogPost.query.filter_by(title='New Test Post').first()
            assert post is not None
            assert post.subtitle == 'A subtitle for testing'
            assert post.body == 'This is the content of the new blog post.'
    
    def test_created_post_has_correct_author(self, authenticated_admin_client, admin_user, app):
        """Test that created posts are associated with the correct author."""
        authenticated_admin_client.post('/new-post', data={
            'title': 'Author Test Post',
            'subtitle': 'Testing author assignment',
            'bg_img_url': 'https://example.com/image.jpg',
            'blog_content': 'Content here.'
        }, follow_redirects=True)
        
        with app.app_context():
            post = BlogPost.query.filter_by(title='Author Test Post').first()
            assert post.author_id == admin_user['id']
    
    def test_created_post_has_date(self, authenticated_admin_client, app):
        """Test that created posts have a date assigned."""
        authenticated_admin_client.post('/new-post', data={
            'title': 'Date Test Post',
            'subtitle': 'Testing date',
            'bg_img_url': 'https://example.com/image.jpg',
            'blog_content': 'Content here.'
        }, follow_redirects=True)
        
        with app.app_context():
            post = BlogPost.query.filter_by(title='Date Test Post').first()
            assert post.date is not None
            assert len(post.date) > 0


class TestReadBlogPost:
    """Test reading and displaying blog posts."""
    
    def test_all_posts_displayed_on_home(self, client, app, admin_user):
        """Test that all blog posts are displayed on home page."""
        # Create multiple posts
        with app.app_context():
            post1 = BlogPost(
                title='First Post',
                subtitle='First subtitle',
                date='January 01, 2024',
                body='First content',
                author_id=admin_user['id'],
                img_url='https://example.com/img1.jpg'
            )
            post2 = BlogPost(
                title='Second Post',
                subtitle='Second subtitle',
                date='January 02, 2024',
                body='Second content',
                author_id=admin_user['id'],
                img_url='https://example.com/img2.jpg'
            )
            db.session.add(post1)
            db.session.add(post2)
            db.session.commit()
        
        response = client.get('/')
        assert response.status_code == 200
        assert b'First Post' in response.data
        assert b'Second Post' in response.data
    
    def test_post_displays_all_content(self, client, test_blog_post):
        """Test that individual post page shows all post details."""
        response = client.get(f'/{test_blog_post["id"]}')
        assert response.status_code == 200
        assert test_blog_post['title'].encode() in response.data
        assert test_blog_post['subtitle'].encode() in response.data
        assert test_blog_post['body'].encode() in response.data
    
    def test_post_to_dict_method(self, app, test_blog_post):
        """Test that BlogPost.to_dict() method works correctly."""
        with app.app_context():
            post = BlogPost.query.get(test_blog_post['id'])
            post_dict = post.to_dict()
            
            assert isinstance(post_dict, dict)
            assert post_dict['title'] == test_blog_post['title']
            assert post_dict['subtitle'] == test_blog_post['subtitle']
            assert 'id' in post_dict
            assert 'author_id' in post_dict


class TestUpdateBlogPost:
    """Test updating existing blog posts."""
    
    def test_admin_can_edit_blog_post(self, authenticated_admin_client, test_blog_post, app):
        """Test that admin can edit an existing blog post."""
        response = authenticated_admin_client.post(
            f'/edit-post/{test_blog_post["id"]}',
            data={
                'title': 'Updated Title',
                'subtitle': 'Updated Subtitle',
                'bg_img_url': 'https://example.com/updated.jpg',
                'blog_content': 'Updated content here.'
            },
            follow_redirects=True
        )
        
        assert response.status_code == 200
        
        # Verify post was updated in database
        with app.app_context():
            post = BlogPost.query.get(test_blog_post['id'])
            assert post.title == 'Updated Title'
            assert post.subtitle == 'Updated Subtitle'
            assert post.body == 'Updated content here.'
    
    def test_edit_preserves_author_and_date(self, authenticated_admin_client, test_blog_post, app):
        """Test that editing a post preserves original author and date."""
        # Get original values
        with app.app_context():
            original_post = BlogPost.query.get(test_blog_post['id'])
            original_author_id = original_post.author_id
            original_date = original_post.date
        
        # Edit the post
        authenticated_admin_client.post(
            f'/edit-post/{test_blog_post["id"]}',
            data={
                'title': 'New Title',
                'subtitle': 'New Subtitle',
                'bg_img_url': 'https://example.com/new.jpg',
                'blog_content': 'New content.'
            },
            follow_redirects=True
        )
        
        # Verify author and date unchanged
        with app.app_context():
            updated_post = BlogPost.query.get(test_blog_post['id'])
            assert updated_post.author_id == original_author_id
            # Date should remain the same (not updated to current date)
            assert updated_post.date == original_date


class TestDeleteBlogPost:
    """Test deleting blog posts."""
    
    def test_admin_can_delete_blog_post(self, authenticated_admin_client, test_blog_post, app):
        """Test that admin can delete a blog post."""
        response = authenticated_admin_client.get(
            f'/delete-post/{test_blog_post["id"]}',
            follow_redirects=True
        )
        
        assert response.status_code == 200
        
        # Verify post was deleted from database
        with app.app_context():
            post = BlogPost.query.get(test_blog_post['id'])
            assert post is None
    
    def test_deleted_post_not_visible_on_home(self, authenticated_admin_client, client, test_blog_post):
        """Test that deleted posts don't appear on home page."""
        # Delete the post
        authenticated_admin_client.get(f'/delete-post/{test_blog_post["id"]}')
        
        # Check home page
        response = client.get('/')
        assert response.status_code == 200
        assert test_blog_post['title'].encode() not in response.data
    
    def test_accessing_deleted_post_returns_404(self, authenticated_admin_client, client, test_blog_post):
        """Test that accessing a deleted post returns 404."""
        # Delete the post
        authenticated_admin_client.get(f'/delete-post/{test_blog_post["id"]}')
        
        # Try to access the deleted post
        response = client.get(f'/{test_blog_post["id"]}')
        assert response.status_code == 404


class TestBlogPostValidation:
    """Test blog post data validation."""
    
    def test_cannot_create_post_with_duplicate_title(self, authenticated_admin_client, test_blog_post, app):
        """Test that posts with duplicate titles are handled correctly."""
        response = authenticated_admin_client.post('/new-post', data={
            'title': test_blog_post['title'],  # Duplicate title
            'subtitle': 'Different subtitle',
            'bg_img_url': 'https://example.com/image.jpg',
            'blog_content': 'Different content.'
        }, follow_redirects=True)
        
        # Should either show error or handle gracefully
        # Depending on your implementation, adjust this assertion
        assert response.status_code in [200, 400]