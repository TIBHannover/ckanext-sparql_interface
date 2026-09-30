from logging import getLogger
from urllib.parse import urlsplit, urlunsplit

import ckan.plugins as p


logger = getLogger(__name__)

DEFAULT_ENDPOINT = 'https://dbpedia.org/sparql'
SUPPORTED_PROFILES = ('nfdi4chem', 'sfb1153', 'sfb1368')


def normalize_endpoint_url(url):
    """Return a canonical HTTP(S) endpoint URL, or an empty string."""
    value = (url or '').strip()
    if not value:
        return ''

    parsed = urlsplit(value)
    if parsed.scheme.lower() not in ('http', 'https') or not parsed.netloc:
        return ''
    if parsed.username or parsed.password or parsed.fragment:
        return ''

    path = parsed.path.rstrip('/') or '/'
    return urlunsplit((
        parsed.scheme.lower(),
        parsed.netloc.lower(),
        path,
        parsed.query,
        '',
    ))


def endpoint_options():
    """Parse configured Label|URL entries and include the default endpoint."""
    config = p.toolkit.config
    default_url = normalize_endpoint_url(config.get(
        'ckanext.sparql_interface.endpoint_url', DEFAULT_ENDPOINT
    )) or DEFAULT_ENDPOINT
    raw = config.get('ckanext.sparql_interface.endpoints', '')

    endpoints = []
    seen = set()
    for entry in raw.split(','):
        entry = entry.strip()
        if not entry:
            continue
        if '|' not in entry:
            logger.warning(
                "Ignoring malformed SPARQL endpoint entry %r; expected Label|URL",
                entry,
            )
            continue
        label, raw_url = entry.split('|', 1)
        url = normalize_endpoint_url(raw_url)
        if not label.strip() or not url:
            logger.warning("Ignoring invalid SPARQL endpoint entry %r", entry)
            continue
        if url not in seen:
            endpoints.append({'label': label.strip(), 'url': url})
            seen.add(url)

    if default_url not in seen:
        endpoints.insert(0, {'label': 'Default', 'url': default_url})

    return endpoints


def default_endpoint_url():
    configured = normalize_endpoint_url(p.toolkit.config.get(
        'ckanext.sparql_interface.endpoint_url', DEFAULT_ENDPOINT
    ))
    return configured or endpoint_options()[0]['url']


def endpoint_is_allowed(url):
    normalized = normalize_endpoint_url(url)
    if not normalized:
        return False
    if p.toolkit.asbool(p.toolkit.config.get(
            'ckanext.sparql_interface.allow_custom_endpoints', False)):
        return True
    return normalized in {item['url'] for item in endpoint_options()}


def project_profile():
    """Resolve the deployment profile while accepting historic config names."""
    config = p.toolkit.config
    configured_value = config.get('ckanext.sparql_interface.profile') or config.get(
        'ckanext.sparql_interface.project_name'
    )
    value = configured_value or config.get('ckan.site_title', '')
    normalized = ''.join(ch for ch in str(value).lower() if ch.isalnum())
    aliases = {
        'nfdi4chem': 'nfdi4chem',
        'sfb1153': 'sfb1153',
        'crc1153': 'sfb1153',
        'sfb1368': 'sfb1368',
        'crc1368': 'sfb1368',
    }
    for alias, profile in aliases.items():
        if alias in normalized:
            return profile

    if configured_value:
        logger.warning(
            "Unknown SPARQL interface profile %r; using nfdi4chem", value
        )
    return 'nfdi4chem'
