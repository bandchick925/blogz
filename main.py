from flask import Flask, request, redirect, render_template, session, flash, url_for, get_flashed_messages
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
import os, jinja2, hashlib, datetime


template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir), autoescape=True)

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:work@localhost:3306/blogz'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.secret_key = 'y337kGcys&zP3B'
db = SQLAlchemy(app)


class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    body = db.Column(db.Text)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    stamp = db.Column(db.DateTime)

    def __init__(self, title, body, owner, stamp):
        self.title = title
        self.body = body
        self.owner = owner
        self.stamp = stamp


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120))
    password = db.Column(db.String(120))
    blogs = db.relationship('Blog', backref='owner')

    def __init__(self, username, password):
        self.username = username
        self.password = hashlib.sha256(str.encode(password)).hexdigest()


@app.before_request
def require_login():
    allowed_routes = ['login', 'signup', 'blog', 'index']
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect('/login')


@app.route('/login', methods=['POST', 'GET'])
def login():
    template = jinja_env.get_template('login.html')
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user:
            if user.password == hashlib.sha256(str.encode(password)).hexdigest():
                session['username'] = username
                flash("Logged in")
                return redirect('/newpost')
            else:
                flash('Password Incorrect')
        else:
            flash('Username Incorrect')

    return template.render(get_flashed_messages=get_flashed_messages)


@app.route('/logout')
def logout():
    del session['username']
    return redirect('/blog')


@app.route('/', methods=['GET'])
def index():
    template = jinja_env.get_template('index.html')
    username = 'Blog Buddy'
    if 'username' in session.keys():
        username = session['username']
    return template.render(username=username)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    template = jinja_env.get_template('signup.html')
    if request.method == 'POST':
        name = request.form['username']
        password = request.form['password']
        verify = request.form['verify']

        global name_error, pword_error, verify_error
        name_error = ''
        pword_error = ''
        verify_error = ''

        def is_name_valid(name):
            global name_error
            existing_user = User.query.filter_by(username=name).first()
            if not existing_user:
                if len(name) > 3:
                    return True
                else:
                    name_error = 'Name is shorter than 3 characters.'
                    return False
            else:
                name_error = 'Username already exists. Select another username.'
                return False

        def pwords_match(pw, vpw):
            global pword_error, verify_error
            if pw == '':
                pword_error = 'Password field cannot be empty'
                return False

            elif ' ' in pw:
                pword_error = 'Password cannot contain spaces'
                return False

            elif vpw == '':
                verify_error = 'Password field cannot be empty'
                return False

            elif ' ' in vpw:
                verify_error = 'Password cannot contain spaces'
                return False

            elif (len(password) > 20) or (len(password) < 3):
                pword_error = 'Password must be 3-20 characters'
                return False

            elif pw != vpw:
                pword_error = verify_error = 'Passwords do not match'
                return False
            else:
                return True

        if is_name_valid(name) and pwords_match(password, verify):
            user = User(username=name, password=password)
            db.session.add(user)
            db.session.commit()
            session['username'] = name
            return redirect('/newpost')
        else:
            return template.render(
                username_error=name_error,
                password_error=pword_error,
                verify_error=verify_error,
                username=name
            )

    return template.render()


@app.route('/blog', methods=['GET'])
def blog():
    template = jinja_env.get_template('posts.html')
    title = 'My Blog'

    if 'id' in request.args.keys():
        pid = request.args.get('id')
        post = Blog.query.get_or_404(pid)
        posts = [post]
        return template.render(posts=posts, title=post.title)

    elif 'user' in request.args.keys():
        uid = request.args.get('user')
        user = User.query.get(id=uid)
        posts = Blog.query.filter_by(owner=user).all()
        template = jinja_env.get_template('singleUser.html')
        return template.render(posts=posts, title='Posts by {}'.format(user.username))

    else:
        posts = Blog.query.order_by(desc(Blog.id)).all()
        return template.render(posts=posts, title=title)


@app.route('/newpost', methods=['GET', 'POST'])
def newpost():
    template = jinja_env.get_template('newpost.html')
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']

        global title_error, body_error
        title_error = ''
        body_error = ''

        def is_title_valid(t):
            global title_error
            if t == '':
                title_error = 'Enter a title for the new post'
                return False
            else:
                return True

        def is_body_valid(b):
            global body_error
            if b == '':
                body_error = 'Enter a body for the new post'
                return False
            else:
                return True

        if is_title_valid(title) and is_body_valid(body):
            username = session['username']
            stamp = datetime.datetime.now()
            owner = User.query.filter_by(username=username).first()
            new = Blog(title=title, body=body, owner=owner, stamp=stamp)
            db.session.add(new)
            db.session.commit()
            return redirect('/blog?id={}'.format(new.id))
        else:
            return template.render(
                title=title, body=body,
                title_error=title_error,
                body_error=body_error
            )

    return template.render()


if __name__ == '__main__':
    app.run()

