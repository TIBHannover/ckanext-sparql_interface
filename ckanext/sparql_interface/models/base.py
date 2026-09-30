from sqlalchemy.ext.declarative import declarative_base
from ckan.model import meta

Base = declarative_base(metadata=meta.metadata)
