# encoding: utf-8

from datetime import datetime
from sqlalchemy import Column, TIMESTAMP
from sqlalchemy.exc import IntegrityError
from sqlalchemy import types as _types
from ckan.model import Session
from .base import Base

class SparqlQueryHash(Base):

    __tablename__ = "sparql_query_hash"
    __table_args__ = {"schema": "public"}

    """
    Table is used to store SPARQL query hashes.
    Short and Long format which can be later used for acquiring the corresponding query when the hash code is given. 
    """

    id = Column(_types.Integer, primary_key=True, autoincrement=True, nullable=False)
    timestamp = Column(TIMESTAMP, nullable=False)
    query_long_format = Column(_types.String, nullable=False)
    query_hash_format = Column(_types.String(32), nullable=False, unique=True)

    @classmethod
    def create(cls, timestamp, query_long_format, query_hash_format):
        """
        Create a new SparqlQueryHash entry if it doesn't already exist.

        @param timestamp: The timestamp of the query.
        @param query_long_format: The full SPARQL query string.
        @param query_hash_format: The hash of the SPARQL query.
        @return: The existing or newly created SparqlQueryHash entry.
        """
        # Check if an entry with the same query_hash_format already exists
        existing_entry = Session.query(cls).filter_by(query_hash_format=query_hash_format).first()

        if existing_entry:
            # If the entry already exists, return it
            return existing_entry
        else:
            # If not, create a new entry
            new_entry = cls(
                timestamp=timestamp,
                query_long_format=query_long_format,
                query_hash_format=query_hash_format,
            )
            Session.add(new_entry)
            try:
                Session.commit()
                return new_entry
            except IntegrityError:
                Session.rollback()
                return Session.query(cls).filter_by(
                    query_hash_format=query_hash_format
                ).one()

    @classmethod
    def get_hash_format(cls, query_long_format=None, query_hash_format=None):
        """
        Retrieves the long format query based on the given hash format or the hash format
        based on the given long format query.

        @param query_long_format: The full SPARQL query string. If provided, this method will
                                  return the associated hash format.
        @param query_hash_format: The hash of the SPARQL query. If provided, this method will
                                  return the associated long format query.
        @return: The associated query string (either hash format or long format) if found,
                 otherwise None.
        """

        if query_long_format:
            # Search by long format to get hash format
            entry = Session.query(cls).filter_by(query_long_format=query_long_format).first()
            return entry.query_hash_format if entry else None
        elif query_hash_format:
            # Search by hash format to get long format
            entry = Session.query(cls).filter_by(query_hash_format=query_hash_format).first()
            return entry.query_long_format if entry else None
        else:
            # If neither format is provided, return None
            return None



