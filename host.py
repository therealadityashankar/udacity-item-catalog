#!/usr/bin/env python3
"""
A weirdly categorized book app

type ./host.py to run the app

categories and books have json endpoints at /JSON
(for eg:
 "http://localhost:5000/category/List%20of%20autobiographies/JSON")
"""
from flask import (Flask,
                   render_template,
                   jsonify,
                   request,
                   redirect,
                   url_for,
                   abort,
                   session as login_session,
                   make_response)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from databases.database_setup import Base, Category, Item, User
from flask_httpauth import HTTPBasicAuth
from functools import wraps
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import requests
import random
import string
import json
import httplib2


auth = HTTPBasicAuth()
app = Flask(__name__)


engine = create_engine('sqlite:///databases/all_info.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)


def login_required(func):
    """checks if the user logged in or not !,
    allows function to execute if user has,
    else does not"""
    @wraps(func)
    def decorator(*args, **kwargs):
        if check_logged_in():
            return func(*args, **kwargs)
        else:
            abort(401)
            return redired(url_for('main'))

    return decorator


@app.errorhandler(401)
def unauthorized_access(error):
    return make_response('you need to be logged in to use this feature !', 401)


def check_logged_in():
    """checks if user has logged in, returns True if logged in,
    False if not"""
    return 'username' in login_session


@app.route("/")
def main():
    session = DBSession()
    categories = session.query(Category).all()
    books = session.query(Item).limit(7).all()
    _books = []
    for book in books:
        category = session.query(Category).filter_by(id=book.category_id).one()
        _books.append([category, book])
    books = _books
    session.close()
    username = login_session.get('username', None)

    return render_template("main.html",
                           categories=categories,
                           books=books,
                           username=username)


@app.route('/login')
def login_user():
    return render_template('login_user.html')


@app.route('/logout')
def logout_user():
    login_session.clear()
    return redirect(url_for('login_user'))


@app.route('/login/<provider>', methods=['POST'])
def login_process(provider):
    if provider == 'google':
        token = request.data
        return authorize_google(token)

    return abort(404)


def authorize_google(auth_code):
    """authorize google sign in"""
    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(auth_code)
    except FlowExchangeError as ex:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = (
        'https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' %
        access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # # Verify that the access token is used for the intended user.
    # gplus_id = credentials.id_token['sub']
    # if result['user_id'] != gplus_id:
    #     response = make_response(json.dumps("Token's user ID doesn't match given user ID."), 401)
    #     response.headers['Content-Type'] = 'application/json'
    #     return response

    # # Verify that the access token is valid for this app.
    # if result['issued_to'] != CLIENT_ID:
    #     response = make_response(json.dumps("Token's client ID does not match app's."), 401)
    #     response.headers['Content-Type'] = 'application/json'
    #     return response

    # stored_credentials = login_session.get('credentials')
    # stored_gplus_id = login_session.get('gplus_id')
    # if stored_credentials is not None and gplus_id == stored_gplus_id:
    #     response = make_response(json.dumps('Current user is already connected.'), 200)
    #     response.headers['Content-Type'] = 'application/json'
    #     return response

    # Get user info
    h = httplib2.Http()
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    name = data['name']
    picture = data['picture']
    email = data['email']

    # see if user exists, if it doesn't make a new one
    session = DBSession()
    user = session.query(User).filter_by(email=email).first()
    if not user:
        user = User(username=name, picture=picture, email=email)
        session.add(user)
        session.commit()
    session.close()

    login_session['email'] = user.email
    login_session['username'] = user.username
    login_session['user_id'] = user.id

    return make_response('success', 200)


@app.route("/category/<category_name>")
def show_category(category_name):
    session = DBSession()
    category = session.query(Category).filter_by(name=category_name).one()
    books = session.query(Item).filter_by(category_id=category.id).all()
    session.close()
    username = login_session.get('username', None)
    return render_template("category.html",
                           category=category,
                           books=books,
                           username=username)


@app.route("/category/<category_name>/JSON")
def jsonify_category_items(category_name):
    session = DBSession()
    category = session.query(Category).filter_by(name=category_name).one()
    books = session.query(Item).filter_by(category_id=category.id).all()
    session.close()
    serialized_books = [book.serialize for book in books]
    items = dict(category=category.serialize, books=serialized_books)
    return jsonify(items)


@app.route("/category/<category_name>/items/<book_name>")
def show_book(category_name, book_name):
    session = DBSession()
    category = session.query(Category).filter_by(name=category_name).one()
    book = session.query(Item).filter_by(category_id=category.id).filter_by(name=book_name).one()
    book_user_id = book.user_id
    session.close()

    username = login_session.get('username')
    if username:
        modifyable_by_user = (book_user_id == login_session['user_id'])
    else:
        modifyable_by_user = None

    return render_template("book.html",
                           book=book,
                           username=username,
                           modifyable_by_user=modifyable_by_user,
                           category=category)

@app.route("/category/<category_name>/items/<book_name>/JSON")
def jsonify_book(category_name, book_name):
    session = DBSession()
    category = session.query(Category).filter_by(name=category_name).one()
    book = session.query(Item).filter_by(category_id=category.id).filter_by(name=book_name).one()
    book_info = book.serialize
    session.close()
    json_contents = jsonify(dict(category=category.name, book=book_info))
    return json_contents

@app.route('/new', methods=['GET', 'POST'])
@login_required
def add_new_book():
    if request.method == 'POST':
        session = DBSession()
        name = request.form['name']
        description = request.form['description']
        category_id = request.form['category_id']
        category = session.query(Category).filter_by(id=category_id).one()
        category_name = category.name
        user_id = login_session['user_id']
        new_book = Item(name=name,
                        description=description,
                        category_id=category.id,
                        user_id=user_id)

        session.add(new_book)
        session.commit()
        session.close()
        return redirect(url_for('show_category',
                                category_name=category_name))

    username = login_session['username']
    session = DBSession()
    categories = session.query(Category).all()
    session.close()
    return render_template("new_book.html",
                           username=username,
                           categories=categories)


@app.route(
    '/category/<category_name>/items/<book_name>/edit',
    methods=[
        'GET',
        'POST'])
@login_required
def edit_book(category_name, book_name):
    if request.method == 'POST':
        session = DBSession()
        category = session.query(Category).filter_by(name=category_name).one()
        book = (session.query(Item)
                .filter_by(category_id=category.id)
                .filter_by(name=book_name).one())
        userid = login_session['user_id']
        editable = (userid == book.user_id)
        if editable:
            book.name = request.form['name']
            book.description = request.form['description']
            category_name = request.form['category_name']
            category = session.query(Category).filter_by(
                name=category_name).one()
            book.category_id = category.id
            session.add(book)
            session.commit()
            session.close()
            return redirect(url_for('show_category',
                                    category_name=category.name))
        else:
            session.close()
            return abort(401)

    session = DBSession()
    book = session.query(Item).filter_by(id=book_id).one()
    category = session.query(Category).filter_by(id=book.category_id).one()
    categories = session.query(Category).all()
    categories.remove(category)
    session.close()
    return render_template("edit_book.html",
                           book=book,
                           categories=categories,
                           category=category)


@app.route(
    '/category/<category_name>/items/<book_name>/delete',
    methods=[
        'GET',
        'POST'])
@login_required
def delete_book(category_name, book_name):
    if request.method == 'POST':
        session = DBSession()
        category = session.query(Category).filter_by(name=category_name).one()
        book = (session.query(Item)
                .filter_by(category_id=category.id)
                .filter_by(name=book_name)
                .one())
        session.delete(book)
        session.commit()
        session.close()
        deletable_by_user = (login_session['user_id'] == book.user_id)
        if deletable_by_user:
            return redirect(url_for('show_category',
                                    category_name=category_name))
        else:
            return abort(401)

    session = DBSession()
    category = session.query(Category).filter_by(name=category_name).one()
    book = (session.query(Item)
            .filter_by(category_id=category.id)
            .filter_by(name=book_name)
            .one())
    session.close()
    username = login_session['username']
    return render_template("delete_book.html",
                           book=book,
                           username=username)


if __name__ == "__main__":
    app.debug = True
    secRandom = random.SystemRandom()
    app.secret_key = ''.join(
        [secRandom.choice(string.ascii_uppercase + string.digits)])
    app.run(host="0.0.0.0")
