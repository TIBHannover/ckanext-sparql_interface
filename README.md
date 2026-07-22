# CKAN SPARQL Interface Extension

Forked from [OpenDataGIS/ckanext-sparql_interface](https://github.com/OpenDataGIS/ckanext-sparql_interface).

This extension adds a YASGUI-based SPARQL editor to CKAN and proxies query execution to configured SPARQL endpoints.

- **Version:** 2.1.0
- **Status:** Development
- **Tested CKAN version:** 2.10.7
- **Python:** 3.9

The extension has primarily been tested with Virtuoso SPARQL endpoints and is maintained for the NFDI4Chem Search Service.

## Installation

Activate your CKAN virtual environment, then install the extension in editable mode:

```bash
git clone https://github.com/OpenDataGIS/ckanext-sparql_interface.git
cd ckanext-sparql_interface
pip install -r requirements.txt
pip install -e .
```

Add the plugin to your CKAN configuration:

```ini
ckan.plugins = sparql_interface
```

Apply CKAN and plugin database migrations in your CKAN environment:

```bash
ckan -c /etc/ckan/default/ckan.ini db upgrade
ckan -c /etc/ckan/default/ckan.ini db pending-migrations --apply
```

## Configuration

Required or commonly used options:

```ini
ckanext.sparql_interface.endpoint_url = https://dbpedia.org/sparql
ckanext.sparql_interface.endpoints = DBpedia|https://dbpedia.org/sparql,NFDI4Chem|https://example.org/sparql
ckanext.sparql_interface.hide_endpoint_url = false
ckanext.sparql_interface.username =
ckanext.sparql_interface.password =
```

`ckanext.sparql_interface.endpoints` is a comma-separated list of `Label|URL` values shown in the endpoint selector. If omitted, DBpedia is used as the default example endpoint.

If the configured SPARQL endpoint requires Basic authentication, set `ckanext.sparql_interface.username` and `ckanext.sparql_interface.password` explicitly in the CKAN config. Leave both values empty for public endpoints. Do not hardcode credentials in `utils.py` or commit real secrets.

The `/llm` route is optional and disabled unless an API key is configured. Do not commit real secrets.

```ini
ckanext.sparql_interface.groq_api_key = <set with environment-specific secret management>
ckanext.sparql_interface.llm_model = llama-3.3-70b-versatile
```

The legacy `ckanext.sparql_interface.openai_api_key` key is still read as a fallback for existing deployments, but new deployments should use `ckanext.sparql_interface.groq_api_key`.

## Public Routes

- `/sparql` renders the YASGUI SPARQL interface.
- `/sparql_interface` redirects to `/sparql`.
- `/sparql_interface/query` executes SPARQL queries when `query` and `server` input is provided.
- `/sparql_interface/save` stores a query and returns a permanent `/sparql/<hash>` URL.
- `/sparql/<hash>` renders the saved query in the editor.

## Development and Tests

The repository includes `test.ini` for CKAN pytest runs. In a CKAN 2.10.7 Docker test environment:

```bash
pip install -r requirements.txt
pip install -e .
ckan -c test.ini db upgrade
ckan -c test.ini db pending-migrations --apply
pytest --ckan-ini=test.ini --cov=ckanext.sparql_interface --disable-warnings ckanext/sparql_interface/tests
```

GitHub Actions runs the same extension test target inside `ckan/ckan-dev:2.10.7` with PostgreSQL, Solr, and Redis services.

## Notes

To configure custom sample queries, edit `ckanext/sparql_interface/templates/sparql_interface/snippets/sample_query.html`.

To change default prefixes used by frontend helpers, edit `prefixes` in `ckanext/sparql_interface/public/ckanext/sparql_interface/public_sparql_interface/base.js`.
