#!/usr/bin/env python3
import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Category, Base, Item, User
from passlib.apps import custom_app_context as pwd_context

engine = create_engine('sqlite:///all_info.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)

session = DBSession()

with open("../lists/list_of_books(filled).json") as jsonfile:
    books = json.load(jsonfile)

print(books)

for book_category in books:
    category = Category(name=book_category)
    session.add(category)
    session.commit()
    for book in books[book_category]:
        item = Item(name=book['title'],
                    description=book['description'],
                    category=category,
                    user_id=1)
        session.add(item)
        session.commit()

admin = User(id=1,
             username="root",
             email="admin@localhost.com")
admin.hash_password("12345")
session.add(admin)
session.commit()
