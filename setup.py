from setuptools import setup, find_packages
from os import path

version = '2.1'

here = path.abspath(path.dirname(__file__))

# Get the long description from the relevant file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='ckanext-sparql_interface',
    version=version,
    description="Sparql_Point",
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        'Development Status :: 4 - Beta',
        'Framework :: CKAN',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
    ],
    keywords='',
    author='Jorge Pantoja',
    author_email='jorgepantojam@gmail.com',
    url='https://github.com/OpenDataGIS/ckanext_sparql_interface',
    license='AGPL',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    include_package_data=True,
    zip_safe=False,
    python_requires='>=3.9',
    install_requires=[
        # -*- Extra requirements: -*-
    ],
    entry_points="""
        [ckan.plugins]
		sparql_interface = ckanext.sparql_interface.plugin:SparqlInterfacePlugin
		[babel.extractors]
		ckan = ckan.lib.extract:extract_ckan
	""",

    # If you are changing from the default layout of your extension, you may
    # have to change the message extractors, you can read more about babel
    # message extraction at
    # http://babel.pocoo.org/docs/messages/#extraction-method-mapping-and-configuration
    message_extractors={
        'ckanext': [
            ('**.py', 'python', None),
            ('**.js', 'javascript', None),
            ('**/templates/**.html', 'ckan', None),
        ],
    }
)
