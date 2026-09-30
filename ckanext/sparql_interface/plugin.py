import ckan.plugins as p
from ckan.lib.plugins import DefaultTranslation
from ckanext.sparql_interface import blueprint
import ckanext.sparql_interface.helpers as sparql_helpers


class SparqlInterfacePlugin(p.SingletonPlugin, DefaultTranslation):
    """SPARQL interface plugin."""

    p.implements(p.IBlueprint)
    p.implements(p.IConfigurer, inherit=True)
    p.implements(p.ITemplateHelpers, inherit=True)
    p.implements(p.ITranslation)

    def get_blueprint(self):
        return blueprint.sparql

    def update_config(self, config):
        p.toolkit.add_template_directory(config, 'templates')
        p.toolkit.add_public_directory(config, 'public/ckanext/sparql_interface')
        p.toolkit.add_resource('public/ckanext/sparql_interface', 'ckanext_sparql_interface')

    def get_helpers(self):
        return dict(sparql_helpers.all_helpers)
