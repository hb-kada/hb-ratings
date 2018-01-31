"""Movie Ratings."""

from jinja2 import StrictUndefined

from flask import (Flask, render_template, redirect, request, flash,
                   session)

from flask_debugtoolbar import DebugToolbarExtension

from model import User, Rating, Movie, connect_to_db, db

import bcrypt

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


@app.route("/register", methods=['GET'])
def show_registration_form():
    """Display registration form"""

    return render_template("registration_form.html")


@app.route('/register', methods=['POST'])
def process_registration_form():
    """Process user registration data"""

    submitted_email = request.form.get('email')
    submitted_password = request.form.get('password')

    # Create hash of password before it is stored in database
    hashed_pw = bcrypt.hashpw(submitted_password.encode('utf-8'), bcrypt.gensalt())

    is_email_exists = (db.session.query(User.email).filter(User.email == submitted_email).first())
    print is_email_exists
    if is_email_exists:
        flash("Email already registered.")
        return redirect('/register')
    else:
        new_user = User(email=submitted_email, password=hashed_pw)
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

    user = (db.session.query(User).filter(User.email == login_email).first())
    print user

    if user:

        # checks if submitted password matches password hash in db. returns boolean
        is_password_match = bcrypt.checkpw(login_password.encode('utf-8'), user.password.encode('utf-8'))

        if is_password_match:
            print "User email and password match"

            session['user'] = user.user_id
            print session
            flash("You are logged in!")

            return redirect('/users/' + str(user.user_id))
        else:
            flash("Login unsuccessful.")
            print session
            return redirect('/login')
    else:
        flash("Login unsuccessful.")
        print session
        return redirect('/login')


@app.route('/logout', methods=['GET'])
def show_logout_form():
    """Logs the user out."""

    del session['user']

    flash("Logged out!")

    return redirect('/')


@app.route("/users")
def user_list():
    """Show list of users."""

    users = User.query.all()
    return render_template("user_list.html", users=users)


@app.route('/users/<user_id>')
def show_user_details(user_id):
    """Shows details for individual user"""

    user = db.session.query(User).get(user_id)

    # for rating_obj in user.ratings:
    #     print rating_obj.movies.movie_title, rating_obj.rating

    #return list of tuples of all (movie_title, rating)
    all_movie_ratings = db.session.query(Movie.movie_title, Rating.rating, Movie.movie_id).join(Rating)

    #filtered by a single user
    movie_ratings_by_user = all_movie_ratings.filter(Rating.user_id == user_id).all()

    return render_template('user_details.html', user=user, movie_ratings=movie_ratings_by_user)


@app.route("/movies")
def movie_list():
    """Show list of movies."""

    movies = Movie.query.order_by(Movie.movie_title).all()
    return render_template("movie_list.html", movies=movies)


@app.route('/movies/<movie_id>')
def show_movie_details(movie_id):
    """Shows details for a movie."""

    movie = db.session.query(Movie).get(movie_id)

    #list of tuples for all movies with (user_id, rating)
    all_movie_ratings = db.session.query(Rating.user_id, Rating.rating)

    #filters by a single movie
    movie_ratings = all_movie_ratings.filter(Rating.movie_id == movie_id).all()

    return render_template('movie_details.html', movie=movie, movie_ratings=movie_ratings)


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
