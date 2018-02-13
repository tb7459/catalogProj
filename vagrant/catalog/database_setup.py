import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class LibraryUsers(Base):
    __tablename__ = 'libraryusers'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))

    @property
    def serialize(self):
        return{
            'name': self.name,
        }


class Genre(Base):
    __tablename__ = 'genres'

    id = Column(Integer, primary_key=True)
    genre = Column(String(80), nullable=False)
    user_id = Column(Integer, ForeignKey('libraryusers.id'))
    libraryusers = relationship(LibraryUsers)

    @property
    def serialize(self):
        return{
            'genre': self.genre,
        }


class Authors(Base):
    __tablename__ = 'authors'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    user_id = Column(Integer, ForeignKey('libraryusers.id'))
    libraryusers = relationship(LibraryUsers)

    @property
    def serialize(self):
        return{
            'name': self.name,
        }


class Books(Base):
    __tablename__ = 'books'

    id = Column(Integer, primary_key=True)
    title = Column(String(80), nullable=False)
    cover_art = Column(String(300), nullable=True)
    synopsis = Column(String(250))

    genre_id = Column(Integer, ForeignKey('genres.id'))
    genres = relationship(Genre)

    author_id = Column(Integer, ForeignKey('authors.id'))
    authors = relationship(Authors)

    user_id = Column(Integer, ForeignKey('libraryusers.id'))
    libraryusers = relationship(LibraryUsers)

    @property
    def serialize(self):
        return{
            'title': self.title,
            'synopsis': self.synopsis,
        }


# insert at end of file #
engine = create_engine('postgresql+psycopg2://catalog:catalog2@35.171.4.160/libbooks')
Base.metadata.create_all(engine)
