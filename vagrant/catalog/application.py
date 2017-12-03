from flask import Flask,  render_template,  request
from flask import redirect,  url_for,  flash,  jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base,  Genre,  Books,  Authors,  User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests


app = Flask(__name__)

engine = create_engine('sqlite:///bookslibrary.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

CLIENT_ID = json.loads(
            open('client_secrets.json',  'r').read()
            )['web']['client_id']
APPLICATION_NAME = "MyLibrary"


@app.route('/library/<int:bookId>/JSON')
def bookJSON(bookId):
    bookQ = session.query(Books).filter_by(id=bookId).one()
    book =  session.query(Books).filter_by(id=bookId).all()
    author = session.query(Authors).filter_by(id=bookQ.author_id).all()
    user = session.query(User).filter_by(id=bookQ.user_id).all()
    genre = session.query(Genre).filter_by(id=bookQ.genre_id).all()

    return jsonify(bookInfo=[i.serialize for i in book],
                   authorInfo=[j.serialize for j in author],
                   userInfo=[k.serialize for k in user],
                   genreInfo=[l.serialize for l in genre])


@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html',  STATE=state)


@app.route('/gconnect',  methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'),  401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json',  scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'),  401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url,  'GET')[1])
    # If there was an error in the access token info,  abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')),  500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."),  401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."),  401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
                   json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token,  'alt': 'json'}
    answer = requests.get(userinfo_url,  params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists,  if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome,  '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style="width: 300px; height: 300px;border-radius: 150px;'
    output += '-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

# User Helper Functions


def createUser(login_session):
    newUser = User(name=login_session['username'],  email=login_session[
                   'email'],  picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

# DISCONNECT - Revoke a current user's token and reset their login_session


@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'),  401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url,  'GET')[0]
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(
                   json.dumps('Successfully disconnected.'),  200)
        response.headers['Content-Type'] = 'application/json'
        genres = session.query(Genre).all()
        allBooks = session.query(Books).limit(10).all()
        return render_template('mainPagePublic.html',  genreId=0,
                               genres=genres,  books=allBooks)
    else:
        response = make_response(
                   json.dumps('Failed to revoke token for given user.',  400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/')
@app.route('/library/')
def bookListStart():
    genres = session.query(Genre).all()
    allBooks = session.query(Books.id, Books.title, Books.cover_art,
                             Books.synopsis, Books.genre_id, Books.author_id,
                             User.name.label("uName"),
                             Authors.name.label("aName")).filter(
                                     Books.user_id == User.id,
                                     Books.author_id ==
                                     Authors.id).order_by(
                                     Books.id.desc()).limit(10).all()

    if 'username' not in login_session:
        return render_template('mainPagePublic.html',  genreId=0,
                               genres=genres,  books=allBooks)
    else:
        return render_template('mainPage.html', genreId=0, genres=genres,
                               books=allBooks)


@app.route('/library/<int:genre_id>/')
@app.route('/library/<int:genre_id>/genre/')
def genre(genre_id):
    genres = session.query(Genre).all()
    genSel = session.query(Genre).filter_by(id=genre_id).one()
    genBooks = session.query(Books.id, Books.title, Books.synopsis,
                             Books.cover_art, Books.genre_id,
                             User.name.label("uName"),
                             Authors.name.label("aName")).filter(
                                     Books.user_id == User.id,
                                     Books.author_id == Authors.id,
                                     Books.genre_id == genre_id).all()
    if 'username' not in login_session:
        return render_template('mainPagePublic.html',  genreId=genre_id,
                               genres=genres,  books=genBooks,  genSel=genSel)
    else:
        return render_template('mainPage.html', genreId=genre_id,
                               genres=genres, books=genBooks,
                               genSel=genSel)


@app.route('/library/editGenre/<int:genreId>', methods=['GET', 'POST'])
def editGenre(genreId):
    if 'username' not in login_session:
        return redirect('/login')

    genre = session.query(Genre).filter_by(id=genreId).one()
    books = session.query(Books).filter_by(genre_id=genreId).all()

    if login_session['user_id'] != genre.user_id:

        returnVal = "<script>function myFunction(){"
        returnVal += "alert('You are not authorized to edit this genre."
        returnVal += "Please create your own genre entry in order to edit"
        returnVal += "items.');}</script><body onload='myFunction()'>"

        return returnVal

    if request.method == 'POST':
        if request.form['edGenre'] == 'Update':
            genre.id = genreId
            genre.genre = request.form['genre']
            session.add(genre)
            session.commit()
        else:
            session.delete(genre)
            session.commit()

        return redirect(url_for('bookListStart'))
    else:
        return render_template('editGenre.html', genre=genre,
                               book_count=len(books))


@app.route('/library/addGenre/', methods=['GET', 'POST'])
def addNewGenre():
    if 'username' not in login_session:
        return redirect('/login')

    if request.method == 'POST':
        newGenre = Genre(genre=request.form['genre'], user_id=login_session['user_id'])
        session.add(newGenre)
        session.commit()
        return redirect(url_for('bookListStart'))
    else:
        return render_template('newgenre.html',  genre_id=0)


@app.route('/library/addBook/<int:genreId>', methods=['GET', 'POST'])
def addNewBook(genreId):
    if 'username' not in login_session:
        return redirect('/login')

    if request.method == 'POST':
        artURL = request.form['coverArt']
        r = requests.get(artURL,  allow_redirects=True)
        fileName = "static/"
        fileName += request.form['title']
        fileName += ".jpg"

        fileName = fileName.replace(' ', '')
        fileName = fileName.replace("'", "")

        open(fileName, 'wb').write(r.content)
        fileName = fileName.replace('static/', '')

        newBook = Books(title=request.form['title'],
                        genre_id=request.form['genre'],
                        author_id=request.form['author'],
                        synopsis=request.form['syn'],
                        cover_art=fileName,
                        user_id=login_session['user_id'])
        session.add(newBook)
        session.commit()
        return redirect(url_for('bookListStart'))
    else:
        genres = session.query(Genre).all()
        authors = session.query(Authors).all()

        return render_template('newBook.html',  genres=genres,
                               authors=authors, genre_id=genreId)


@app.route('/library/delBook/<int:genreId>/<int:bookId>',
           methods=['GET',  'POST'])
def delBook(genreId, bookId):
    if 'username' not in login_session:
        return redirect('/login')

    genres = session.query(Genre).all()
    authors = session.query(Authors).all()
    book = session.query(Books).filter_by(id=bookId).one()

    itemToDelete = session.query(Books).filter_by(id=bookId).one()
    if login_session['user_id'] != book.user_id:
        returnVal = "<script>function myFunction() {alert('You are not"
        returnVal += "authorized to delete this book. Please create your "
        returnVal += "own books in order to delete them.');}</script>"
        returnVal += "<body onload='myFunction()'>"
        return returnVal

    if request.method == 'POST':
        if request.form['delBook'] == 'Yes':
            session.delete(itemToDelete)
            session.commit()
            flash('Book Successfully Deleted')
            return redirect(url_for('bookListStart'))
        else:
            return render_template('updBook.html',  genres=genres,
                                   authors=authors,  genre_id=genreId,
                                   book=book)

    else:
        return render_template('delBook.html',  genres=genres,
                               authors=authors,  genre_id=genreId,
                               book=book)


@app.route('/library/updBook/<int:genreId>/<int:bookId>',
           methods=['GET',  'POST'])
def updBook(genreId, bookId):
    if 'username' not in login_session:
        return redirect('/login')

    genres = session.query(Genre).all()
    authors = session.query(Authors).all()
    book = session.query(Books).filter_by(id=bookId).one()

    if login_session['user_id'] != book.user_id:

        returnVal = "<script>function myFunction(){"
        returnVal += "alert('You are not authorized to edit this book."
        returnVal += "Please create your own book entry in order to edit"
        returnVal += "items.');}</script><body onload='myFunction()'>"

        return returnVal

    if request.method == 'POST':
        if book.cover_art != request.form['cover_art']:
            artURL = request.form['cover_art']
            r = requests.get(artURL,  allow_redirects=True)
            fileName = "static/"
            fileName += request.form['title']
            fileName += ".jpg"

            fileName = fileName.replace(' ', '')
            fileName = fileName.replace("'", "")

            open(fileName, 'wb').write(r.content)
            fileName = fileName.replace('static/', '')

        if request.form['title']:
            book.title = request.form['title']
        if request.form['genre']:
            book.genre_id = request.form['genre']
        if request.form['author']:
            book.author_id = request.form['author']
        if request.form['syn']:
            book.synopsis = request.form['syn']
        if request.form['cover_art']:
            book.cover_art = fileName

        session.add(book)
        session.commit()
        return redirect(url_for('bookListStart'))
    else:
        return render_template('updBook.html',  genres=genres, authors=authors,
                               genre_id=genreId, book=book)


@app.route('/library/addAuthor/<int:genreId>',  methods=['GET', 'POST'])
def addNewAuthor(genreId):
    if 'username' not in login_session:
        return redirect('/login')

    if request.method == 'POST':
        newAuthor = Authors(name=request.form['name'], user_id=login_session['user_id'])
        session.add(newAuthor)
        session.commit()
        return redirect(url_for('addNewBook', genreId=genreId))
    else:
        return render_template('newAuthor.html', genreId=genreId)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0',  port=5000)
