import os

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

        # CKAN searches extension template directories in registration order.
        # Keep this extension's header override ahead of project themes that
        # replace the complete navigation block.
        template_path = os.path.join(os.path.dirname(__file__), 'templates')
        template_paths = [
            path for path in config.get('extra_template_paths', '').split(',')
            if path and os.path.normpath(path) != os.path.normpath(template_path)
        ]
        config['extra_template_paths'] = ','.join(
            [template_path] + template_paths
        )

        p.toolkit.add_public_directory(config, 'public/ckanext/sparql_interface')
        p.toolkit.add_resource('public/ckanext/sparql_interface', 'ckanext_sparql_interface')

    def get_helpers(self):
        return dict(sparql_helpers.all_helpers)
