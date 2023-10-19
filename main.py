from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

import requests
from pprint import pprint

url = "https://api.themoviedb.org/3/search/movie"

headers = {
    "accept": "application/json",
    "Authorization": <Your bearer, see API documentation>,
}
"""
Red underlines? Install the required packages first: 
Open the Terminal in PyCharm (bottom left). 

On Windows type:
python -m pip install -r requirements.txt

On MacOS type:
pip3 install -r requirements.txt

This will install the packages from requirements.txt for this project.
"""

app = Flask(__name__)
app.config["SECRET_KEY"] = "8BYkEfBA6O6donzWlSihBXox7C0sKR6b"
Bootstrap5(app)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movies.db"

# Create the extension
db = SQLAlchemy()

# initialize the app with the extension
db.init_app(app)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)


# new_movie = Movie(
#     title="Phone Booth",
#     year=2002,
#     description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
#     rating=7.3,
#     ranking=10,
#     review="My favourite character was the caller.",
#     img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
# )

# Create table schema in the database. Requires application context.
with app.app_context():
    db.create_all()
    # db.session.add(new_movie)
    # db.session.commit()


class RatingForm(FlaskForm):
    rating = StringField("Your Rating Out of 10 e.g. 7.5")
    review = StringField("Your Review")
    submit = SubmitField("Done")


class AddForm(FlaskForm):
    title = StringField("Movie Title")
    submit = SubmitField("Add Movie")


@app.route("/")
def home():
    result = db.session.execute(db.select(Movie).order_by(Movie.rating.desc()))
    all_movies = result.scalars().all() # convert ScalarResult to Python List
    for rank, movie in enumerate(all_movies, start = 1):
        movie.ranking = rank
    db.session.commit()

    return render_template("index.html", movies=all_movies)


@app.route("/edit", methods=["POST", "GET"])
def rate_movie():
    print(request.args)  # l'objecte es manté després d'executar render_template
    form = RatingForm()
    movie_id = request.args.get("id")
    movie = db.get_or_404(Movie, movie_id)
    if form.validate_on_submit():
        movie.rating = float(form.rating.data)
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("edit.html", form=form, id=movie_id)


@app.route("/delete")
def delete_movie():
    movie_id = request.args.get("id")
    movie_to_delete = db.get_or_404(Movie, movie_id)  # get a book by id
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/add", methods=["GET", "POST"])
def add_movie():
    form = AddForm()
    if form.validate_on_submit():
        # form.title.data
        params = {
            "query": form.title.data,
            "include_adult": "false",
            "language": "en-US",
        }
        response = requests.get(url, headers=headers, params=params)
        results = response.json()["results"]
        return render_template("select.html", results=results)
    return render_template("add.html", form=form)


@app.route("/populate")
def populate():
    id = request.args.get("id")
    details = requests.get(f"https://api.themoviedb.org/3/movie/{id}", headers=headers)
    #pprint(details)
    poster = details.json()["poster_path"]
    new_movie = Movie(
        title=details.json()["title"],
        year=int(details.json()["release_date"][:4]),
        description=details.json()["overview"],
        img_url=f"https://image.tmdb.org/t/p/w500/{poster}",
    )
    db.session.add(new_movie)
    db.session.commit()
    return redirect(url_for("rate_movie", id = new_movie.id))  # Passo el parametre id com a request

if __name__ == "__main__":
    app.run(debug=True)
