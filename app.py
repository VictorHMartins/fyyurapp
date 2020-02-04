'''
PLEASE READ BEFORE RUNNING THE CODE

After upgrading the migration to create the tables, the application will run, 
however for it to function properly 
the 'genre' table needs to be already filled with static values that
do not change.


This is the SQL command needed:

INSERT INTO genre (genre) VALUES('Alternative'),('Blues'), ('Classical'), ('Country'), ('Electronic'), ('Folk'), ('Funk'), ('Hip-Hop'), ('Heavy Metal'), ('Instrumental'), ('Jazz'), ('Musical Theatre'), ('Pop'), ('Punk'), ('R&B'), ('Reggae') ,('Rock n Roll'), ('Soul'), ('Other');p'), ('Punk'), ('R&B'), ('Rock n Roll'), ('Soul'), ('Other');

I thought this initially was a good idea, however 
I realized very late that the way I constructed the 
database was very poor in regards to flexibility.
I misjudged how much time I had to formulate a more 
robust Model due to having to catch up with the lesson since 
I started the class late. I want to redo the whole thing however 
I simply do not have enough time.
I apoligize in advance, I know I will receive very
little points, I hope to deliver fully robust future projects in the future.

'''




#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import sqlalchemy
import itertools
import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from sqlalchemy.orm import validates
from sys import exc_info
from collections import Counter


#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)


#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

# Created Venue Table with relations to Artist table.
class Venue(db.Model):
  __tablename__ = 'venue'

  id = db.Column(db.Integer, primary_key=True, nullable=False)
  name = db.Column(db.String, nullable=False)
  city = db.Column(db.String(120), nullable=False)
  state = db.Column(db.String(2), nullable=False)
  address = db.Column(db.String(120), nullable=False)
  phone = db.Column(db.String(120), nullable=False)
  image_link = db.Column(db.String(500))
  facebook_link = db.Column(db.String(120))
  upcoming_shows = db.Column(db.Integer)
  artist = db.relationship('Artist', secondary='artist_venue', backref=db.backref('venue'))
  show = db.relationship('Show', backref=db.backref('venue'))
  

# Created Artist, child relation to Venue table.
class Artist(db.Model):
  __tablename__ = 'artist'

  id = db.Column(db.Integer, primary_key=True, nullable=False)
  name = db.Column(db.String, nullable=False)
  city = db.Column(db.String(120), nullable=False)
  state = db.Column(db.String(2), nullable=False)
  phone = db.Column(db.String(120), nullable=False)
  image_link = db.Column(db.String(500))
  facebook_link = db.Column(db.String(500))
  

  
# Creates the relationship between both Artists and Venues.
artist_venue = db.Table('artist_venue',
  db.Column('id', db.Integer, primary_key=True, nullable=False),
  db.Column('artist_id', db.Integer, db.ForeignKey('artist.id'), nullable=False),
  db.Column('venue_id', db.Integer, db.ForeignKey('venue.id'), nullable=False)
  )


# Created Genre wBeing the parent to both Artist and Venue: m::m
class Genre(db.Model):
  __tablename__ = 'genre'

  id = db.Column(db.Integer, primary_key=True, nullable=False)
  genre = db.Column(db.String(120),nullable=False)
  artist = db.relationship('Artist', secondary='artist_genre', backref=db.backref('genre'))
  venue = db.relationship('Venue', secondary='venue_genre', backref=db.backref('genre'))


# Association table for Artist and Genre
artist_genre = db.Table('artist_genre',
  db.Column('id', db.Integer, primary_key=True, nullable=False),
  db.Column('artist_id', db.Integer, db.ForeignKey('artist.id'), nullable=False),
  db.Column('genre_id', db.Integer, db.ForeignKey('genre.id'), nullable=False)
)


# Association table for Venue and Genre
venue_genre = db.Table('venue_genre',
  db.Column('id', db.Integer, primary_key=True, nullable=False),
  db.Column('venue_id', db.Integer, db.ForeignKey('venue.id'), nullable=False),
  db.Column('genre_id', db.Integer, db.ForeignKey('genre.id'), nullable=False)
)


# Created Show to relate both Artist and Venues, however it itself would store
# IDs so that it can identify the shows to its parents.
class Show(db.Model):
  __tablename__ = 'show'

  id = db.Column(db.Integer, primary_key=True)
  start_time = db.Column(db.DateTime, nullable=False)
  artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'))
  venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'))
  artist = db.relationship('Artist', backref=db.backref('show'))



#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  
  try:
    # Creates query and obtains the venue: id, name, and start-time.
    data = []
    venue = db.session.query(Venue).all()
    show = db.session.query(Venue.id, Venue.name, Show.start_time).join(Venue.show).filter(Venue.id == Show.venue_id).all()

    # Presents data in the following format to be sent back to client.
    show_data = []
    for s in show:
      temp = {
        "id": s.id, 
        "name": s.name, 
        "start_time": s.start_time 
      }
      show_data.append(temp)
    
    # This gets each show via ID and returns the occurence of shows if more than one is found
    occurence = Counter([k['id'] for k in show_data if k.get('id')])
    # This organizes in descending order.
    common = dict(occurence.most_common())

    # Appends data to data list
    data = []
    for d in venue:
      temp = {
        "city": d.city, 
        "state": d.state, 
        "venues": [{
        "id": d.id, 
        "name": d.name, 
        "num_upcoming_shows": 0
        }]
      }
      data.append(temp)

    # If the occurence is true for each venue it'll increment num_upcoming_shows
    for v in data:        
      for venue in v['venues']:
        if venue['id'] in common:
          venue['num_upcoming_shows'] = common[venue['id']]
  
  except:
      db.session.rollback()
      db.session.close()
      flash('Venue ' + request.form['name'] + ' Had an issue pulling data')
      return render_template(redirect(url_for('venues')))


  return render_template('pages/venues.html', areas=data);


@app.route('/venues/search', methods=['POST'])
def search_venues():
  
  search_term = request.form.get('search_term')

  # This gets whatever word the user puts in case insensitive and returns values
  # The following query line# 197 has problems depending on your version of Python3 make sure you have 
  # The latest version possible for both Flask-Alchemy and Python3.6+
  venue = db.session.query(Venue.id, Venue.name).filter(Venue.name.ilike(f'%{search_term}%')).all()
  show = db.session.query(Venue.id, Show.start_time, Venue.name).join(Venue.show).filter(venue[0].id == Show.venue_id).all()
  

  show_data = []
  for s in show:
    temp = {"id": s.id, "name": s.name, "start_time": s.start_time 
    }
    show_data.append(temp)


  # This gets each show via ID and returns the occurence of shows if more than one is found
  occurence = Counter([k['id'] for k in show_data if k.get('id')])
  # This organizes in descending order.
  common = dict(occurence.most_common())

  count = 1
  for d in venue:
    response = {
      "count": count, 
      "data": [{
      "id": d.id, 
      "name": d.name, 
      "num_upcoming_shows": common[d.id]
      }]
    }
    count += 1

  
  return render_template('pages/search_venues.html', 
  results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
 
  # obtains the venue by its id and the genres the venue has on schedule
  venue = db.session.query(Venue).filter(Venue.id == venue_id).all()
  genres = db.session.query(Genre.genre).join(Venue.genre).filter(Venue.id == venue_id).all()

  g = []
  for i in genres:     
    for x in i:
      g.append(x)
  
  for s in venue:
    venue_data = {"id": s.id, 
    "name": s.name, 
    "genres": g, 
    "address": s.address, 
    "city": s.city,
    "state": s.state, 
    "phone": s.phone, 
    "facebook_link": s.facebook_link}

  
  data = list(filter(lambda d: d['id'] == venue_id, [venue_data]))[0]
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():

  try:
    error = False
    genre = request.form.getlist('genres') # Takes Genres from the ImuutableDict
    data = {}
    for (k, v) in request.form.items(): # Obtains the rest of the entries.
      data[k] = v
    
    # Creates Venue with gathered data from above.
    venue = Venue(name=data['name'], city=data['city'], state=data['state'], address=data['address'], phone=data['phone'], facebook_link=data['facebook_link'])
    
    # Adds Venue to Model
    db.session.add(venue)

    # For each genre it associates each with the Venue.
    for g in genre:
      genre_title = db.session.query(Genre).filter(Genre.genre == g).first()
      venue.genre.append(genre_title)
    
    # Comming the additions
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully listed!')


    # If any exceptions are raised it will flash an error on screen.
  except:
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')


  return render_template('pages/home.html')



@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):

  # Fetch API returns a JSON objects that can be manipulated. 
  # Here the reponse gets sent with a True as a check.
  try:
    # Obtains the venue name and ten deletes the record, depending on the circumstance 
    # it will either error or give notice that it was sucessful.
    venue_name = request.get_json()['name']
    venue = db.session.query(Venue).filter(Venue.id == venue_id).first()
    db.session.delete(venue)
    db.session.commit()
    flash('Sucess! the Venue: ' + venue_name + ' was removed.')

  except:
    flash('An error occurred. Artist ' + venue_name + ' could not be listed.')
  return jsonify({'response': True})

  


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  
  data = []
  query = db.session.query(Artist).all()
  for d in query:
    artistDict = {"id":d.id, "name":d.name}
    data.append(artistDict)


  return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():

  # Searches for the value in the request.
  search_term = request.form.get('search_term')

  # This gets whatever word the user puts in case insensitive and returns values
  # The following query line# 197 has problems depending on your version of Python3 make sure you have 
  # The latest version possible for both Flask-Alchemy and Python3.6+
  artist = db.session.query(Artist.id, Artist.name).filter(Artist.name.ilike(f'%{search_term}%')).all()
  show = db.session.query(Artist.id, sqlalchemy.cast(Show.start_time, sqlalchemy.String), Artist.name).join(Artist.show).filter(artist[0].id == Show.artist_id).all()
  

  show_data = []
  for s in show:
    temp = {"id": s.id, "name": s.name, "start_time": s.start_time 
    }
    show_data.append(temp)


  # This gets each show via ID and returns the occurence of shows if more than one is found
  occurence = Counter([k['id'] for k in show_data if k.get('id')])
  # This organizes in descending order.
  common = dict(occurence.most_common())

  count = 1
  for d in artist:
    response = {
      "count": count, 
      "data": [{
      "id": d.id, 
      "name": d.name, 
      "num_upcoming_shows": common[d.id]
      }]
    }
    count += 1

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  
  query = db.session.query(Artist).all()
  artist = []

  # It'll cycle through the selected IDs obj 
  # and send the artist object back in the response.
  for d in query:
    artistDict = {
      "id":d.id, 
      "name":d.name, 
      "city":d.city, 
      "state":d.state,
      "phone":d.phone, 
      "image_link":d.image_link, 
      "facebook_link":d.facebook_link
    }

    artist.append(artistDict)
  
  
  data = list(filter(lambda d: d['id'] == artist_id, artist))[0]
  return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()

  artist = db.session.query(Artist).get(artist_id)

  return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):

  error = False
  genre = request.form.getlist('genres') # Takes Genres from the ImuutableDict
  fetched_artist = {}
  
  for (k, v) in request.form.items(): # Obtains the rest of the entries.
    fetched_artist[k] = v

  # Updates all fields
  artist = db.session.query(Artist).get(artist_id)
  artist.name = fetched_artist['name']
  artist.city = fetched_artist['city']
  artist.state = fetched_artist['state']
  artist.phone = fetched_artist['phone']
  artist.facebook_link = fetched_artist['facebook_link']
  
  # for each genre in the list it'll append to the relationship tables between artist and genre
  for g in genre:
      genre_title = db.session.query(Genre).filter(Genre.genre == g).first()
      artist.genre.append(genre_title)

  db.session.commit()

  return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()

  try:
    venue = db.session.query(Venue).get(venue_id)

  except:
    db.session.rollback()
    db.session.close()
    error = True
    flash('Communication with Database failed, Please check connection!')
  
  return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  
  try:

    error = False
    genre = request.form.getlist('genres') # Takes Genres from the ImuutableDict
    fetched_venues = {}
    
    for (k, v) in request.form.items(): # Obtains the rest of the entries.
      fetched_venues[k] = v

    # queries venue and then updates fields.
    venue = db.session.query(Venue).get(venue_id)
    venue.name = fetched_venues['name']
    venue.city = fetched_venues['city']
    venue.state = fetched_venues['state']
    venue.address = fetched_venues['address']
    venue.phone = fetched_venues['phone']
    venue.facebook_link = fetched_venues['facebook_link']
    

    for g in genre:
      genre_title = db.session.query(Genre).filter(Genre.genre == g).first()
      venue.genre.append(genre_title)


    db.session.commit()
    flash('Successfully entering. Venue ' + request.form['name'])


  except:
    error = True
    db.session.rollback()
    db.session.close()
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')


  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # Initial start to entering data into Artists and Genres tables.
  try:
    error = False
    genre = request.form.getlist('genres') # Takes Genres from the ImuutableDict
    data = {}
    for (k, v) in request.form.items(): # Obtains the rest of the entries.
      data[k] = v
    
    # Creates Artist with gathered data from above.
    artist = Artist(name=data['name'], city=data['city'], state=data['state'],
      phone=data['phone'], facebook_link=data['facebook_link'])
    
    # Adds artist to Model
    db.session.add(artist)

    # For each genre it associates each with the Artist.
    for g in genre:
      genre_title = db.session.query(Genre).filter(Genre.genre == g).first()
      artist.genre.append(genre_title)
    
    
    db.session.commit()
    db.session.close()
    flash('Artist ' + request.form['name'] + ' was successfully listed!')


  except:
    error = True
    db.session.rollback()
    db.session.close()
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')


  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():

  try:
    # Obtains the records for both venues and artist that are playing at the current show.
    show = db.session.query(Venue.id.label("v_id"), 
    Venue.name.label("v_name"), Artist.id.label("a_id"), 
    Artist.name.label("a_name"), Artist.image_link,
    sqlalchemy.cast(Show.start_time, sqlalchemy.String).label("start_time")).join(Show.artist, 
    Venue).filter(Show.venue_id == Venue.id).all()

    data = []
    for d in show:
      show_dict = {"venue_id":d.v_id, 
      "venue_name":d.v_name, 
      "artist_id":d.a_id, 
      "artist_name":d.a_name,
      "artist_image_link":d.image_link, 
      "start_time":d.start_time
      }
      data.append(show_dict)
  
  except:
    db.session.rollback()
    db.session.close()
    error = True
    flash('Show has failed to be listed! Please check connection!')


  return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
 
  try:
    error = False
    data = {} # Takes Shows from the ImuutableDict
    for (k, v) in request.form.items(): # Obtains the rest of the entries.
      data[k] = v

    # Creates Show with gathered data from above.
    show = Show(artist_id=data['artist_id'], venue_id=data['venue_id'], start_time=data['start_time'] )
    db.session.add(show)
    db.session.commit()
    db.session.close()

    flash('Show was successfully listed!')
  
  except:
    db.session.rollback()
    db.session.close()
    error = True
    flash('Show has failed to be listed! Please check connection!')


  return render_template('pages/home.html')



@app.errorhandler(404)
def not_found_error(error):
  return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
  return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
