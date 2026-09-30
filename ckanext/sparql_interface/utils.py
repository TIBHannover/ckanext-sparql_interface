import base64
from logging import getLogger

import ckan.plugins as p
from SPARQLWrapper import JSON, POST, SPARQLWrapper

from ckanext.sparql_interface.config import (
    endpoint_is_allowed,
    normalize_endpoint_url,
)


logger = getLogger(__name__)


def _configured_auth_endpoints():
    raw = p.toolkit.config.get(
        'ckanext.sparql_interface.auth_endpoints', ''
    )
    return {
        normalize_endpoint_url(url)
        for url in raw.split(',')
        if normalize_endpoint_url(url)
    }


def _basic_auth_credentials(server_url):
    """Return credentials only for an explicitly trusted endpoint."""
    config = p.toolkit.config
    if not p.toolkit.asbool(config.get(
            'ckanext.sparql_interface.auth_enabled', False)):
        return None

    normalized_url = normalize_endpoint_url(server_url)
    if (not endpoint_is_allowed(normalized_url)
            or normalized_url not in _configured_auth_endpoints()):
        return None

    username = config.get('ckanext.sparql_interface.auth_username')
    password = config.get('ckanext.sparql_interface.auth_password')
    if not username or not password:
        logger.warning(
            'SPARQL authentication is enabled for %s, but credentials are incomplete',
            normalized_url,
        )
        return None
    return username, password


def _basic_auth_headers(server_url):
    credentials = _basic_auth_credentials(server_url)
    if not credentials:
        return {}
    token = base64.b64encode(
        '{}:{}'.format(*credentials).encode('utf-8')
    ).decode('ascii')
    return {'Authorization': 'Basic {}'.format(token)}


def sparql_query_SPARQLWrapper(data_structure):
    """Execute a query through a configured endpoint without exposing secrets."""
    request_values = p.toolkit.request.values
    query_string = request_values.get('query', '').strip()
    server_url = normalize_endpoint_url(request_values.get('server'))

    if not query_string:
        raise ValueError('No SPARQL query provided')
    if not endpoint_is_allowed(server_url):
        raise ValueError('SPARQL endpoint is not configured')

    max_query_length = p.toolkit.asint(p.toolkit.config.get(
        'ckanext.sparql_interface.max_query_length', 50000
    ))
    if len(query_string) > max_query_length:
        raise ValueError('SPARQL query exceeds the configured size limit')

    timeout = p.toolkit.asint(p.toolkit.config.get(
        'ckanext.sparql_interface.query_timeout', 60
    ))
    sparql = SPARQLWrapper(server_url)
    credentials = _basic_auth_credentials(server_url)
    if credentials:
        sparql.setCredentials(*credentials)
    sparql.setQuery(query_string)
    sparql.setReturnFormat(JSON)
    sparql.setMethod(POST)
    sparql.setTimeout(timeout)

    logger.info('Executing SPARQL query against configured endpoint %s', server_url)
    return sparql.query().convert()


# Kept for extensions or templates that imported the historic helper name.
sparqlQuery = sparql_query_SPARQLWrapper
