import unittest

from ckanext.sparql_interface.query import localise_self_service_clauses


ENDPOINT = 'https://example.test/fuseki/dataset/query'


class LocaliseSelfServiceClausesTest(unittest.TestCase):
    def test_localises_service_for_current_endpoint(self):
        query = 'SELECT * WHERE { SERVICE <%s> { ?s ?p ?o } }' % ENDPOINT

        self.assertEqual(
            localise_self_service_clauses(query, ENDPOINT)[0],
            'SELECT * WHERE { { ?s ?p ?o } }'
        )


    def test_localises_case_insensitively_and_ignores_trailing_slash(self):
        query = 'SELECT * WHERE { service silent <%s/>\n{ ?s ?p ?o } }' % ENDPOINT

        self.assertEqual(
            localise_self_service_clauses(query, ENDPOINT)[0],
            'SELECT * WHERE { { ?s ?p ?o } }'
        )


    def test_leaves_remote_service_unchanged(self):
        query = 'SELECT * WHERE { SERVICE <https://remote.test/query> { ?s ?p ?o } }'

        self.assertEqual(localise_self_service_clauses(query, ENDPOINT)[0], query)


    def test_does_not_rewrite_comments_or_string_literals(self):
        query = '''SELECT * WHERE {
          # SERVICE <https://example.test/fuseki/dataset/query> { ignored
          BIND("SERVICE <https://example.test/fuseki/dataset/query> {" AS ?label)
          ?s ?p ?o
        }'''

        self.assertEqual(localise_self_service_clauses(query, ENDPOINT)[0], query)


    def test_localises_multiple_self_references_only(self):
        query = '''SELECT * WHERE {
          SERVICE <https://example.test/fuseki/dataset/query> { ?s ?p ?o }
          SERVICE <https://remote.test/query> { ?s ?p2 ?o2 }
          SERVICE <https://example.test/fuseki/dataset/query/> { ?s ?p3 ?o3 }
        }'''

        result, count = localise_self_service_clauses(query, ENDPOINT)

        self.assertEqual(count, 2)
        self.assertEqual(result.count('SERVICE'), 1)
        self.assertIn('SERVICE <https://remote.test/query>', result)


if __name__ == '__main__':
    unittest.main()
