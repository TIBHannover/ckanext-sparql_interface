# CKAN SPARQL Interface

This extension adds a YASGUI SPARQL editor and a server-side SPARQL proxy to
CKAN. One codebase supports three deployments through configuration profiles:

| Profile | Historic branch | Project-specific interface |
| --- | --- | --- |
| `nfdi4chem` | `master` | NFDI4Chem sample-query buttons |
| `sfb1153` | `sfb1153` | SFB1153 sample summary query |
| `sfb1368` | `crc-sfb` | SFB1368 temperature summary query |

The default profile is `nfdi4chem`, so an existing NFDI4Chem deployment does
not acquire either SFB-specific button when upgrading.

## Compatibility

- CKAN 2.9, 2.10, and 2.11
- Python 3.9 with CKAN 2.9
- Python 3.10 with CKAN 2.10 and 2.11
- PostgreSQL-backed CKAN database
- SPARQL endpoints returning SPARQL JSON results

The continuous-integration matrix is configured for CKAN 2.9.11, 2.10.7, and
2.11.6. Treat version 3.0.1 as a production candidate until all three jobs and
the two SFB deployment smoke tests pass.

## Installation

Install the same branch or release in every CKAN instance:

```bash
pip install -r requirements.txt
pip install -e .
```

In docker-ckan, add an installation line for the eventual merged branch or
tag to `ckan/Dockerfile`, and append `sparql_interface` to `CKAN__PLUGINS`:

```dockerfile
ckanext-install.sh <repository-owner>/ckanext-sparql_interface <tag-or-branch>
```

```dotenv
CKAN__PLUGINS="... sparql_interface"
```

Add `sparql_interface` to `ckan.plugins`, then apply the extension migrations:

```bash
ckan -c /etc/ckan/default/ckan.ini db upgrade -p sparql_interface
```

The migration is idempotent. It creates the saved-query table when needed and
adds a unique constraint to query hashes. Back up a production database before
running any migration.

## Common Configuration

Every endpoint accepted by the proxy must be listed in `endpoints`. This is a
security boundary: browsers cannot make CKAN query arbitrary internal URLs.

```ini
ckanext.sparql_interface.endpoint_url = https://example.org/sparql
ckanext.sparql_interface.endpoints = Primary|https://example.org/sparql
ckanext.sparql_interface.hide_endpoint_url = false
ckanext.sparql_interface.allow_custom_endpoints = false
ckanext.sparql_interface.query_timeout = 60
ckanext.sparql_interface.max_query_length = 50000
ckanext.sparql_interface.save_enabled = true
```

Multiple selector entries use a comma-separated `Label|URL` format:

```ini
ckanext.sparql_interface.endpoints = Main|https://example.org/sparql,Archive|https://archive.example.org/sparql
```

## Deployment Profiles

Use exactly one profile in each CKAN configuration.

### NFDI4Chem (CKAN 2.9)

```ini
ckanext.sparql_interface.profile = nfdi4chem
ckanext.sparql_interface.endpoint_url = https://your-nfdi4chem-endpoint.example/sparql
ckanext.sparql_interface.endpoints = NFDI4Chem|https://your-nfdi4chem-endpoint.example/sparql
ckanext.sparql_interface.auth_enabled = false
```

### SFB1153 (CKAN 2.10 or 2.11)

```ini
ckanext.sparql_interface.profile = sfb1153
ckanext.sparql_interface.endpoint_url = https://your-sfb1153-endpoint.example/query
ckanext.sparql_interface.endpoints = SFB1153|https://your-sfb1153-endpoint.example/query
```

### SFB1368 (CKAN 2.10 or 2.11)

```ini
ckanext.sparql_interface.profile = sfb1368
ckanext.sparql_interface.endpoint_url = https://your-sfb1368-endpoint.example/query
ckanext.sparql_interface.endpoints = SFB1368|https://your-sfb1368-endpoint.example/query
```

The historic values `crc1153` and `crc1368` are accepted as aliases, but new
configuration should use `sfb1153` and `sfb1368`.

## Endpoint Authentication

Basic authentication is off by default. When an SFB endpoint requires it, add
an exact endpoint allowlist and inject the secret through deployment
configuration. Credentials are never rendered into HTML or JavaScript.

```ini
ckanext.sparql_interface.auth_enabled = true
ckanext.sparql_interface.auth_endpoints = https://your-sfb-endpoint.example/query
ckanext.sparql_interface.auth_username = readonly
ckanext.sparql_interface.auth_password = <secret>
```

`auth_endpoints` is separate from `endpoints` on purpose. An Authorization
header is sent only when the requested URL exactly matches both the normal
endpoint allowlist and the authentication allowlist.

Keep `allow_custom_endpoints = false` in production. Turning it on restores
arbitrary proxy targets and should be limited to isolated development use.

For docker-ckan, CKAN configuration keys can be supplied with uppercase
environment variables and double underscores in place of dots. For example:

```dotenv
CKANEXT__SPARQL_INTERFACE__PROFILE=sfb1153
CKANEXT__SPARQL_INTERFACE__ENDPOINT_URL=https://your-sfb1153-endpoint.example/query
CKANEXT__SPARQL_INTERFACE__ENDPOINTS=SFB1153|https://your-sfb1153-endpoint.example/query
CKANEXT__SPARQL_INTERFACE__AUTH_ENABLED=true
CKANEXT__SPARQL_INTERFACE__AUTH_ENDPOINTS=https://your-sfb1153-endpoint.example/query
CKANEXT__SPARQL_INTERFACE__AUTH_USERNAME=readonly
CKANEXT__SPARQL_INTERFACE__AUTH_PASSWORD=<secret>
```

Keep real usernames and passwords in the deployment's secret store or local
`.env`, never in this repository.

## Optional LLM Route

The `/llm` route remains disabled unless a server-side key is configured. The
client cannot supply or override this key.

```ini
ckanext.sparql_interface.groq_api_key = <secret>
ckanext.sparql_interface.llm_model = llama-3.3-70b-versatile
```

Install the optional `openai` dependency only when this route is used.

## Routes

- `/sparql` renders the editor.
- `/sparql_interface` redirects to `/sparql` for old links.
- `/sparql_interface/query` proxies queries to configured endpoints.
- `/sparql_interface/save` stores a query when saving is enabled.
- `/sparql/<hash>` opens a stored query.

## Local Verification

After placing this extension in each docker-ckan source tree, configure that
instance's profile and endpoint, rebuild its CKAN image, apply migrations, and
run:

```bash
pytest --ckan-ini=test.ini ckanext/sparql_interface/tests
```

CKAN 2.9 and 2.10 do not register CKAN's pytest plugins automatically. For
those versions, add `-p ckan.tests.pytest_ckan.ckan_setup -p
ckan.tests.pytest_ckan.fixtures` before `--ckan-ini` as shown in the CI matrix.

Test the two SFB instances separately before updating NFDI4Chem. Confirm the
visible sample button, endpoint selector, query execution, permanent-link save,
and authenticated endpoint behavior in each instance.

For the current `/home/katabathunib/trr375/docker-ckan` checkout, the base image
is CKAN 2.11.6 on Python 3.10. Its existing comment that this extension is
Python 2-only no longer applies to this branch. Replace that comment only when
you add the install line, plugin name, and SFB1153 profile during local testing.

## Branch Strategy

Development for the consolidated version is based on
`migration/ckan-2.10` in `production/multi-project`. The older `master`,
`sfb1153`, and `crc-sfb` branches remain useful as history, but deployments
should converge on one merged branch or tagged release and differ only through
CKAN configuration.
