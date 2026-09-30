import pytest


@pytest.fixture(autouse=True)
def load_sparql_interface_plugin(with_plugins):
    """Load the plugin before CKAN constructs app and database fixtures."""
    yield


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
