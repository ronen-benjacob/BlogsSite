import pytest
import os
import sys
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash

# Prevent .env file from affecting test database configuration
# Set a flag to indicate we're in test mode, then unset SQLALCHEMY_DATABASE_URI
# so main.py will use SQLite default when imported
os.environ['PYTEST_CURRENT_TEST'] = '1'  # Flag to indicate test mode
_original_db_uri = os.environ.pop('SQLALCHEMY_DATABASE_URI', None)

# Add parent directory to path so we can import main
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app as flask_app, db, User, BlogPost, Comment

# Choose database based on environment variable
USE_POSTGRES = os.environ.get('TEST_WITH_POSTGRES', 'false').lower() == 'true'

@pytest.fixture(scope='function')
def app():
    """Create and configure a test Flask application instance."""
    
    if USE_POSTGRES:
        # Use PostgreSQL for integration tests
        test_db_uri = os.environ.get(
            'TEST_DATABASE_URI',
            'postgresql://blog_user:blog_password_123@localhost:5432/blog_test_db'
        )
        print(f"\n🐘 Running tests with PostgreSQL: {test_db_uri}")
    else:
        # Use SQLite for fast unit tests (default)
        test_db_uri = 'sqlite:///:memory:'
        print("\n⚡ Running tests with SQLite (in-memory)")
    
    # Set up test configuration
    flask_app.config.update({
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,  # Disable CSRF for testing
        'SQLALCHEMY_DATABASE_URI': test_db_uri,
        'SECRET_KEY': 'test-secret-key-for-testing-only',
    })
    
    # Create the database and tables
    with flask_app.app_context():
        db.create_all()
        yield flask_app
        
        # Cleanup
        db.session.remove()
        
        if USE_POSTGRES:
            # For PostgreSQL, drop all tables but keep the database
            db.drop_all()
        else:
            # For SQLite in-memory, just drop (database disappears automatically)
            db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """Create a test client for the Flask application."""
    return app.test_client()


@pytest.fixture(scope='function')
def runner(app):
    """Create a test CLI runner for the Flask application."""
    return app.test_cli_runner()


@pytest.fixture(scope='function')
def test_user(app, admin_user):
    """Create a test user in the database (ensures admin_user is created first)."""
    with app.app_context():
        user = User.query.filter_by(email='testuser@example.com').first()
        if not user:
            user = User(
                email='testuser@example.com',
                password=generate_password_hash('password123', method='scrypt', salt_length=16),
                name='Test User'
            )
            db.session.add(user)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                user = User.query.filter_by(email='testuser@example.com').first()
        if user is None:
            raise RuntimeError("Failed to create or retrieve test user.")
        # Ensure test_user is not id=1 (admin)
        if user.id == 1:
            # If somehow test_user got id=1, delete and recreate
            db.session.delete(user)
            db.session.commit()
            user = User(
                email='testuser@example.com',
                password=generate_password_hash('password123', method='scrypt', salt_length=16),
                name='Test User'
            )
            db.session.add(user)
            db.session.commit()
        db.session.refresh(user)
        user_id = user.id

    return {
        'id': user_id,
        'email': 'testuser@example.com',
        'password': 'password123',
        'name': 'Test User'
    }


@pytest.fixture(scope='function')
def admin_user(app):
    """Create an admin user (ID=1) in the database."""
    with app.app_context():
        admin = User.query.filter_by(id=1).first()
        if not admin:
            admin = User(
                id=1,
                email='admin@example.com',
                password=generate_password_hash('adminpass123', method='scrypt', salt_length=16),
                name='Admin User'
            )
            db.session.add(admin)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                admin = User.query.filter_by(id=1).first()
        if admin is None:
            raise RuntimeError("Failed to create or retrieve admin user.")
        db.session.refresh(admin)

    return {
        'id': admin.id,
        'email': 'admin@example.com',
        'password': 'adminpass123',
        'name': 'Admin User'
    }


@pytest.fixture(scope='function')
def test_blog_post(app, admin_user):
    """Create a test blog post in the database."""
    with app.app_context():
        post = BlogPost(
            title='Test Blog Post',
            subtitle='This is a test subtitle',
            date='January 01, 2024',
            body='This is the test blog post content.',
            author_id=admin_user['id'],
            img_url='https://example.com/test-image.jpg'
        )
        db.session.add(post)
        db.session.commit()
        
        db.session.refresh(post)
        post_id = post.id
        
    return {
        'id': post_id,
        'title': 'Test Blog Post',
        'subtitle': 'This is a test subtitle',
        'body': 'This is the test blog post content.',
    }


@pytest.fixture(scope='function')
def authenticated_client(client, test_user):
    """Create a client with an authenticated test user."""
    with client:
        client.post('/login', data={
            'email': test_user['email'],
            'password': test_user['password']
        }, follow_redirects=True)
        yield client


@pytest.fixture(scope='function')
def authenticated_admin_client(client, admin_user):
    """Create a client with an authenticated admin user."""
    with client:
        client.post('/login', data={
            'email': admin_user['email'],
            'password': admin_user['password']
        }, follow_redirects=True)
        yield client