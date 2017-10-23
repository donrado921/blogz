from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:blogzpassword@localhost:8889/blogz' 
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = 'blogzsupersecretkey'

class Blog(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    body = db.Column(db.Text)
    date = db.Column(db.DateTime)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self,title,body,owner,date=None):
        self.title = title
        self.body = body
        self.owner = owner
        if date == None:
            date = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        self.date = date

    def __repr__(self):
        return '<Blog %r>' % self.title


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(120))
    blogs = db.relationship('Blog', backref='owner')
    
    def __init__(self, username, password):
        self.username = username
        self.password = password

    def __repr__(self):
        return '<User %r>' % self.username


@app.before_request 
def require_login():
    allowed_routes = ['login','signup','blog','index']
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect('/login')


@app.route('/')
def index():
    users = User.query.all()
    return render_template('index.html', title="Blogz - Home", users=users)
    

@app.route('/login', methods=["POST", "GET"])
def login():
    if request.method == 'GET':
        return render_template('login.html', title="Blogz - Login")
    elif request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = User.query.filter_by(username=username)
        if users.count() == 1:
            user = users.first()
            if password != user.password:
                flash('INCORRECT PASSWORD', 'error2')
                return redirect("/login")
            elif password == user.password:
                session['username'] = user.username
                return redirect("/newpost")
        flash('INCORRECT USERNAME', 'error1')
        return redirect("/login")


@app.route('/logout')
def logout():
  del session['username']
  return redirect('/')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        verify = request.form['verify']

        if (len(username) < 3): 
            username = ''
        if username == '':
            flash("Please enter a valid username", 'username_error')
        if password == '' or (len(password) < 3):
            flash("Please enter a valid password", 'password_error')
        if verify == '':
            flash("Passwords do not match", 'verify_error')
        if password != verify: 
            flash("Passwords do not match", 'verify_error')
    
        username_db_count = User.query.filter_by(username=username).count()
        if username_db_count > 0:
            flash(username + ' is already taken', 'user_taken')
            return redirect('/signup')
        if not password or not username:
            return redirect('/signup')
        if password != verify:
            return redirect('/signup')
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        session['username'] = user.username
        return redirect("/newpost")
    else:
        return render_template('signup.html', title="Blogz - Signup")

@app.route('/blog')
def blog():

    blogs = Blog.query.order_by(Blog.date.desc()).all()
    users = User.query.all()

    blog_id = request.args.get('id')
    get_user = request.args.get('user')

    if blog_id:
        single_blog = Blog.query.filter_by(id=blog_id).first()
        return render_template('single_blog.html', title="Blogz - All Posts", single_blog=single_blog, users=users)

    if get_user:
        owner = User.query.filter_by(username=get_user).first()
        blogs = Blog.query.filter_by(owner=owner).order_by(Blog.date.desc()).all()
        return render_template('blog.html', title="Blogz - All Posts", blogs=blogs, users=users)


    return render_template('blog.html', title="Blogz - All Posts", blogs=blogs, users=users)


@app.route('/newpost', methods=["POST", "GET"])
def newpost():

    if request.method == "POST":
        blog_title = request.form['blog_title']
        blog_body = request.form['blog_body']
        owner = owner = User.query.filter_by(username=session["username"]).first()
        if blog_title and blog_body:
            new_blog = Blog(blog_title, blog_body, owner)
            db.session.add(new_blog)
            db.session.commit()
            blog_id = str(new_blog.id)
            return redirect('/blog?id='+ blog_id)

        if not blog_title:
            flash("Please enter a blog title.", "error1")
        if not blog_body:
            flash("Please enter a blog body.", "error2")
        return redirect('/newpost')

    return render_template('newpost.html', title="Blogz - New Post")


if __name__ == '__main__':
  app.run()