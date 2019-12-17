"""Python script that calls the Expander Assets V2 API
Usage: python list_on_prem_assets.py bearer_token_here
    This code authenticates to Expanse's Expander API,
    and calls the Assets V2 API. Response is printed to stdout.
    Expander API Swagger Docs: https://api.expander.expanse.co/api/v1/docs/
    Expander API Knowledge Base: https://knowledgebase.expanse.co/expander-apis/
"""

import sys
import pprint
import requests

BASE_URL = 'http://expander.expanse.co'
ID_TOKEN_URL = BASE_URL + '/api/v1/idtoken'
ASSETS_URL = BASE_URL + '/api/v2/ip-range'


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
        limit=None,
        offset=None,
        sort=None,
        business_units=None,
        business_unit_names=None,
        inet=None,
        tags=None,
        tag_names=None,
        include=None
):
    """Constructs the parameters object for the API call.

    Args:
        limit (int): Returns at most this many results in a single api call (default: 100, max: 10,000).
        offset (int): Returns results starting at this offset (default: 0).
        sort (str): Comma-separated string; orders results by the given fields. If the field name is prefixed by a -,
                    then the ordering will be descending for that field. Use a dotted notation to order by fields
                    that are nested
                    Available values: id, -id, startAddress, -startAddress, endAddress, -endAddress, ipVersion, -ipVersion
        business_units (str): Comma-separated string; Returns only results whose Business Unit’s ID falls in the provided
                              list. NOTE: If omitted, API will return results for all Business Units the user has
                              permissions to view. Also, cannot be used with the business-unit-names parameter.
        business_unit_names (str): Comma-separated string; Returns only results whose Business Unit’s name falls in the
                                   provided list. NOTE: If omitted, API will return results for all Business Units the
                                   user has permissions to view. Also, cannot be used with the business-units parameter.
        inet (str): Search for given IP/CIDR block using a single IP (d.d.d.d), a dashed IP range (d.d.d.d-d.d.d.d),
                    a CIDR block (d.d.d.d/m), a partial CIDR (d.d.), or a wildcard (d.d.*.d). Returns only results
                    whose [startAddress, endAddress] range overlap with the given IP Address or CIDR.
        tags (str): Comma-separated string; Returns only results who are associated with the provided Tag IDs.
                    Cannot be used with the tag-names parameter.
        tag_names (str): Comma-separated string; Returns only results who are associated with the provided Tag names.
                         Cannot be used with the tags parameter.
        include (str): Comma-separated string; Include the provided fields as part of the serialized result.
                       Available values: annotations, severityCounts, attributionReasons,
                       relatedRegistrationInformation, locationInformation
    Returns:
         dict: the params object to be sent to the API
    """
    tokens = {
        'limit': limit,
        'offset': offset,
        'sort': sort,
        'business-units': business_units,
        'business-unit-names': business_unit_names,
        'inet': inet,
        'tags': tags,
        'tag-names': tag_names,
        'include': include
    }
    params = {}

    for token_key, token_value in tokens.items():
        if token_value is not None:
            params.update({token_key: token_value})

    return params


def get_assets(id_token, is_printing_page_results):
    """Method to call the Assets V2 API using the ID token we got earlier.
    We use a loop to handle pagination. Assets output is printed to
    stdout using pretty-print for formatting, and returned as a list of json
    objects.
   Args:
       id_token (str): The ID Token from authentication endpoint.
       is_printing_page_results(bool): Whether or not method will print results to stdout as it paginates API.
   Returns:
       list[dict]: A list of json objects, where each one is an asset.
   Raises:
       RequestException: An error occurred when making the request.
   """

    # We paginate by looping and pulling the 'next_url' from each API response
    next_url = ASSETS_URL
    params = construct_api_params()
    print('Calling {} endpoint...'.format(ASSETS_URL))
    results = []
    while next_url is not None:
        try:
            response = requests.get(
                next_url,
                headers={
                    # Use ID token from prior request to call Assets endpoint.
                    'Authorization': 'JWT ' + id_token
                },
                params=params).json()
            print(response)
            next_url = response['pagination']['next']
            page_results = response['data']
            total_count = response['meta']['totalCount']
            if is_printing_page_results:
                pprint.pprint(page_results)
            results = results + page_results
            print('Retrieved {} Assets on this page, total so far: {} out of {}'
                  .format(len(page_results), len(results), total_count))

            if next_url:
                print('Loading next page...')

        except requests.exceptions.RequestException as request_exception:
            sys.exit('Request returned an exception: ' + str(request_exception))

    if not is_printing_page_results:
        pprint.pprint(results)

    print('Process has completed: {} Total Assets have been loaded'.format(len(results)))

    return results


def main():
    """Main Method
    First, calls get_expander_id_token with CLI-provided bearer token to retrieve the ID Token.
    Next, calls get_assets with ID Token to iterate through all pages of Assets and print
        results to standard out. Set the boolean to False to only print combined results at end.
   """
    input_token = sys.argv[1] if len(sys.argv) > 1 else sys.exit('Three args required; found 0')

    id_token = get_expander_id_token(input_token)
    get_assets(id_token, True)


if __name__ == '__main__':
    main()
