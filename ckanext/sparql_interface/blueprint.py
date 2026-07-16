import requests
from flask import Blueprint, redirect, url_for, jsonify, render_template, make_response, request
from datetime import datetime
from ckan.plugins.toolkit import render
import ckan.plugins.toolkit as tk
from ckanext.sparql_interface.utils import sparql_query_SPARQLWrapper as utils_sparqlQuery
from ckanext.sparql_interface.models.query_hash import SparqlQueryHash as sparql_db_table
from flask import Response
import hashlib
from logging import getLogger

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

    respuesta = utils_sparqlQuery('')

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
    data = request.get_json(silent=True) or {}
    sparql_query = data.get('query')

    if not sparql_query:
        return jsonify({"error": "No SPARQL query provided"}), 400

    query_hash = hashlib.sha256(sparql_query.encode('utf-8')).hexdigest()[:32]
    url_query_hash = url_for(
        'sparql_interface.retrieve_sparql_query_template',
        query_hash=query_hash,
        _external=True
    )
    timestamp = datetime.now()

    sparql_db_table.create(timestamp, sparql_query, query_hash )
    logger.info(f'sending it to Database')
    try:

        return jsonify({"hash": url_query_hash}), 200

    except Exception as e:
        # Handle any errors that occur during saving
        return jsonify({"error": str(e)}), 500


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

    except Exception as e:
        # Handle any errors that occur during retrieval
        return jsonify({"error": str(e)}), 500

@sparql.route(u'/sparql/<query_hash>', methods=['GET'])
def retrieve_sparql_query_template(query_hash):
    sparql_record_json = retrieve_sparql_query(query_hash)
    logger.debug(f"{sparql_record_json}")
    return render_template('sparql_interface/snippets/hash_query.html', query_hash=sparql_record_json)


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

    api_key = request.values.get('apikey') or tk.config.get(
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
