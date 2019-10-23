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
    
    def __init__(self, title, body, owner):
        self.title = title
        self.body = body
        self.owner = owner

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    pw_hash = db.Column(db.String(120))
    blogs = db.relationship('Blog', backref='owner')
    
    def __init__(self, email, password):
        self.email = email
        self.pw_hash = make_pw_hash(password)

#directing user to either login in or signup before entering site
@app.before_request
def require_login():
    allowed_routes = ['login', 'signup']
    if request.endpoint not in allowed_routes and 'email' not in session:
        return redirect('/login')

#user login session function 
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
            return render_template('login.html', title="Blogz!")
    else:
        return render_template('login.html', title="Blogz!")


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
        def verify_email(x):
            try:
                if x.count('@') is 1 and '.com' in x:
                    return True
            except ValueError:
                if x.count('@') > 1:
                    return False
                
        def verify_uspw(x):
            try:
                if 20 < len(x) > 3:
                    return True
            except ValueError:
                if 3 < len(x) > 20:
                    return False

            if not verify_email(email):            
                email_error = "Please submit a valid email."
                email = ''

            if not verify_uspw(password):
                pw_error = "Please enter a valid password. Must be between 3 and 20 characters."
                password = ''

            if not verify_uspw(verify):
                verify_error = "Passwords must match. Please re-enter."
                verify = ''

                return render_template('signup.html', title="signup at Blogz!", email_error=email_error, pw_error=pw_error, verify_error=verify_error,email=email, password=password, verify=verify)

        existing_user = User.query.filter_by(email=email).first()
        if not existing_user:
            new_user = User(email, password)
            db.session.add(new_user)
            db.session.commit()
            session['email'] = email
            return redirect('/')
        else:
            flash("The email <strong>{0}</strong> is already signuped".format(email), 'danger')

    return render_template('signup.html')

@app.route('/logout', methods=['POST', 'GET'])
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

@app.route('/index', methods=['POST', 'GET'])
def main_page():
    user_id = request.args.get('id')
    
    if user_id == None:
        users = User.query.all()
        return render_template('index.html', users=users, title='Blogz!')
    else:
        user = User.query.get(blog_id)
        return render_template('index.html', user=user, title='My Blog Entries')


@app.route('/blog', methods=['POST', 'GET'])
def blog():
    blog_id = request.args.get('id')
    user_id = str(request.args.get('user'))
    
    if blog_id == None:
        posts = Blog.query.all()
        return render_template('blog.html', posts=posts, title='Blogz!')
    else:
        post = Blog.query.get(blog_id)
        return render_template('entry.html', post=post, title='My Blog Entries')

    
@app.route('/singleuser', methods=['POST', 'GET'])
def entries():
    owner = User.query.filter_by(email=session['email']).first()
    blog_id = request.args.get('id')

    if blog_id == None:
        posts = Blog.query.filter_by()
        user = Blog.query.filter_by(owner=owner).all()
        return render_template('singleuser.html', posts=posts, user=user, title='Blogz!')
    else:
        post = Blog.query.get(blog_id)
        return render_template('entry.html', post=post, title='Blog Entry')


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
            new_entry = Blog(blog_title, blog_body, owner)
            db.session.add(new_entry)
            db.session.commit() 
            return redirect('/blog?id={}'.format(new_entry.id)) 
        else:
            return render_template('newpost.html', title='New Entry', title_error=title_error, body_error=body_error, 
                blog_title=blog_title, blog_body=blog_body)
    
    return render_template('newpost.html', title='New Entry')


if __name__ == '__main__':
    app.run()
