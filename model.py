"""Models and database functions for Ratings project."""

import heapq
import time
from flask_sqlalchemy import SQLAlchemy
import correlation
from collections import defaultdict

# This is the connection to the PostgreSQL database; we're getting this through
# the Flask-SQLAlchemy helper library. On this, we can find the `session`
# object, where we do most of our interactions (like committing, etc.)

db = SQLAlchemy()


##############################################################################
# Model definitions

class User(db.Model):
    """User of ratings website."""

    __tablename__ = "users"

    user_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    email = db.Column(db.String(64), nullable=True)
    password = db.Column(db.String(64), nullable=True)
    age = db.Column(db.Integer, nullable=True)
    zipcode = db.Column(db.String(15), nullable=True)
    gender = db.Column(db.String(15), nullable=True)
    occupation = db.Column(db.String(30), nullable=True)

    def __repr__(self):
        """Provide helpful representation when printed."""

        return "<User user_id={} age={} zipcode={}>".format(self.user_id,
                                                            self.age,
                                                            self.zipcode)

    def similarity(self, other):
        """Return Pearson rating for user compared to other user."""

        u_ratings = {}
        paired_ratings = []

        for r in self.ratings:
            u_ratings[r.movie_id] = r

        for r in other.ratings:
            u_r = u_ratings.get(r.movie_id)
            if u_r:
                paired_ratings.append((u_r.rating, r.rating))

        if paired_ratings:
            return correlation.pearson(paired_ratings)

        else:
            return 0.0

    # Courtesy of Henry
    def predict_rating(self, movie):
        """Predict user's rating of a movie."""
        # import pdb; pdb.set_trace()

        UserMovies = db.aliased(Rating)

        MovieUsers = db.aliased(Rating)

        query = db.session.query(Rating, UserMovies, MovieUsers) \
            .join(UserMovies, UserMovies.movie_id == Rating.movie_id) \
            .join(MovieUsers, Rating.user_id == MovieUsers.user_id) \
            .filter(UserMovies.user_id == self.user_id) \
            .filter(MovieUsers.movie_id == movie.movie_id)

        print query

        known_ratings = {}

        paired_ratings = defaultdict(list)
        for rating, user_movie, movie_user in query:
            paired_ratings[rating.user_id].append((user_movie.rating, rating.rating))
        
            known_ratings[rating.user_id] = movie_user.rating
        
        similarities = []
        print known_ratings
        for _id, score in known_ratings.iteritems():
            similarity = correlation.pearson(paired_ratings[_id])
            print similarity
            if similarity > 0:
                similarities.append((similarity, score))
                print similarities
                if not similarities:
                    return None
        
        numerator = sum([score * sim for sim, score in similarities])
        print numerator
        
        denominator = sum([sim for sim, score in similarities])
        print denominator

        return numerator/denominator

# Put your Movie and Rating model classes here.


class Movie(db.Model):
    """Movies in ratings website."""

    __tablename__ = "movies"

    movie_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    movie_title = db.Column(db.String(128), nullable=False)
    released_on = db.Column(db.DateTime, nullable=False)
    imdb_url = db.Column(db.String(256), nullable=True)

    def __repr__(self):
        """Provide helpful representation when printed."""

        return "<Movie movie_id={} movie_title={}>".format(self.movie_id,
                                                           self.movie_title)


class Rating(db.Model):
    """Ratings in ratings website."""

    __tablename__ = "ratings"

    rating_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id",
                                                  ondelete="CASCADE"),
                        nullable=False)

    movie_id = db.Column(db.Integer, db.ForeignKey("movies.movie_id",
                                                   ondelete="CASCADE"),
                         nullable=False)

    rating = db.Column(db.Integer, nullable=False)

    users = db.relationship('User', backref=db.backref('ratings',
                                                       order_by=rating_id))

    movies = db.relationship('Movie', backref=db.backref('ratings',
                                                         order_by=rating_id))

    def __repr__(self):
        """Provide helpful representation when printed."""

        return "<Rating rating_id={} user_id={} movie_id={} rating={}>" \
            .format(self.rating_id,
                    self.user_id,
                    self.movie_id,
                    self.rating)


##############################################################################
# Helper functions

def connect_to_db(app):
    """Connect the database to our Flask app."""

    # Configure to use our PstgreSQL database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///ratings'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.app = app
    db.init_app(app)


if __name__ == "__main__":
    # As a convenience, if we run this module interactively, it will leave
    # you in a state of being able to work with the database directly.

    from server import app
    connect_to_db(app)
    print "Connected to DB."
