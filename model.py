"""Models and database functions for Ratings project."""

from flask_sqlalchemy import SQLAlchemy

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
