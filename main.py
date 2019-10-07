from flask import Flask, request, redirect, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
import jinja2
import os


template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir), autoescape=True)


app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://build-a-blog:work@localhost:3306/build-a-blog'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)


class Blog(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    body = db.Column(db.Text)

    def __init__(self, title, body):
        self.title = title
        self.body = body


@app.route('/blog', methods=['GET'])
def display_blog():
    template = jinja_env.get_template('posts.html')
    title = 'Build-A-Blog'

    if 'id' in request.args.keys():
        pid = request.args.get('id')
        post = Blog.query.get_or_404(pid)
        posts = [post]
        return template.render(posts=posts, title=post.title)
    else:
        posts = Blog.query.order_by(desc(Blog.id)).all()
        return template.render(posts=posts, title=title)


@app.route('/newpost', methods=['GET'])
def display_form():
    template = jinja_env.get_template('newpost.html')
    return template.render()


@app.route('/newpost', methods=['POST'])
def validate_form():
    template = jinja_env.get_template('newpost.html')
    title = request.form['title']
    body = request.form['body']
    global title_error, body_error
    title_error = ''
    body_error = ''

    def is_title_valid(t):
        global title_error
        if t == '':
            title_error = 'Please Enter a Title'
            return False
        else:
            return True

    def is_body_valid(b):
        global body_error
        if b == '':
            body_error = 'Please Insert Text'
            return False
        else:
            return True

    if is_title_valid(title) and is_body_valid(body):
        new = Blog(title=title, body=body)
        db.session.add(new)
        db.session.commit()
        return redirect('/blog?id={}'.format(new.id))
    else:
        return template.render(
            title=title, body=body,
            title_error=title_error,
            body_error=body_error
        )


if __name__ == '__main__':
    app.run()

