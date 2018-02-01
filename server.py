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
    hashed_pw = bcrypt.hashpw(submitted_password.encode('utf-8'),
                              bcrypt.gensalt())

    # Create bool if submitted password exists or not
    is_email_exists = bool((db.session.query(User.email)
                            .filter(User.email == submitted_email).first()))

    # If email exists, user can't register it again. Return to login page.
    if is_email_exists:
        flash("Email already registered.")
        return redirect('/register')
    # Otherwise, register account by adding new user to DB; send to homepage.
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

    # Retrieve user object with corresponding email.
    user = (db.session.query(User).filter(User.email == login_email).first())

    # If we found a user...
    if user:
        # Create bool to signal whether submitted password matches
        # password hash in db.
        is_password_match = bcrypt.checkpw(login_password.encode('utf-8'),
                                           user.password.encode('utf-8'))

        # If password does match, log in user.
        if is_password_match:
            print "User email and password match"

            session['user'] = user.user_id
            print session
            flash("You are logged in!")

            return redirect('/users/' + str(user.user_id))
        # Otherwise, flash error and redirect to login form.
        else:
            flash("Login unsuccessful.")
            print session
            return redirect('/login')
    # ...otherwise if user not found, flash error, and redirect to login form.
    else:
        flash("Login unsuccessful.")
        print session
        return redirect('/login')


@app.route('/logout', methods=['GET'])
def show_logout_form():
    """Logs the user out."""
    # session['user'] signals that the user is logged in. Clear it to log out.
    del session['user']
    flash("Logged out!")
    return redirect('/')


@app.route("/users")
def user_list():
    """Show list of users."""
    # Get all user objects to use in template.
    users = User.query.all()
    return render_template("user_list.html", users=users)


@app.route('/users/<user_id>')
def show_user_details(user_id):
    """Shows details for individual user"""

    #Creates user object joined to both ratings and movies
    user = User.query.options(db.joinedload('ratings', 'movies')).get(user_id)

    return render_template('user_details.html',
                           user=user)

    # movie_ratings=movie_ratings_by_user


@app.route("/movies")
def movie_list():
    """Show list of movies."""

    movies = Movie.query.order_by(Movie.movie_title).all()
    return render_template("movie_list.html", movies=movies)


@app.route('/movies/<movie_id>')
def show_movie_details(movie_id):
    """Shows details for a movie."""

    movie = db.session.query(Movie).get(movie_id)

    # Query to get list of tuples for all movies with (user_id, rating)
    all_movie_ratings = db.session.query(Rating.user_id, Rating.rating)

    # Filters by the specified movie_id and fetches those tuples.
    movie_ratings = all_movie_ratings.filter(Rating.movie_id == movie_id).all()

    user_id = session.get('user')

    if user_id:
        user_rating = Rating.query.filter_by(
            movie_id=movie_id, user_id=user_id).first()

    else:
        user_rating = None

    # Get average rating of movie

    rating_scores = [r.rating for r in movie.ratings]
    avg_rating = float(sum(rating_scores)) / len(rating_scores)

    prediction = None

    # Prediction code: only predict if the user hasn't rated it.

    if (not user_rating) and user_id:
        user = User.query.get(user_id)
        if user:
            prediction = user.predict_rating(movie)

    return render_template('movie_details.html',
                           movie=movie,
                           movie_ratings=movie_ratings,
                           user_rating=user_rating,
                           average=avg_rating,
                           prediction=prediction)


@app.route('/add-rating', methods=['POST'])
def add_rating():
    """Allows a logged-in user to add a rating."""

    user_rating = request.form.get('user_rating')
    movie_id = request.form.get('movie_id')
    user_id = session.get('user')

    # Gets rating object for specific user and movie
    rating_entry = db.session.query(Rating) \
        .filter((Rating.user_id == user_id),
                (Rating.movie_id == movie_id)).first()

    # If rating entry exists, updates rating
    if rating_entry:
        rating_entry.rating = user_rating
    # Else adds new rating to database
    else:
        new_rating = Rating(user_id=user_id, movie_id=movie_id, rating=user_rating)

    db.session.commit()
    return redirect('/movies/' + movie_id)

@app.route('/update-info', methods=['GET'])
def show_update_info_page():
    """Shows form to update user info"""

    if session.get('user'):
        return render_template('update_info.html')
    else:
        flash("Please login to update your profile.")
        return redirect('/login')

@app.route('/update-info', methods=['POST'])
def update_user_info():
    """Update user info in database"""

    age = request.form.get('age')
    gender = request.form.get('gender')
    occupation = request.form.get('occupation')
    zipcode = request.form.get('zipcode')

    user_id = session.get('user')

    user = db.session.query(User).get(user_id)

    if age:
        user.age = age
    if gender:
        user.gender = gender
    if occupation:
        user.occupation = occupation
    if zipcode:
        user.zipcode = zipcode

    db.session.commit()

    return redirect('/users/' + str(user_id))


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
