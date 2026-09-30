import hashlib
from logging import getLogger

import requests
from flask import Blueprint, jsonify, make_response, redirect, request, url_for
from datetime import datetime
import ckan.plugins.toolkit as tk
from ckan.plugins.toolkit import render
from ckanext.sparql_interface.utils import sparql_query_SPARQLWrapper as utils_sparqlQuery
from ckanext.sparql_interface.models.query_hash import SparqlQueryHash as sparql_db_table
from flask import Response

logger = getLogger(__name__)

sparql = Blueprint(u'sparql_interface', __name__)


def _disable_cache(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['Surrogate-Control'] = 'no-store'
    return response


@sparql.route(u'/sparql')
def index():
    return render('sparql_interface/index.html')

@sparql.route(u'/sparql_interface')
def old_index():
    return redirect(url_for('sparql_interface.index'))

@sparql.route(u'/query')
def old_query():
    return redirect(url_for('sparql_interface.query_page'))

@sparql.route(u'/sparql_interface/query', methods=['GET', 'POST'])
def query_page():
    if not request.values.get('query') and not request.values.get('server'):
        return redirect(url_for('sparql_interface.index'))

    try:
        respuesta = utils_sparqlQuery('')
    except ValueError as error:
        return _disable_cache(jsonify({'error': str(error)})), 400
    except Exception:
        logger.exception('SPARQL endpoint request failed')
        return _disable_cache(jsonify({
            'error': 'The configured SPARQL endpoint request failed.'
        })), 502

    if request.values.get('direct_link') == '1':
        return _disable_cache(jsonify(respuesta))

    if isinstance(respuesta, Response):
        return _disable_cache(respuesta)

    response = make_response(render(
        'sparql_interface/query.html',
        extra_vars={'results': respuesta, 'direct_link': '0'}
    ))
    return _disable_cache(response)


#to save the query when "Save Query" button is clicked
@sparql.route(u'/sparql_interface/save', methods=['POST'])
def save_sparql_query():
    if not tk.asbool(tk.config.get(
            'ckanext.sparql_interface.save_enabled', True)):
        return jsonify({'error': 'Saving SPARQL queries is disabled.'}), 404

    data = request.get_json(silent=True) or {}
    sparql_query = (data.get('query') or '').strip()

    if not sparql_query:
        return jsonify({"error": "No SPARQL query provided"}), 400

    max_query_length = tk.asint(tk.config.get(
        'ckanext.sparql_interface.max_query_length', 50000
    ))
    if len(sparql_query) > max_query_length:
        return jsonify({'error': 'SPARQL query exceeds the configured size limit'}), 413

    try:
        query_hash = hashlib.sha256(
            sparql_query.encode('utf-8')
        ).hexdigest()[:32]
        url_query_hash = url_for(
            'sparql_interface.retrieve_sparql_query_template',
            query_hash=query_hash,
            _external=True
        )
        sparql_db_table.create(datetime.utcnow(), sparql_query, query_hash)
        logger.info('Saved SPARQL query %s', query_hash)
        return jsonify({"hash": url_query_hash}), 200
    except Exception:
        logger.exception('Failed to save SPARQL query')
        return jsonify({'error': 'Failed to save SPARQL query.'}), 500


# Retrieve the SPARQL query from the database when URL hash is given
def retrieve_sparql_query(query_hash):
    try:
        # Retrieve the record from the database using the query hash
        sparql_record = sparql_db_table.get_hash_format(query_hash_format=query_hash)

        # Check if the record exists
        if not sparql_record:
            return jsonify({"error": "No record found with the provided hash"}), 404

        # Return the data in the response
        return sparql_record

    except Exception:
        logger.exception('Failed to retrieve SPARQL query %s', query_hash)
        return jsonify({'error': 'Failed to retrieve SPARQL query.'}), 500

@sparql.route(u'/sparql/<query_hash>', methods=['GET'])
def retrieve_sparql_query_template(query_hash):
    if len(query_hash) != 32 or any(
            char not in '0123456789abcdef' for char in query_hash.lower()):
        return jsonify({'error': 'Invalid SPARQL query hash.'}), 404
    sparql_record = retrieve_sparql_query(query_hash)
    if isinstance(sparql_record, tuple):
        return sparql_record
    return render(
        'sparql_interface/snippets/hash_query.html',
        extra_vars={'query_hash': sparql_record},
    )


# LLM Feature

# def init_prompt():
#     with open(os.path.join(FEDORKG_PATH, 'prompt.txt'), 'r', encoding='utf-8') as prompt_file:
#         return prompt_file.read()

prompt = """
You are an expert assistant that converts natural language questions into precise SPARQL queries for the NFDI4Chem Search Service. The underlying knowledge graph uses vocabularies such as DCAT, schema.org, and chemistry-specific identifiers (e.g., InChI, InChIKey, ChEBI, SMILES). Assume datasets are modeled as instances of dcat:Dataset and may contain metadata such as titles, descriptions, chemical identifiers, keywords, contributors, and access links. Do not explain. Only return a valid SPARQL query that directly answers the user's question, and without formatting like code blocks. 
Instructions:
- If the query uses a namespace prefix (like dcat:, schema:, dct:), always declare it at the top with PREFIX.
- Only add PREFIXes that are needed for the specific query.
- Return only the SPARQL query. No explanations, no formatting.
Question:
"""

@sparql.route(u'/llm', methods=['GET','POST'])
def llm():

    question = request.values.get('question', None)
    if question is None:
        return jsonify({"error": "No question passed."}), 400
    if len(question) > 128:
        return jsonify({"error": "Your question exceeds 128 characters."}), 400

    api_key = tk.config.get(
        'ckanext.sparql_interface.groq_api_key'
    ) or tk.config.get('ckanext.sparql_interface.openai_api_key')
    if not api_key:
        return jsonify({"error": "LLM integration is not configured."}), 503

    try:
        import openai
    except ImportError:
        return jsonify({"error": "LLM integration dependency is not installed."}), 503

    try:
        client = openai.OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=api_key
        )
        chat_completion = client.chat.completions.create(
            messages=[{
                "role": "user",
                "content": f"{prompt}\n{question}",
            }],
            model=tk.config.get(
                'ckanext.sparql_interface.llm_model',
                'llama-3.3-70b-versatile'
            ),
        )
        return chat_completion.choices[0].message.content
    except requests.exceptions.HTTPError as http_err:
        logger.warning("LLM HTTP error: %s", http_err)
        return jsonify({"error": "LLM service returned an HTTP error."}), 502
    except Exception as err:
        logger.exception("LLM request failed")
        return jsonify({"error": "LLM request failed."}), 502
