from flask import Flask, request, redirect, render_template, flash, session
from flask_sqlalchemy import SQLAlchemy
from hashutils import make_pw_hash, check_pw_hash

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:password@localhost:3306/blogz'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = 'yatNMk4ynv88HM'

class Blog(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    body = db.Column(db.Text)
    owner_id = db.Column(db.Integer,db.ForeignKey('user.id'))
    
    def __init__(self, title, body):
        self.title = title
        self.body = body

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    pw_hash = db.Column(db.String(120))
    blogs = db.relationship('Blog', backref='owner')
    
    def __init__(self, email, password):
        self.email = email
        self.pw_hash = make_pw_hash(password)


@app.before_request
def require_login():
    allowed_routes = ['login', 'signup']
    if request.endpoint not in allowed_routes and 'email' not in session:
        return redirect('/login')

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_pw_hash(password, user.pw_hash):
            session['email'] = email
            flash("Logged in",'info')
            return redirect('/index')
        else:
            flash('User password incorrect or user does not exist', 'error')
    else:
        return render_template('login.html')


@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        verify = request.form['verify']
        email_error = ''
        pw_error = ''
        verify_error = ''

        # TODO - validate user's data
        
        existing_user = User.query.filter_by(email=email).first()
        if not existing_user:
            new_user = User(email, password)
            db.session.add(new_user)
            db.session.commit()
            session['email'] = email
            return redirect('/')
        else:
            flash("The email <strong>{0}</strong> is already registered".format(email), 'danger')

    return render_template('signup.html')

@app.route('/logout')
def logout():
    del session['email']
    flash("Logged out",'info')
    return redirect('/')


@app.route('/', methods=['POST', 'GET'])
def index():

    owner = User.query.filter_by(email=session['email']).first()

    if request.method == 'POST':
        blog_name = request.form['blog']
        new_blog = Blog(blog_name, owner)
        db.session.add(new_blog)
        db.session.commit()

    blogs = Blog.query.filter_by(owner=owner).all()
    return render_template('blog.html',title="Blogz!", 
        blogs=blogs)

@app.route('/index')
def main_page():
    user_id = request.args.get('id')

    if user_id == None:
        owner = User.query.all()
        return render_template('index.html',owner=owner, title='Blogz!')

    else:
        blog = User.query.get(user_id)
        return render_template('entry.html',blog=blog, title='Blog Entry')


@app.route('/blog')
def blog():
    blog_id = request.args.get('id')

    if blog_id == None:
        posts = Blog.query.all()
        return render_template('blog.html',posts=posts, title='Build-A-Blog')

    else:
        post = Blog.query.get(blog_id)
        return render_template('entry.html',post=post, title='Blog Entry')


@app.route('/newpost', methods=['POST', 'GET'])
def new_post():

    owner = User.query.filter_by(email=session['email']).first()

    if request.method == 'POST':
        blog_title = request.form['blog-title']
        blog_body = request.form['blog-entry']
        title_error = ''
        body_error = ''

        if not blog_title:
            title_error = "Please enter a blog title"
        if not blog_body:
            body_error = "Please enter a blog entry"

        if not body_error and not title_error:
            new_entry = Blog(blog_title, blog_body)     
            db.session.add(new_entry)
            db.session.commit()  

            blog_id = int(request.form['blog-id'])
            entry = Blog.query.id(blog_id)
            entry.private = True   
            db.session.add(entry)
            db.session.commit()   
            return redirect('/blog?id={}'.format(new_entry.id))
        else:
            new_entry = Blog(blog_title, blog_body)     
            db.session.add(new_entry)
            db.session.commit()
            return redirect('/blog?id={}'.format(new_entry.id))  
    else:
        return render_template('newpost.html', title='New Entry', title_error=title_error, body_error=body_error, 
            blog_title=blog_title, blog_body=blog_body)
    
    return render_template('newpost.html', title='New Entry')

@app.route('/delete-blog', methods=['POST'])
def private_blog():

    blog_id = int(request.form['blog-id'])
    blog = blog.query.get(blog_id)
    db.session.add(blog)
    db.session.commit()

    return redirect('/')


if __name__ == '__main__':
    app.run()
