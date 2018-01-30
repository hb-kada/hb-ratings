"""Movie Ratings."""

from jinja2 import StrictUndefined

from flask import (Flask, render_template, redirect, request, flash,
                   session)

from flask_debugtoolbar import DebugToolbarExtension

from model import User, Rating, Movie, connect_to_db, db


app = Flask(__name__)

# Required to use Flask sessions and the debug toolbar
app.secret_key = "ABC"

# Normally, if you use an undefined variable in Jinja2, it fails
# silently. This is horrible. Fix this so that, instead, it raises an
# error.
app.jinja_env.undefined = StrictUndefined


@app.route('/')
def index():
    """Homepage."""

    return render_template("homepage.html")


@app.route("/users")
def user_list():
    """Show list of users."""

    users = User.query.all()
    return render_template("user_list.html", users=users)


@app.route("/register", methods=['GET'])
def show_registration_form():
    """Display registration form"""

    return render_template("registration_form.html")


@app.route('/register', methods=['POST'])
def process_registration_form():
    """Process user registration data"""

    submitted_email = request.form.get('email')
    submitted_password = request.form.get('password')

    #TODO: Add flash message telling user email already exists

    is_email_exists = db.session.query(User.email).filter(User.email == submitted_email).first()
    print is_email_exists
    if is_email_exists:
        return redirect('/register')
    else:
        new_user = User(email=submitted_email, password=submitted_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect('/')


@app.route('/login', methods=['GET'])
def show_login_form():
    """Display login form."""

    return render_template("login_form.html")


@app.route('/login', methods=['POST'])
def process_login_form():
    """Process login data."""

    login_email = request.form.get('email')
    login_password = request.form.get('password')

    is_email_exists = db.session.query(User.email) \
        .filter(User.email == login_email).first()

    is_password_match = db.session.query(User.password).filter(User.email == login_email, login_password == User.password).first()

    if is_email_exists and is_password_match:
        print "User email and password match"
        return redirect('/')
    else:
        print "User email not found OR password doesn't match."
        return redirect('/login')

    # Check to see if email exists in users table
        # AND check if corresponding password matches submitted password
            # If so, log user in
    # Else, redirect back to login page (with a flash later!)


if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the
    # point that we invoke the DebugToolbarExtension
    app.debug = True
    # make sure templates, etc. are not cached in debug mode
    app.jinja_env.auto_reload = app.debug

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    # app.run()
    
    app.run(port=5000, host='0.0.0.0')
