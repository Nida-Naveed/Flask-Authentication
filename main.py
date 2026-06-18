from flask import Flask, render_template, request, url_for, redirect, flash, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from wtforms import StringField, validators
from flask_wtf import FlaskForm
from wtforms.fields.simple import PasswordField

app = Flask(__name__)  #instantiate Flask app
app.config['SECRET_KEY'] = 'secret-key-goes-here'

# CREATE DATABASE
class Base(DeclarativeBase):
    pass

#database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app) #pass your flask app


# CREATE TABLE IN DB
class User(UserMixin, db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(200))
    name: Mapped[str] = mapped_column(String(1000))

#create all tables configured by inheriting db.Model
with app.app_context():
    db.create_all()

#flask login Manager - for routes authentication
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

#Registration Flask Form
class RegisterForm(FlaskForm):
    name = StringField('Name', [validators.Length(min=1, max=100)])
    email = StringField('Email Address', [validators.Email()])
    password = PasswordField('Password', [validators.Length(min=1, max=100)])

@app.route('/')
def home():
    return render_template("index.html")


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            email=form.email.data
            password = form.password.data
            name = form.name.data

            existing_user = db.session.execute(
                db.select(User).where(User.email == email)
            ).scalar()
            #avoid integrity error by checking occurrence beforehand in the DB
            if existing_user:
                flash('ooopsssss Email address already registered!')
                return redirect(url_for("login"))

            #hashedpassword
            hashed_password = generate_password_hash(password)
            user = User(email=email, password=hashed_password, name=name)
            db.session.add(user)
            db.session.commit()
            #session started for current_user
            login_user(user)
            flash('Registered successfully.') #Flask flash messages
            return redirect(url_for("secrets"))

    return render_template("register.html",form=form)


@app.route('/login',methods=["GET","POST"])
def login():
    if request.method == 'POST':
        email = request.form['email']
        entered_password = request.form['password']
        user = db.session.execute(db.select(User).where(User.email == email)).scalar()
        if user:
            if check_password_hash(user.password, entered_password):
                login_user(user)
                flash('You are logged in')
                return redirect(url_for("secrets",name=user.name,logged_in=current_user.is_authenticated))
            else:
                flash('Invalid Credentials!!')
                return render_template("index.html")
        else:
            flash('Invalid Credentials!!')
            return render_template("index.html")
    return render_template("login.html")


@app.route('/secrets')
@login_required
def secrets():
    return render_template("secrets.html")


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You were successfully logged out')
    return redirect(url_for("home"))


@app.route('/download')
@login_required
def download():
    flash("File downloaded...")
    return (send_from_directory(
        'static/files', 'cheat_sheet.pdf', as_attachment=True)
    )


if __name__ == "__main__":
    app.run(debug=True)
