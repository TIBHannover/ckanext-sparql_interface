from urllib.parse import urlparse
import ckan.plugins as p
from ckanext.sparql_interface.utils import sparql_query_SPARQLWrapper as utils_sparqlQuery
from logging import getLogger
import hashlib


logger = getLogger(__name__)

all_helpers = {}

def helper(fn):
    """
    collect helper functions into ckanext.sparql.all_helpers dict
    """
    all_helpers[fn.__name__] = fn
    return fn

### GET FUNCTIONS ###

#Returns get/post query param data

@helper
def get_query():
    return p.toolkit.request.values.get('query')

#Returns get/post direct_link param to check whether to return in a specific format the data

@helper
def check_direct_link():
    return p.toolkit.request.values.get('direct_link')

#Used to check whether a string is a url

@helper
def check_is_url(strtocheck):
    results = urlparse(strtocheck)
    # logger.debug(f'results: {results}')
    return results.scheme

@helper
def sparql_endpoint_url():
    endpointUrl = p.toolkit.config.get('ckanext.sparql_interface.endpoint_url', 'http://dbpedia.org/sparql')
    #logger.debug("endpointUrl: " + endpointUrl)
    return endpointUrl

@helper
def sparql_hide_endpoint_url():
    hideEndpointUrl = p.toolkit.asbool(p.toolkit.config.get('ckanext.sparql_interface.hide_endpoint_url', 'False'))
    #logger.debug("hideEndpointUrl: %s" % hideEndpointUrl)
    return hideEndpointUrl

@helper
def sparqlQuery(data_structure):
    return utils_sparqlQuery(data_structure)



@helper
def sparql_endpoint_options():
    raw = p.toolkit.config.get(
        'ckanext.sparql_interface.endpoints',
        'DBpedia|https://dbpedia.org/sparql'
    )

    endpoints = []
    for item in raw.split(','):
        label, url = item.strip().split('|', 1)
        endpoints.append({
            'label': label.strip(),
            'url': url.strip()
        })

    return endpoints


@helper
def default_sparql_endpoint_url():
    return p.toolkit.config.get(
        'ckanext.sparql_interface.default_endpoint',
        'https://dbpedia.org/sparql'
    )




