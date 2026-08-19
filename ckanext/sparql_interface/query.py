import re


def _normalise_endpoint_url(url):
    return (url or '').strip().rstrip('/')


def _mask_sparql_strings_and_comments(query):
    """Mask text in which a SERVICE clause must not be interpreted."""
    masked = list(query)
    index = 0
    length = len(query)

    while index < length:
        if query[index] == '#':
            end = query.find('\n', index)
            if end == -1:
                end = length
            masked[index:end] = ' ' * (end - index)
            index = end
            continue

        quote = None
        if query.startswith("'''", index) or query.startswith('"""', index):
            quote = query[index:index + 3]
        elif query[index] in ("'", '"'):
            quote = query[index]

        if quote:
            start = index
            index += len(quote)
            while index < length:
                if query.startswith(quote, index):
                    index += len(quote)
                    break
                index += 2 if query[index] == '\\' else 1
            end = min(index, length)
            masked[start:end] = ' ' * (end - start)
            continue

        index += 1

    return ''.join(masked)


def localise_self_service_clauses(query, server_url):
    """Replace SERVICE calls to the current endpoint with local groups.

    Returns the transformed query and the number of replacements. Remote
    SERVICE targets remain federated and comments/string literals are ignored.
    """
    current_endpoint = _normalise_endpoint_url(server_url)
    if not query or not current_endpoint:
        return query, 0

    visible_query = _mask_sparql_strings_and_comments(query)
    service_pattern = re.compile(
        r'\bSERVICE\s+(?:SILENT\s+)?<([^>]*)>\s*(?=\{)',
        re.IGNORECASE
    )
    replacements = [
        (match.start(), match.end())
        for match in service_pattern.finditer(visible_query)
        if _normalise_endpoint_url(match.group(1)) == current_endpoint
    ]

    for start, end in reversed(replacements):
        query = query[:start] + query[end:]

    return query, len(replacements)
