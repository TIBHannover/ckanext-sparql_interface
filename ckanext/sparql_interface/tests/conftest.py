import pytest


@pytest.fixture
def sparql_migrated_db(clean_db):
    import ckan.cli.db as db
    from ckan.model import Session
    from ckanext.sparql_interface.models.query_hash import SparqlQueryHash

    db._run_migrations('sparql_interface', None, True)
    Session.query(SparqlQueryHash).delete()
    Session.commit()
    yield
    Session.query(SparqlQueryHash).delete()
    Session.commit()

