from datetime import date, datetime
from flask import Flask, render_template, redirect, url_for, flash, abort
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Text, ForeignKey
from sqlalchemy.exc import IntegrityError
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from forms import Add_Post_Form, Register_Form, Login_Form, Comment_Form
import os
import sys
from dotenv import load_dotenv

'''
On Windows type:
python -m pip install -r requirements.txt
'''

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_KEY')
# '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)

login_manager = LoginManager()
login_manager.init_app(app)

# CREATE DATABASE
class Base(DeclarativeBase):
    pass

# Detect if running in test mode (pytest sets PYTEST_CURRENT_TEST)
# In test mode, ignore any PostgreSQL URI from .env and use SQLite default
# so test fixtures can override it. In production/Docker, use environment variable.
_is_test_mode = 'PYTEST_CURRENT_TEST' in os.environ or 'pytest' in sys.modules
if _is_test_mode:
    # In test mode, ignore .env PostgreSQL config and default to SQLite in-memory
    # Test fixtures will override this with the appropriate test database
    db_uri = os.environ.get('SQLALCHEMY_DATABASE_URI')
    # If URI is set to PostgreSQL in test mode, ignore it and use SQLite default
    if db_uri and db_uri.startswith('postgresql://'):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = db_uri or 'sqlite:///:memory:'
else:
    # In production, use environment variable or SQLite file default
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI') or 'sqlite:///blog.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)

# CK Editor
ckeditor = CKEditor(app)
app.config['CKEDITOR_PKG_TYPE'] = 'full'

# Gravatar
gravatar = Gravatar(app,
                size=100,
                rating='g',
                default='retro',
                force_default=False,
                force_lower=False,
                use_ssl=False,
                base_url=None)

# CONFIGURE TABLES
class BlogPost(db.Model):     
    __tablename__ = "blog_posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)        
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)    
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))    
    author: Mapped["User"] = relationship(back_populates="blogs")    
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)
    comments: Mapped[list["Comment"]] = relationship(back_populates="blog_post")

    def to_dict(self):                        
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}
    
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)    
    email: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(250), nullable=False)
    name: Mapped[str] = mapped_column(String(250), nullable=False)    
    blogs: Mapped[list["BlogPost"]] = relationship(back_populates="author")
    comments: Mapped[list["Comment"]] = relationship(back_populates="author")

    def to_dict(self):                        
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}
    
class Comment(UserMixin, db.Model):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)            
    text: Mapped[str] = mapped_column(Text, nullable=False)    
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))    
    author: Mapped["User"] = relationship(back_populates="comments")   
    blog_post_id: Mapped[int] = mapped_column(ForeignKey("blog_posts.id"))    
    blog_post: Mapped["BlogPost"] = relationship(back_populates="comments")             

    def to_dict(self):                        
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

def init_database() -> None:
    """Ensure all database tables exist."""
    with app.app_context():
        db.create_all()

# Decorators
def admin_only(func):
    @wraps(func)
    def wrapper_function(*args, **kwargs):
        # Do something BEFORE the original function runs
        print(current_user)
        if current_user.is_authenticated and current_user.id == 1:
        
            # Call the original function and store its result
            result = func(*args, **kwargs)
            
            # Return the original function's result
            return result
        
        else:
            # Do something AFTER the original function runs
            abort(403)
        
    # The decorator returns the new wrapper function
    return wrapper_function

# Users endpoints
@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)

@app.route('/register', methods=["GET", "POST"])
def register():    
    register_form = Register_Form()
    if register_form.validate_on_submit():

        # Get the form register info
        email = register_form.email.data
        password = register_form.password.data
        name = register_form.name.data

        # Check if the user's email already exist in the DB
        existing_user = User.query.filter_by(email=email).first()         
        # db.session.execute(db.select(User).where(User.email == email)).scalar()
        if existing_user:
            # Show error
            flash(f'Email {email} already exists! Login instead.')            
            return redirect('login')
        else:
            # Encrypt the password - Hash incl. salt the user's password
            hashed_password = generate_password_hash(
                password, 
                method='scrypt', 
                salt_length=16
            )

            # Save the user in the DB
            new_user = User(        
                email = email,
                password = hashed_password,        
                name = name,
            )
            db.session.add(new_user)
            db.session.commit()

            # Login the newly registered user
            login_user(new_user)

            # Redirect the user to the Secrets page
            return redirect(url_for('get_all_posts'))
    
    return render_template(template_name_or_list='register.html', form=register_form)

@app.route('/login', methods=["GET", "POST"])
def login():    
    login_form = Login_Form()

    if login_form.validate_on_submit():
        # Login and validate the user.        
        email = login_form.email.data
        password = login_form.password.data

        # Validate if the email exists
        user = User.query.filter_by(email=email).first()         
        
        if not user:
            flash('Credentials are not valid!')
            return redirect('login')            

        # Validate the user's credentials
        logged_db_user = User.query.filter_by(email=email).first()                      
        hashed_password_from_db = logged_db_user.password  # This is the hashed password stored in DB
    
        # Check if password matches
        if check_password_hash(hashed_password_from_db, password):            
            login_user(logged_db_user)            
            return redirect(url_for('get_all_posts'))
        else:
            flash('Credentials are not valid!')
            return redirect(url_for('login')) 
    
    # Handling "GET" method - show the Login page
    return render_template('login.html', form=login_form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))    

# Blog Posts endpoints
@app.route('/')
def get_all_posts():    
    all_posts = db.session.execute(db.select(BlogPost)).scalars().all()        
    return render_template("index.html", all_posts=all_posts, curr_year=datetime.now().year)

@app.route('/<int:post_id>', methods=["GET", "POST"])
def show_post(post_id):    
    comment_form = Comment_Form()
    if comment_form.validate_on_submit():
        if current_user.is_authenticated:
            new_comment = Comment(
                text = comment_form.text.data,
                author_id = current_user.id,
                blog_post_id = post_id,
            )
            db.session.add(new_comment)
            db.session.commit()
            return redirect(url_for('show_post', post_id=post_id))
        else:
            flash("You need to log in to the site in order to comment on blog posts.")
            return redirect(url_for('login'))
    
    requested_post = db.session.get(BlogPost, post_id)
    if requested_post is None:
        abort(404)

    return render_template("post.html", post=requested_post, form=comment_form)

@app.route('/new-post', methods=["GET", "POST"])
@admin_only
def new_post():
    add_post_form = Add_Post_Form()
    if add_post_form.validate_on_submit():
        new_blog_post = BlogPost()
        new_blog_post.author_id = current_user.id
        new_blog_post.title = add_post_form.title.data
        new_blog_post.subtitle = add_post_form.subtitle.data        
        new_blog_post.img_url = add_post_form.bg_img_url.data
        new_blog_post.body = add_post_form.blog_content.data
        new_blog_post.date = date.today().strftime("%B %d, %Y")
        db.session.add(new_blog_post)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("A blog post with that title already exists. Please choose a different title.")
            return render_template(template_name_or_list='make-post.html', form=add_post_form), 400
        except Exception:
            db.session.rollback()
            raise
        return redirect(location=url_for('get_all_posts'))
    return render_template(template_name_or_list='make-post.html', form=add_post_form)

@app.route('/edit-post/<int:post_id>', methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    edited_post = db.get_or_404(BlogPost, post_id)  
    add_post_form = Add_Post_Form()
    if add_post_form.validate_on_submit():
        edited_post.title = add_post_form.title.data
        edited_post.subtitle = add_post_form.subtitle.data        
        edited_post.img_url = add_post_form.bg_img_url.data
        edited_post.body = add_post_form.blog_content.data        
        db.session.commit()
        return redirect(location=url_for('show_post', post_id=edited_post.id))
        
    add_post_form = Add_Post_Form(
        title = edited_post.title,
        subtitle = edited_post.subtitle,
        bg_img_url = edited_post.img_url,        
        blog_content = edited_post.body  
    )
    return render_template(template_name_or_list='make-post.html', form=add_post_form, post=edited_post)

@app.route('/delete-post/<int:post_id>')
@admin_only
def delete_post(post_id):
    deleted_post = db.session.get(BlogPost, post_id)
    if deleted_post is None:
        abort(404)
    db.session.delete(deleted_post)
    db.session.commit()
    return redirect(location=url_for('get_all_posts'))

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")


if __name__ == "__main__":
    init_database()
    app.run(debug=False, port=5003)
