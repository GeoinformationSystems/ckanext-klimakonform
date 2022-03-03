import logging

from sqlalchemy import Column, DDL, event, ForeignKey, Index, types
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from model import Object

Base = declarative_base(cls=Object)

log = logging.getLogger(__name__)


class GeocodingResults(Base):
    '''
    Database Model class for the results of geocoding
    '''
    __tablename__ = 'klimakonform_geocoding'
    id = Column(types.Integer, primary_key=True, nullable=False)
    term = Column(types.UnicodeText, unique=True, nullable=False, index=True)
    coordinates = Column(types.UnicodeText, unique=True, nullable=False, index=True)


def create_tables():
    '''
    Create the necessary database tables.
    '''
    log.debug('Creating database tables')
    from ckan.model.meta import engine
    Base.metadata.create_all(engine)