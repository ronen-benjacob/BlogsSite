"""
Tests for authentication functionality:
- User registration
- User login
- User logout
- Password hashing
"""
import pytest
from main import db, User


class TestRegistration:
    """Test user registration functionality."""
    
    def test_register_page_loads(self, client):
        """Test that the registration page loads successfully."""
        response = client.get('/register')
        assert response.status_code == 200
        assert b'Register' in response.data or b'register' in response.data
    
    def test_successful_registration(self, client, app):
        """Test that a new user can register successfully."""
        response = client.post('/register', data={
            'email': 'newuser@example.com',
            'password': 'newpassword123',
            'name': 'New User'
        }, follow_redirects=True)
        
        # Should redirect to home page after successful registration
        assert response.status_code == 200
        
        # Check that user was created in database
        with app.app_context():
            user = User.query.filter_by(email='newuser@example.com').first()
            assert user is not None
            assert user.name == 'New User'
            # Password should be hashed, not plain text
            assert user.password != 'newpassword123'
    
    def test_duplicate_email_registration(self, client, test_user):
        """Test that registering with an existing email shows an error."""
        response = client.post('/register', data={
            'email': test_user['email'],  # Already exists
            'password': 'anotherpassword',
            'name': 'Another User'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'already exists' in response.data or b'Login instead' in response.data
    
    def test_registration_with_invalid_email(self, client):
        """Test registration with invalid email format."""
        response = client.post('/register', data={
            'email': 'notanemail',  # Invalid format
            'password': 'password123',
            'name': 'Test User'
        }, follow_redirects=False)
        
        # Should show validation error (form won't submit)
        assert response.status_code in [200, 400]


class TestLogin:
    """Test user login functionality."""
    
    def test_login_page_loads(self, client):
        """Test that the login page loads successfully."""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'Login' in response.data or b'login' in response.data
    
    def test_successful_login(self, client, test_user):
        """Test that a user can login with correct credentials."""
        response = client.post('/login', data={
            'email': test_user['email'],
            'password': test_user['password']
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Should redirect to home page
        assert b'Blog' in response.data or b'Posts' in response.data
    
    def test_login_with_wrong_password(self, client, test_user):
        """Test that login fails with incorrect password."""
        response = client.post('/login', data={
            'email': test_user['email'],
            'password': 'wrongpassword'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'not valid' in response.data or b'incorrect' in response.data.lower()
    
    def test_login_with_nonexistent_email(self, client):
        """Test that login fails with non-existent email."""
        response = client.post('/login', data={
            'email': 'nonexistent@example.com',
            'password': 'anypassword'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'not valid' in response.data or b'not found' in response.data.lower()
    
    def test_login_redirects_unauthenticated_user(self, client):
        """Test that accessing protected routes redirects to login."""
        response = client.get('/new-post', follow_redirects=False)
        # Should get 403 Forbidden or redirect
        assert response.status_code in [302, 303, 403]


class TestLogout:
    """Test user logout functionality."""
    
    def test_logout_redirects_to_home(self, authenticated_client):
        """Test that logout redirects to home page."""
        response = authenticated_client.get('/logout', follow_redirects=True)
        assert response.status_code == 200
    
    def test_user_cannot_access_protected_route_after_logout(self, authenticated_admin_client):
        """Test that user cannot access admin routes after logout."""
        # First logout
        authenticated_admin_client.get('/logout')
        
        # Try to access admin route
        response = authenticated_admin_client.get('/new-post', follow_redirects=False)
        assert response.status_code in [302, 303, 403]


class TestPasswordSecurity:
    """Test password hashing and security."""
    
    def test_password_is_hashed(self, app, test_user):
        """Test that passwords are stored hashed, not in plain text."""
        with app.app_context():
            user = User.query.filter_by(email=test_user['email']).first()
            # Password in DB should NOT equal plain text password
            assert user.password != test_user['password']
            # Should be a hash (contains special characters)
            assert len(user.password) > 50  # Hashes are long
    
    def test_password_hash_is_verifiable(self, app, test_user):
        """Test that hashed passwords can be verified correctly."""
        from werkzeug.security import check_password_hash
        
        with app.app_context():
            user = User.query.filter_by(email=test_user['email']).first()
            # Correct password should verify
            assert check_password_hash(user.password, test_user['password'])
            # Wrong password should not verify
            assert not check_password_hash(user.password, 'wrongpassword')