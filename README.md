# Flask Blog

A professional Flask blog application with comprehensive CI/CD pipeline.

## 🚀 Status Badges

![CI Pipeline](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/ci.yml/badge.svg)
![Integration Tests](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/integration.yml/badge.svg)
![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)
![Code Coverage](https://img.shields.io/badge/coverage-95%25-brightgreen.svg)
![Tests](https://img.shields.io/badge/tests-40%20passed-success.svg)

## 📋 Features

- User authentication (register, login, logout)
- Create, read, update, delete blog posts
- Comment on posts
- Admin-only post management
- Responsive design with Bootstrap
- CKEditor for rich text editing
- Gravatar integration

## 🧪 Testing

- **40 comprehensive tests**
- **95% code coverage**
- Automated testing with GitHub Actions
- Unit tests with SQLite
- Integration tests with PostgreSQL

## 🛠️ Tech Stack

- **Backend**: Flask 2.3.3, SQLAlchemy 2.0
- **Database**: PostgreSQL (production), SQLite (testing)
- **Frontend**: Bootstrap 5, Jinja2 templates
- **Testing**: pytest, pytest-flask
- **CI/CD**: GitHub Actions, Docker

## 🚀 Quick Start

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/ronen-benjacob/BlogsSite.git
cd BlogsSite

# Start the application
docker-compose up

# Access the blog
open http://localhost:5003
```

### Local Development

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export FLASK_KEY="your-secret-key"
export SQLALCHEMY_DATABASE_URI="your-database-url"

# Run the application
python main.py
```

## 🧪 Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_auth.py

# Run in Docker
docker-compose run --rm web pytest
```

## 📊 CI/CD Pipeline

Our CI/CD pipeline includes:

- ✅ Code linting (flake8, black)
- ✅ Unit tests (SQLite)
- ✅ Integration tests (PostgreSQL)
- ✅ Code coverage reporting (95%+)
- ✅ Multi-Python version testing (3.9-3.12)
- ✅ Security scanning
- ✅ Docker image building

## 📝 Project Structure

```
flask-blog/
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── integration.yml
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_blog_posts.py
│   └── test_routes.py
├── templates/
├── static/
├── main.py
├── forms.py
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License.

## 👨‍💻 Author

Your Name - [GitHub Profile](https://github.com/ronen-benjacob)

---
