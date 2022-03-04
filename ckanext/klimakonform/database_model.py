# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import logging

from sqlalchemy import Column, DDL, event, ForeignKey, Index, types
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

from ckan.model.meta import Session


log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler())


class Object(object):
    '''
    Base class for ORM classes.

    To create a declarative base for SQLAlchemy usinfromg this class::

        Base = declarative_base(cls=Object)

    '''
    __abstract__ = True

    # Based on http://stackoverflow.com/a/37419325/857390
    @classmethod
    def get_or_create(cls, create_kwargs=None, **kwargs):
        '''
        Get an instance or create it.

        At first all keyword arguments are used to search for a single
        instance. If that instance is found it is returned. If no
        instance is found then it is created using the keyword arguments
        and any additional arguments given in the ``create_kwargs``
        dict. The created instance is then returned.
        '''
        if not kwargs:
            raise ValueError('No filter keyword arguments.')
        try:
            # First assume that the object already exists
            return cls.one(**kwargs)
        except NoResultFound:
            # Since the object doesn't exist, try to create it
            kwargs.update(create_kwargs or {})
            obj = cls(**kwargs)
            try:
                with Session.begin_nested():
                    Session.add(obj)
                return obj
            except IntegrityError as e:
                log.exception(e)
                # Assume someone has raced the object creation
                return cls.one(**kwargs)
    @classmethod
    def select_if_exists(cls, **kwargs):
        if not kwargs:
            raise ValueError('No filter keyword arguments.')
        try:
            # First assume that the object already exists
            return cls.one(**kwargs).coordinates
        except NoResultFound:
            # Since the object doesn't exist, try to create it
            log.debug("No Results found in DB")
            return 

    @classmethod
    def one(cls, **kwargs):
        return cls.query().filter_by(**kwargs).one()

    @classmethod
    def filter_by(cls, **kwargs):
        return cls.query().filter_by(**kwargs)

    @classmethod
    def filter(cls, *args, **kwargs):
        return cls.query().filter(*args, **kwargs)

    @classmethod
    def query(cls):
        return Session.query(cls)

Base = declarative_base(cls=Object)

class GeocodingResults(Base):
    '''
    Database Model class for the results of geocoding
    '''
    __tablename__ = 'klimakonform_geocoding'
    id = Column(types.Integer, primary_key=True, nullable=False)
    term = Column(types.UnicodeText, unique=True, nullable=False, index=True)
    coordinates = Column(types.UnicodeText, unique=True, nullable=False, index=True)

# Todo: move this class to another module
class SearchQuery(object):
    '''
    A single search query.

    Provides the actual query string (``.string``), its normalized words
    (``.words``) and context terms (``.context_terms``).
    '''
    def __init__(self, query):
        self.query = query
        self.query_string = self._normalize_query(query['q'])
    
    def _normalize_query(self, q):
        q = q.lower()
        q = q.replace('ß', 'ss')
        return q

    def store(self):
        '''
        Store the query in the database.
        '''
        term = self.query_string.split(' ')[0]
        bbox = self.query['extras']['ext_bbox'] 
        log.debug('QS: {}'.format(self.query))
        log.debug('Saving coords for following query: {}'.format(term))
        GeocodingResults.get_or_create(term=term, coordinates=bbox)
        Session.commit()

        """
        terms = sorted((GeocodingResults.get_or_create(term=t) for t in self.words),
                       key=lambda t: t.term)
        Session.commit()
        """
    def get_results_if_exists(self):
        term = self.query_string.split(' ')[0]
        results = GeocodingResults.select_if_exists(term=term)
        if results:
            log.debug('Query Results from db: {}'.format(results))
            return results    
        return 

def create_tables():
    '''
    Create the necessary database tables.
    '''
    log.debug('Creating database tables')
    from ckan.model.meta import engine
    Base.metadata.create_all(engine)

