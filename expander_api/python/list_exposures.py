"""Python script that calls the Expander Exposures API

Usage: python list_exposures.py bearer_token_here

    This code authenticates to Expanse's Expander API,
    and calls the Exposures V2 API. Response is printed to stdout.

    Expander API Swagger Docs: https://api.expander.expanse.co/api/v1/docs/
    Expander API Knowledge Base: https://knowledgebase.expanse.co/expander-apis/
"""

import sys
import pprint
import requests

BASE_URL = 'http://expander.expanse.co'
ID_TOKEN_URL = BASE_URL + '/api/v1/idtoken'


def get_expander_id_token(bearer_token):
    """Method to call Expander authentication endpoint, using the Bearer token to get ID token

        For authentication, we obtain a JSON web token (JWT) via the ​IdToken​ API endpoint
        by presenting the bearer token. The resulting JWT is used to access all other endpoints.
        JWTs have an expiration time, after which they are invalid.

   Args:
       bearer_token (str): The token we use to authenticate against Expander API

   Returns:
       str: The ID Token that we receive from endpoint
   """

    try:
        print('Calling /api/v1/idtoken endpoint...')
        auth_response = requests.get(
            ID_TOKEN_URL,
            headers={
                'Authorization': 'Bearer ' + bearer_token,
                'Content-Type': 'application/json'
            },
            timeout=10).json()
        if 'error' in auth_response:
            sys.exit('API returned an error: ' + auth_response['error'])
        else:
            print('Successfully Authenticated')
            return auth_response['token']  # return the ID token that we received from endpoint
    except requests.exceptions.RequestException as request_exception:
        sys.exit('Request returned an exception: ' + str(request_exception))


def construct_api_params(
        accept=None,
        limit=None,
        offset=None,
        exposure_type=None,
        inet=None,
        content=None,
        activity_status=None,
        last_event_time=None,
        last_event_window=None,
        severity=None,
        event_type=None,
        provider=None,
        cloud=None,
        tag=None,
        business_unit=None,
        port_number=None,
        sort=None
):
    """Constructs the parameters object for the API call.

    Args:
        accept (str): When set to text/csv, this endpoint will return a CSV string. Otherwise,
                      it should be set to application/json or omitted from the request.
        limit (int): How many items to return at one time (default 100, max 10,000)
                     Note that this parameter will be ignored when requesting CSV data
        offset (int): How many items to skip before beginning to return results (default 0)
                      Note that this parameter will be ignored when requesting CSV data
        exposure_type (str): Returns only results that have an exposure type that is in the given list. The values
                             which can be used in this parameter should be retrieved from /configurations/exposures
        inet (str): Search for given IP/CIDR block using a single IP (d.d.d.d), a dashed IP range (d.d.d.d-d.d.d.d),
                    a CIDR block (d.d.d.d/m), a partial CIDR (d.d.), or a wildcard (d.d.*.d). Returns only results
                    whose IP address overlaps with the passed IP Address or CIDR
        content (str): Returns only results whose contents match the given query
        activity_status (str): Returns only results that have the given activity states Available values: active, inactive
        last_event_time (str): Returns only results whose last scanned or last disappearance were after the given timestamp
        last_event_window (str): Returns only results whose last scanned were after the beginning of the given window.
                                 If this parameter is given, lastEventTime will be ignored
        severity (str): Comma-separated string; Returns only results associated with the given severity list
        event_type (str): Returns only results that have an event type that is in the given list
                          Available values: appearance, reappearance, disappearance
        provider (str): Comma-separated string; Returns only results that were found on the given providers. The cloud
                        must be set to true to use this parameter.
                        Available values: Akamai Technologies, Amazon Web Services, Google, Microsoft Azure, Other, Rackspace
        cloud (bool): This query parameter is deprecated, and will be removed at some point in the future. If set to
                      true, return only results that were found in cloud ip space (i.e. outside of on-premise ip space)
                      If not set or set to false, return only results that were found in on-premise ip space. This
                      flag must be set to use the provider parameter.
        tag (str): Comma-separated string with no spaces after the comma; Returns only results that have ips
                   corresponding to the given set of tags
        business_unit (str): Comma-separated string; Returns only results associated with the given businessUnit
                             ids, provided that the requesting user has permissions to view results associated with the
                             given business unit
        port_number (str): Comma-separated string; Returns only results that have port numbers corresponding to the
                           given port numbers
        sort (str): Comma-separated string; orders results by the given fields. If the field name is prefixed by a -,
                    then the ordering will be descending for that field. Use a dotted notation to order by
                    fields that are nested. The values which can be used in this parameter should be retrieved
                    from /configurations/exposures. When requesting multiple exposure types via the exposureType filter,
                    the set of valid sorting fields will be the intersection of valid sorting fields from each of
                    those exposure types.
    Returns:
         dict: the params object to be sent to the API
    """
    tokens = {
        'Accept': accept,
        'limit': limit,
        'offset': offset,
        'exposureType': exposure_type,
        'inet': inet,
        'content': content,
        'activityStatus': activity_status,
        'lastEventTime': last_event_time,
        'lastEventWindow': last_event_window,
        'severity': severity,
        'eventType': event_type,
        'provider': provider,
        'cloud': cloud,
        'tag': tag,
        'businessUnit': business_unit,
        'portNumber': port_number,
        'sort': sort
    }
    params = {}

    for token_key, token_value in tokens.items():
        if token_value is not None:
            params.update({token_key: token_value})

    return params


def get_exposures(id_token, is_printing_page_results):
    """Method to call the Exposures API using the ID token we got earlier.

    We use a loop to handle pagination. Exposures output is printed to
    stdout using pretty-print for formatting, and returned as a list of json
    objects.

   Args:
       id_token (str): The ID Token from authentication endpoint.
       is_printing_page_results(bool): Whether or not method will print results to stdout as it paginates API.

   Returns:
       list[dict]: A list of json objects, where each one is an exposure.

   Raises:
       RequestException: An error occurred when making the request.
   """

    # We paginate by looping and pulling the 'next_url' from each API response
    next_url = 'http://expander.expanse.co/api/v2/exposures/ip-ports'
    params = construct_api_params()
    print('Calling v2/exposures/ip-ports endpoint...')
    results = []
    while next_url is not None:
        try:
            response = requests.get(
                next_url,
                headers={
                    # Use ID token from prior request to call Exposures endpoint.
                    'Authorization': 'JWT ' + id_token
                },
                params=params).json()
            next_url = response['pagination']['next']
            total_count = response['meta']['totalCount']
            page_results = response['data']
            if is_printing_page_results:
                pprint.pprint(page_results)
            results = results + page_results
            print('Retrieved {} Exposures on this page, total so far: {} out of {}'
                  .format(len(page_results), len(results), total_count))
            if next_url:
                print('Loading next page...')
        except requests.exceptions.RequestException as request_exception:
            sys.exit('Request returned an exception: ' + str(request_exception))

    if not is_printing_page_results:
        pprint.pprint(results)

    print('Process has completed: {} Total Exposures have been loaded'.format(len(results)))
    return results


def main():
    """Main Method

    First, calls get_expander_id_token with CLI-provided bearer token to retrieve the ID Token.
    Next, calls get_exposures with ID Token to iterate through all pages of Exposures and print
        results to standard out. Set the boolean to False to only print combined results at end.
   """
    input_token = sys.argv[1]
    id_token = get_expander_id_token(input_token)
    get_exposures(id_token, True)


if __name__ == '__main__':
    main()
