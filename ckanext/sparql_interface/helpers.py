import ckan.plugins as p
from urllib.parse import urlparse
from ckanext.sparql_interface.config import (
    default_endpoint_url,
    endpoint_options,
    project_profile,
)
from ckanext.sparql_interface.utils import sparql_query_SPARQLWrapper as utils_sparqlQuery
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
    return p.toolkit.request.params.get('query')

#Returns get/post direct_link param to check whether to return in a specific format the data

@helper
def check_direct_link():
    return p.toolkit.request.params.get('direct_link')

#Used to check whether a string is a url

@helper
def check_is_url(strtocheck):
    results = urlparse(strtocheck)
    # logger.debug(f'results: {results}')
    return results.scheme

@helper
def sparql_endpoint_url():
    return default_endpoint_url()

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
    return endpoint_options()


@helper
def default_sparql_endpoint_url():
    return default_endpoint_url()


@helper
def sparql_project_name():
    return project_profile()


@helper
def sparql_save_enabled():
    return p.toolkit.asbool(p.toolkit.config.get(
        'ckanext.sparql_interface.save_enabled', True
    ))

