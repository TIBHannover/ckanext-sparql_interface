import base64
import hashlib
from urllib.parse import urlparse

import pytest


pytestmark = [
    pytest.mark.ckan_config("ckan.plugins", "sparql_interface"),
    pytest.mark.ckan_config(
        "ckanext.sparql_interface.endpoints",
        "DBpedia|https://dbpedia.org/sparql"
    ),
    pytest.mark.usefixtures("with_plugins"),
]


def test_plugin_loads():
    import ckan.plugins as plugins

    assert plugins.plugin_loaded("sparql_interface")


def test_sparql_page_renders_yasgui(app):
    response = app.get("/sparql")

    assert response.status_code == 200
    assert "SPARQL Editor" in response.text
    assert 'id="yasgui"' in response.text


@pytest.mark.parametrize("path", ["/sparql_interface", "/sparql_interface/query"])
def test_legacy_routes_redirect(app, path):
    response = app.get(path, status=302)

    assert response.location.endswith("/sparql")


def test_old_query_route_redirects_to_query_endpoint(app):
    response = app.get("/query", status=302)

    assert response.location.endswith("/sparql_interface/query")


def test_legacy_query_route_calls_proxy(app, monkeypatch):
    from ckanext.sparql_interface import blueprint

    monkeypatch.setattr(
        blueprint,
        "utils_sparqlQuery",
        lambda data_structure: {
            "head": {"vars": ["s"]},
            "results": {"bindings": []},
        },
    )

    response = app.post(
        "/sparql_interface/query",
        params={
            "query": "SELECT * WHERE { ?s ?p ?o } LIMIT 1",
            "server": "https://example.test/sparql",
            "direct_link": "1",
        },
    )

    assert response.status_code == 200
    assert response.json["head"]["vars"] == ["s"]


@pytest.mark.ckan_config("ckanext.sparql_interface.username", "test-user")
@pytest.mark.ckan_config("ckanext.sparql_interface.password", "test-password")
def test_sparql_basic_auth_header_uses_config():
    from ckanext.sparql_interface.utils import _basic_auth_headers

    expected_auth = base64.b64encode(
        b"test-user:test-password"
    ).decode("utf-8")

    assert _basic_auth_headers() == {
        "Authorization": "Basic {}".format(expected_auth)
    }


@pytest.mark.ckan_config("ckanext.sparql_interface.username", "")
@pytest.mark.ckan_config("ckanext.sparql_interface.password", "")
def test_sparql_basic_auth_header_is_empty_without_configured_credentials():
    from ckanext.sparql_interface.utils import _basic_auth_headers

    assert _basic_auth_headers() == {}


@pytest.mark.usefixtures("sparql_migrated_db")
def test_query_save_api_returns_permanent_hash_url(app):
    query = "SELECT * WHERE { ?s ?p ?o } LIMIT 1"

    response = app.post_json("/sparql_interface/save", {"query": query})

    assert response.status_code == 200
    parsed = urlparse(response.json["hash"])
    assert parsed.path == "/sparql/{}".format(
        hashlib.sha256(query.encode("utf-8")).hexdigest()[:32]
    )


@pytest.mark.usefixtures("sparql_migrated_db")
def test_query_hash_retrieval_renders_saved_query(app):
    query = "SELECT * WHERE { ?s ?p ?o } LIMIT 2"
    save_response = app.post_json("/sparql_interface/save", {"query": query})
    hash_path = urlparse(save_response.json["hash"]).path

    response = app.get(hash_path)

    assert response.status_code == 200
    assert query in response.text


def test_database_migration_initializes_table(clean_db):
    import ckan.cli.db as db
    import ckan.model as model

    db._run_migrations('sparql_interface', None, True)

    assert model.Session.bind.has_table("sparql_query_hash")
