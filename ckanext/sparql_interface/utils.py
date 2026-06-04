import ckan.plugins as p
import collections
import urllib.parse
import urllib.request
import urllib.error
import json
from SPARQLWrapper import SPARQLWrapper, JSON
import base64
from logging import getLogger
from ckan.common import json
from flask import make_response

logger = getLogger(__name__)


def sparql_query_SPARQLWrapper(data_structure):
    logger.debug("Entering sparql_query_SPARQLWrapper")

    c = p.toolkit.c
    c.direct_link = p.toolkit.request.params.get('direct_link')

    request_values = p.toolkit.request.values

    query_string = request_values.get('query')
    server_url = request_values.get('server')
    logger.debug("SPARQL proxy server_url: %s", server_url)

    if not query_string:
        logger.error("No query provided")
        raise ValueError("No query provided")
    if not server_url:
        logger.error("No SPARQL endpoint server URL provided")
        raise ValueError("No SPARQL endpoint server URL provided")

    # TODO: Add Credentials must be removed. Test Purpose only
    sparql = SPARQLWrapper(server_url)
    sparql.setCredentials("readonly", "one2rule4all")
    sparql.setQuery(query_string)
    sparql.setReturnFormat(JSON)

    try:
        response = sparql.query()
        # Check the HTTP status code
        status_code = response.info().get('status')
        content_type = response.info().get('Content-Type', '')

        if status_code and status_code != '200':
            logger.error(f"Received non-200 response status: {status_code}")
            return f"Error: Received status code {status_code}"

        if 'html' in content_type.lower():
            logger.error(f"Unexpected HTML response: {response.read()[:200]}")
            return "Error: Received an HTML page instead of JSON data. Check your credentials and endpoint URL."

        results = response.convert()
        c.sparql_query = query_string
        # logger.debug(f'Results from Wrapper: {results}')
        return results
    except Exception as e:
        logger.error(f"Error executing SPARQL query: {e}")
        raise


def sparqlQuery_veryNew(data_structure):
    logger.debug("Entering sparqlQuery")
    c = p.toolkit.c
    c.direct_link = p.toolkit.request.params.get('direct_link')

    # Determine the format for the response
    response_format = p.toolkit.request.params.get('type_response_query', 'json')
    if response_format == 'json':
        format = "application/json"
    elif response_format == 'turtle':
        format = "text/turtle"
    elif response_format == 'csv':
        format = "application/json"  # CSV will be converted later
    elif response_format == 'js':
        format = "application/javascript"
    else:
        format = "application/json"
    logger.debug("Format: " + format)

    params_query = {
        "query": p.toolkit.request.params.get('query'),
        "debug": "off",
        "timeout": "",
        "format": format,
        "save": "display",
        "fname": ""
    }

    querypart = urllib.parse.urlencode(params_query)
    server = p.toolkit.request.params.get('server')
    logger.debug("server: " + server)

    # Add credentials for basic authentication
    username = 'readonly'  # Replace with your username
    password = 'one2rule4all'  # Replace with your password
    auth = base64.b64encode(f'{username}:{password}'.encode('utf-8')).decode('utf-8')
    logger.debug(f'auth:{auth}')
    headers = {'Authorization': f'Basic {auth}'}

    request_url = f"{server}?{querypart}"
    request = urllib.request.Request(request_url, headers=headers)
    logger.debug(request)

    try:
        temp_result = urllib.request.urlopen(request)
    except urllib.error.HTTPError as excp:
        logger.debug(excp)
        response = make_response(f"Error accessing server: {excp}", 418)
        return response
    else:
        temp_response_query = temp_result.read()
        response_query = temp_response_query.decode("utf-8")
        logger.debug("response_query: {}".format(response_query))

        if response_format == 'json':
            data = json.loads(response_query, object_pairs_hook=collections.OrderedDict)
            response = make_response(json.dumps(data, separators=(',', ':')))
            response.content_type = 'application/json'
            logger.debug("data: {}".format(data))
            return response
        elif response_format == 'turtle':
            response = make_response(response_query)
            response.content_type = 'text/turtle'
            return response
        elif response_format == 'csv':
            data = json.loads(response_query, object_pairs_hook=collections.OrderedDict)
            output = []
            for result in data["head"]["vars"]:
                output.append(result + ",")
            output.append("\n")

            for result in data["results"]["bindings"]:
                index = 0
                for attributes, values in result.items():
                    if attributes == data["head"]["vars"][index]:
                        output.append("\"" + values['value'] + "\"" + ',')
                        index += 1
                    else:
                        key = 0
                        for listheader in data["head"]["vars"]:
                            if listheader != attributes and key >= index:
                                output.append(',')
                            elif listheader == attributes:
                                output.append("\"" + values['value'] + "\"" + ',')
                                index = key + 1
                                break
                            key += 1
                output.append("\n")
            response = make_response("".join(output))
            response.content_type = 'text/csv'
            response.charset = "utf-8-sig"
            return response
        elif response_format == 'js':
            response = make_response(response_query)
            response.content_type = "application/javascript"
            return response
        elif response_format == 'query':
            return "data.upf.edu/sparql?view_code=" + p.toolkit.request.params.get('query')
        else:
            data = json.loads(response_query, object_pairs_hook=collections.OrderedDict)
            return data


def sparqlQuery(data_structure):
    logger.debug("Entering sparqlQuery")
    c = p.toolkit.c
    c.direct_link = p.toolkit.request.params.get('direct_link')

    if p.toolkit.request.params.get('type_response_query') == 'json':
        format = "application/json"
    elif p.toolkit.request.params.get('type_response_query') == 'turtle':
        format = "text/turtle"
    elif p.toolkit.request.params.get('type_response_query') == 'csv':
        # The conversion to csv is made later
        format = "application/json"
    elif p.toolkit.request.params.get('type_response_query') == 'js':
        format = "application/javascript"
    else:
        ## Default Format
        format = "application/json"
    logger.debug("Format: " + format)
    params_query = {
        "query": p.toolkit.request.params.get('query'),
        "debug": "off",
        "timeout": "",
        "format": format,
        "save": "display",
        "fname": ""
    }

    querypart = urllib.parse.urlencode(params_query)
    # logger.debug("querypart: " + querypart)

    server_oauth = p.toolkit.request.params.get('server')
    username = 'readonly'  # Replace with your username
    password = 'one2rule4all'  # Replace with your password
    server = f"http://{username}:{password}@{server_oauth}"
    logger.debug("server: " + server)

    # logger.debug("url: {0}?{1}".format(server, querypart))

    try:
        temp_result = urllib.request.urlopen("{0}?{1}".format(server, querypart))
    except urllib.error.HTTPError as excp:
        logger.debug(excp)
        response = make_response(('{0}'.format(server), 418))
        return response

    else:
        temp_response_query = temp_result.read()
        response_query = temp_response_query.decode("utf-8")
        # logger.debug("response_query: {}".format(response_query))

        if p.toolkit.request.params.get('type_response_query') == 'json':
            data = json.loads(response_query, object_pairs_hook=collections.OrderedDict)
            response = make_response(json.dumps(data, separators=(',', ':')))
            response.content_type = 'application/json'
            # response.headers['Content-disposition'] = 'attachment; filename=query.json'
            return response
            # logger.debug("data: {}".format(data))
            # return data
        elif p.toolkit.request.params.get('type_response_query') == 'turtle':
            response = make_response(response_query)
            response.content_type = 'text/turtle'
            return response
        elif p.toolkit.request.params.get('type_response_query') == 'csv':
            data = json.loads(response_query, object_pairs_hook=collections.OrderedDict)
            output = []
            for result in data["head"]["vars"]:
                output.append(result + ",")
            output.append("\n")

            for result in data["results"]["bindings"]:
                index = 0
                for attributes, values in result.items():
                    if attributes == data["head"]["vars"][index]:
                        output.append("\"" + values['value'] + "\"" + ',')
                        index += 1
                    else:
                        key = 0
                        for listheader in data["head"]["vars"]:
                            if listheader != attributes and key >= index:
                                output.append(',')
                            elif listheader == attributes:
                                output.append("\"" + values['value'] + "\"" + ',')
                                index = key + 1
                                break
                            key += 1
                output.append("\n")
            response = make_response("".join(output))
            response.content_type = 'text/csv'
            # p.toolkit.response.headers['Content-disposition'] = 'attachment; filename=query.csv'
            response.charset = "utf-8-sig"
            return response
        elif p.toolkit.request.params.get('type_response_query') == 'js':
            p.toolkit.response.content_type = "application/javascript"
            return response_query
        elif p.toolkit.request.params.get('type_response_query') == 'query':
            return "data.upf.edu/sparql?view_code=" + p.toolkit.request.params.get('query')
        else:
            data = json.loads(response_query, object_pairs_hook=collections.OrderedDict)
        return data


def sparqlQueryold(data_structure):
    c = p.toolkit.c
    c.direct_link = p.toolkit.request.params.get('direct_link')

    if p.toolkit.request.params.get('type_response_query') == 'json':
        format = "application/json"
    elif p.toolkit.request.params.get('type_response_query') == 'turtle':
        format = "text/turtle"
    elif p.toolkit.request.params.get('type_response_query') == 'csv':
        # The conversion to csv is made later
        format = "application/json"
    elif p.toolkit.request.params.get('type_response_query') == 'js':
        format = "application/javascript"
    else:
        ## Default Format
        format = "application/json"

    params_query = {
        "default-graph": "",
        "should-sponge": "soft",
        "query": p.toolkit.request.params.get('query'),
        "debug": "off",
        "timeout": "",
        "format": format,
        "save": "display",
        "fname": ""
    }

    querypart = urllib.urlencode(params_query)
    # logger.debug("querypart: " + querypart)

    server = p.toolkit.request.params.get('server')
    logger.debug("server: " + server)

    # Add Credentials for authentication

    username = 'readonly'
    password = 'one2rule4all'
    auth = base64.b64encode(f'{username}:{password}'.encode('utf-8')).decode('utf-8')
    headers = {'Authorization': f'Basic {auth}'}

    req = urllib2.Request(server, querypart, headers)
    temp_result = urllib2.urlopen(req)
    response_query = temp_result.read()
    # logger.debug("response_query: " + response_query)

    if p.toolkit.request.params.get('type_response_query') == 'json':
        data = json.loads(response_query, object_pairs_hook=collections.OrderedDict)
        p.toolkit.response.content_type = 'application/json'
        # response.headers['Content-disposition'] = 'attachment; filename=query.json'
        return json.dumps(data, separators=(',', ':'))
    elif p.toolkit.request.params.get('type_response_query') == 'turtle':
        p.toolkit.response.content_type = 'text/turtle'
        return response_query
    elif p.toolkit.request.params.get('type_response_query') == 'csv':
        p.toolkit.response.content_type = 'text/plain'
        p.toolkit.response.headers['Content-disposition'] = 'attachment; filename=query.csv'
        p.toolkit.response.charset = "utf-8-sig"
        data = json.loads(response_query, object_pairs_hook=collections.OrderedDict)
        output = []
        for result in data["head"]["vars"]:
            output.append(result + ",")
        output.append("\n")

        for result in data["results"]["bindings"]:
            index = 0
            for attributes, values in result.items():
                if attributes == data["head"]["vars"][index]:
                    output.append("\"" + values['value'] + "\"" + ',')
                    index += 1
                else:
                    key = 0
                    for listheader in data["head"]["vars"]:
                        if listheader != attributes and key >= index:
                            output.append(',')
                        elif listheader == attributes:
                            output.append("\"" + values['value'] + "\"" + ',')
                            index = key + 1
                            break
                        key += 1
            output.append("\n")
        return "".join(output)
    elif p.toolkit.request.params.get('type_response_query') == 'js':
        p.toolkit.response.content_type = "application/javascript"
        return response_query
    elif p.toolkit.request.params.get('type_response_query') == 'query':
        return "data.upf.edu/sparql?view_code=" + p.toolkit.request.params.get('query')
    else:
        data = json.loads(response_query, object_pairs_hook=collections.OrderedDict)
        return data

