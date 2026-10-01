import base64
import hashlib
from pathlib import Path
from urllib.parse import urlparse

import pytest
import sqlalchemy as sa


pytestmark = [
    pytest.mark.ckan_config("ckan.plugins", "sparql_interface"),
    pytest.mark.ckan_config(
        "ckanext.sparql_interface.endpoints",
        "DBpedia|https://dbpedia.org/sparql"
    ),
]


def response_text(response):
    """Return decoded response data across CKAN's test client versions."""
    return response.get_data(as_text=True)


def test_plugin_loads():
    import ckan.plugins as plugins

    assert plugins.plugin_loaded("sparql_interface")


def test_plugin_registers_routes_and_helpers(app):
    import ckan.plugins.toolkit as tk

    routes = {rule.rule for rule in app.flask_app.url_map.iter_rules()}
    assert {
        "/sparql",
        "/sparql/<query_hash>",
        "/sparql_interface",
        "/sparql_interface/query",
        "/sparql_interface/save",
        "/llm",
    }.issubset(routes)
    assert tk.h.sparql_endpoint_url() == "https://dbpedia.org/sparql"
    assert tk.h.sparql_project_name() == "nfdi4chem"
    assert tk.config["extra_template_paths"].split(",")[0].endswith(
        "ckanext/sparql_interface/templates"
    )


def test_homepage_renders_with_plugin_enabled(app):
    response = app.get("/")

    assert response.status_code == 200


def test_header_contains_sparql_navigation_link(app):
    response = app.get("/")

    contents = response_text(response)
    assert 'href="/sparql"' in contents
    assert ">SPARQL</a>" in contents
    assert contents.index(">Groups</a>") < contents.index(">SPARQL</a>")
    assert contents.index(">SPARQL</a>") < contents.index(">About</a>")


def test_sparql_navigation_link_is_active_on_editor_page(app):
    response = app.get("/sparql")

    contents = response_text(response)
    assert 'class="active"><a href="/sparql"' in contents


@pytest.mark.parametrize("enabled", [True, False])
def test_user_manual_navigation_detection(monkeypatch, enabled):
    import ckanext.sparql_interface.helpers as helpers

    monkeypatch.setattr(
        helpers.p,
        "plugin_loaded",
        lambda plugin: enabled and plugin == "user_manual",
    )

    assert helpers.sparql_user_manual_enabled() is enabled


def test_sparql_page_renders_yasgui(app):
    response = app.get("/sparql")

    assert response.status_code == 200
    contents = response_text(response)
    assert "SPARQL Editor" in contents
    assert 'id="yasgui"' in contents
    assert 'data-query-endpoint="/sparql_interface/query"' in contents
    assert "ckanext_sparql_interface" in contents
    assert "yasqe-4.2.28.min.js" not in contents
    assert 'id="find_datasets_by_ikey"' in contents


@pytest.mark.parametrize(
    "path, marker",
    [
        ("/public_sparql_interface/base_styles.css", ".sparql_hideme"),
        ("/public_sparql_interface/base.js", "sparqlInterfaceYasgui"),
        ("/public_sparql_interface/yasgui/yasgui-4.2.28.min.js", "Yasgui"),
    ],
)
def test_required_static_assets_are_served(app, path, marker):
    response = app.get(path)

    assert response.status_code == 200
    assert marker in response_text(response)


@pytest.mark.ckan_config("ckanext.sparql_interface.profile", "sfb1153")
def test_sfb1153_page_renders_its_sample_query_button(app):
    response = app.get("/sparql")

    contents = response_text(response)
    assert 'id="sfb1153"' in contents
    assert 'id="sfb1368"' not in contents
    assert 'id="find_datasets_by_ikey"' not in contents


@pytest.mark.ckan_config("ckanext.sparql_interface.profile", "sfb1368")
def test_sfb1368_page_renders_its_sample_query_button(app):
    response = app.get("/sparql")

    contents = response_text(response)
    assert 'id="sfb1368"' in contents
    assert 'id="sfb1153"' not in contents
    assert 'id="find_datasets_by_ikey"' not in contents


@pytest.mark.ckan_config("ckanext.sparql_interface.profile", "")
@pytest.mark.ckan_config("ckanext.sparql_interface.project_name", "crc1153")
def test_historic_crc_profile_alias_is_supported(app):
    response = app.get("/sparql")

    assert 'id="sfb1153"' in response_text(response)


@pytest.mark.parametrize("path", ["/sparql_interface", "/sparql_interface/query"])
def test_legacy_routes_redirect(app, path):
    response = app.get(path, status=302, follow_redirects=False)

    assert response.location.endswith("/sparql")


def test_old_query_route_redirects_to_query_endpoint(app):
    response = app.get("/query", status=302, follow_redirects=False)

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


def test_query_results_template_renders(app, monkeypatch):
    from ckanext.sparql_interface import blueprint

    monkeypatch.setattr(
        blueprint,
        "utils_sparqlQuery",
        lambda data_structure: {
            "head": {"vars": ["label"]},
            "results": {"bindings": [{"label": {"value": "Example"}}]},
        },
    )
    response = app.post(
        "/sparql_interface/query",
        params={
            "query": "SELECT * WHERE { ?s ?p ?o } LIMIT 1",
            "server": "https://dbpedia.org/sparql",
        },
    )

    assert response.status_code == 200
    contents = response_text(response)
    assert "SPARQL Results" in contents
    assert "Example" in contents


@pytest.mark.ckan_config("ckanext.sparql_interface.auth_enabled", "true")
@pytest.mark.ckan_config(
    "ckanext.sparql_interface.auth_endpoints",
    "https://dbpedia.org/sparql",
)
@pytest.mark.ckan_config("ckanext.sparql_interface.auth_username", "test-user")
@pytest.mark.ckan_config("ckanext.sparql_interface.auth_password", "test-password")
def test_sparql_basic_auth_header_uses_config():
    from ckanext.sparql_interface.utils import _basic_auth_headers

    expected_auth = base64.b64encode(
        b"test-user:test-password"
    ).decode("utf-8")

    assert _basic_auth_headers("https://dbpedia.org/sparql/") == {
        "Authorization": "Basic {}".format(expected_auth)
    }


@pytest.mark.ckan_config("ckanext.sparql_interface.auth_enabled", "true")
@pytest.mark.ckan_config(
    "ckanext.sparql_interface.auth_endpoints",
    "https://trusted.example/sparql",
)
@pytest.mark.ckan_config("ckanext.sparql_interface.auth_username", "test-user")
@pytest.mark.ckan_config("ckanext.sparql_interface.auth_password", "test-password")
def test_sparql_basic_auth_is_not_sent_to_other_endpoints():
    from ckanext.sparql_interface.utils import _basic_auth_headers

    assert _basic_auth_headers("https://dbpedia.org/sparql") == {}


def test_unconfigured_endpoint_is_rejected(app):
    response = app.post(
        "/sparql_interface/query",
        params={
            "query": "SELECT * WHERE { ?s ?p ?o } LIMIT 1",
            "server": "http://127.0.0.1:5432/private",
            "direct_link": "1",
        },
        status=400,
    )

    assert response.json["error"] == "SPARQL endpoint is not configured"


def test_endpoint_parser_ignores_credentials_and_malformed_entries():
    from ckanext.sparql_interface.config import normalize_endpoint_url

    assert normalize_endpoint_url("https://Example.org/sparql/") == (
        "https://example.org/sparql"
    )
    assert normalize_endpoint_url("http://user:secret@example.org/sparql") == ""
    assert normalize_endpoint_url("file:///etc/passwd") == ""


def test_webassets_manifest_defines_frontend_bundle():
    manifest = (
        Path(__file__).parents[1]
        / "public"
        / "ckanext"
        / "sparql_interface"
        / "webassets.yaml"
    )

    assert manifest.is_file()
    contents = manifest.read_text(encoding="utf-8")
    assert "sparql_interface:" in contents
    assert "public_sparql_interface/base_styles.css" in contents
    assert "public_sparql_interface/base.js" in contents


@pytest.mark.usefixtures("sparql_migrated_db")
def test_query_save_api_returns_permanent_hash_url(app):
    query = "SELECT * WHERE { ?s ?p ?o } LIMIT 1"

    response = app.post("/sparql_interface/save", json={"query": query})

    assert response.status_code == 200
    parsed = urlparse(response.json["hash"])
    assert parsed.path == "/sparql/{}".format(
        hashlib.sha256(query.encode("utf-8")).hexdigest()[:32]
    )


@pytest.mark.usefixtures("sparql_migrated_db")
def test_query_hash_retrieval_renders_saved_query(app):
    query = "SELECT * WHERE { ?s ?p ?o } LIMIT 2"
    save_response = app.post("/sparql_interface/save", json={"query": query})
    hash_path = urlparse(save_response.json["hash"]).path

    response = app.get(hash_path)

    assert response.status_code == 200
    assert query in response_text(response)


def test_invalid_query_hash_returns_not_found(app):
    response = app.get("/sparql/not-a-valid-hash", status=404)

    assert response.json["error"] == "Invalid SPARQL query hash."


def test_database_migration_initializes_table(clean_db):
    import ckan.cli.db as db
    import ckan.model as model

    db._run_migrations('sparql_interface', None, True)

    assert "sparql_query_hash" in sa.inspect(
        model.Session.bind
    ).get_table_names()
