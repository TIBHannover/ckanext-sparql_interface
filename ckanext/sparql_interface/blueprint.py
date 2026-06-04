# encoding: utf-8
import requests
import os
# import openai
import time
from flask import Blueprint, redirect, url_for, jsonify, render_template
from datetime import datetime
from ckan.plugins.toolkit import c, render, request
import ckan.plugins.toolkit as tk
import ckan.lib.helpers as h
from ckanext.sparql_interface.utils import sparql_query_SPARQLWrapper as utils_sparqlQuery
from ckanext.sparql_interface.models.query_hash import SparqlQueryHash as sparql_db_table
from flask import Response
import hashlib
from logging import getLogger

logger = getLogger(__name__)

sparql = Blueprint(u'sparql_interface', __name__)


@sparql.route(u'/sparql')
def index():
    return render('sparql_interface/index.html')

@sparql.route(u'/sparql_interface')
def old_index():
    return h.redirect_to('sparql_interface.index')

@sparql.route(u'/query')
def old_query():

    return h.redirect_to('sparql_interface.query_page')

@sparql.route(u'/sparql_interface/query', methods=['GET', 'POST'])
def query_page():
    respuesta = utils_sparqlQuery('')

    if request.values.get('direct_link') == '1':
        return jsonify(respuesta)

    if isinstance(respuesta, Response):
        return respuesta

    return render(
        'sparql_interface/query.html',
        extra_vars={'results': respuesta, 'direct_link': '0'}
    )


#to save the query when "Save Query" button is clicked
@sparql.route(u'/sparql_interface/save', methods=['POST'])
def save_sparql_query():
    # Parse the incoming JSON request
    data = request.get_json()
    sparql_query = data.get('query')

    if not sparql_query:
        return jsonify({"error": "No SPARQL query provided"}), 400

    # Convert the SPARQL query to a short hash using SHA-256
    query_hash = hashlib.sha256(sparql_query.encode('utf-8')).hexdigest()[:32]
    url_query_hash = 'http://localhost:5000/sparql/' + query_hash
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
    #return h.redirect_to('sparql_interface.index')
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

# # OPENAI_API_KEY = "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"
# API_KEY_DEFAULT = tk.config.get('ckanext.sparql_interface.openai_api_key')
# logger.debug(API_KEY_DEFAULT)


@sparql.route(u'/llm', methods=['GET','POST'])
def llm():

    question = request.values.get('question', None)
    if question is None:
        raise ValueError('ERROR: No question passed.')
    elif len(question) > 128:
        raise ValueError('ERROR: Your question exceeds 128 characters.')
    else:
        api_key = request.values.get('apikey', None)
        logger.debug(f"THE API KEY {api_key}")
        if api_key is None:
            api_key=API_KEY_DEFAULT
            logger.debug(f"Default API KEY {api_key}")

        client = openai.OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=api_key

        )

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": f"{prompt}\n{question}",
                }
            ],
            model="llama-3.3-70b-versatile",
        )

        # data = {
        #     "model": "gpt-3.5-turbo",
        #     "messages": [
        #         {"role": "user", "content": f"{prompt}\n{question}"}
        #     ]
        # }


        try:
            response = chat_completion.choices[0].message.content
            logger.debug(response)
            content=response
            return content

        except requests.exceptions.HTTPError as http_err:
            if response.status_code == 429:
                return None
            else:
                raise RuntimeError(f"HTTP error occurred: {http_err}")
        except Exception as err:
            raise RuntimeError(f"An error occurred: {err}")





