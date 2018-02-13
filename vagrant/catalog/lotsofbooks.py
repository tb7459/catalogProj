from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import LibraryUsers, Base, Authors, Genre, Books

engine = create_engine('postgresql+psycopg2://catalog:catalog2@35.171.4.160/libbooks')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


# First user
user1 = LibraryUsers(id=1,
             name="Tim Brown",
             email="tb7459@att.com",
             picture="")

session.add(user1)
session.commit()

# First author
author1 = Authors(id=1,
                  name="Anne McCaffrey",
                  user_id=1)

session.add(author1)
session.commit()

# First Genres
genre1 = Genre(id=1,
               genre="SciFi",
               user_id=1)

genre2 = Genre(id=2,
               genre="Fantasy",
               user_id=1)

session.add(genre1)
session.commit()

session.add(genre2)
session.commit()

# First Books
book1 = Books(id=1,
              title="The Rowan",
              cover_art="TheRowan.jpg",
              synopsis="Book 1 of the Rowan Series",
              genre_id=1,
              author_id=1,
              user_id=1)

book2 = Books(id=2,
              title="Damia",
              cover_art="Damia.jpg",
              synopsis="Book 2 of the Rowan series",
              genre_id=1,
              author_id=1,
              user_id=1)

book3 = Books(id=3,
              title="Damia's Children",
              cover_art="DamiasChildren.jpg",
              synopsis="Book 3 of the Rowan series",
              genre_id=1,
              author_id=1,
              user_id=1)


session.add(book1)
session.commit()

session.add(book2)
session.commit()

session.add(book3)
session.commit()

print "added books!"
