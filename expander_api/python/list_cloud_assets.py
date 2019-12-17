"""Python script that calls the Expander Cloud Assets API
Usage: python list_cloud_assets.py bearer_token_here
    This code authenticates to Expanse's Expander API,
    and calls the Cloud Assets API. Response is printed to stdout.
    Expander API Swagger Docs: https://api.expander.expanse.co/api/v1/docs/
    Expander API Knowledge Base: https://knowledgebase.expanse.co/expander-apis/
"""

import sys
import pprint
import requests

BASE_URL = 'http://expander.expanse.co'
ID_TOKEN_URL = BASE_URL + '/api/v1/idtoken'
CLOUD_ASSETS_URL = BASE_URL + '/api/v1/assets/cloud/ips'


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
        tenancy_type=None,
        account_integration=None,
        region=None,
        provider=None,
        business_unit=None,
        business_unit_name=None,
        domain=None,
        domain_search=None,
        origin=None,
        inet=None,
        limit=None,
        offset=None,
        sort=None,
):
    """Constructs the parameters object for the API call.

    Args:
        tenancy_type (str): Filter by tenancy type - Available values: single-tenant, multi-tenant
        account_integration (str): Filter by provider account integrations by IDs
        region (str): Filter by cloud regions
        provider (str): Comma-separated string; Returns only results that were found on the given providers.
                        If not set, results will include anything regardless of provider status.
                        Available values: Akamai Technologies, Amazon Web Services,
                        Google, Microsoft Azure, Other, Rackspace
        business_unit (str): Comma-separated string; Returns only results whose Business Unit’s ID falls in the provided
                             list. NOTE: If omitted, API will return results for all Business Units the user has
                             permissions to view. Also, cannot be used with the filter[business-unit-name] parameter.
        business_unit_name (str): Comma-separated string; Returns only results whose Business Unit’s name falls in the
                                  provided list. NOTE: If omitted, API will return results for all Business Units the
                                  user has permissions to view. Also, cannot be used with the
                                  filter[business-unit] parameter.
        domain (str): Search for given domain value via exact match
        domain_search (str): Search for given domain value via substring match
        origin (str): Filter by asset origin -- Available values: expanse-identified, cloud-account-integration
        inet (str): Search for given IP/CIDR block using a single IP (d.d.d.d), a dashed IP range (d.d.d.d-d.d.d.d),
                    a CIDR block (d.d.d.d/m), a partial CIDR (d.d.), or a wildcard (d.d.*.d).
        limit (int): Page size in pagination
        offset (int): Offset in pagination
        sort (str): Sort by specified properties -- Available values: ip, -ip, lastSeen, -lastSeen, provider.name, -provider.name
    Returns:
         dict: the params object to be sent to the API
    """
    tokens = {
        'filter[tenancy-type]': tenancy_type,
        'filter[account-integration]': account_integration,
        'filter[region]': region,
        'filter[provider]': provider,
        'filter[business-unit]': business_unit,
        'filter[business-unit-name]': business_unit_name,
        'filter[domain]': domain,
        'filter[domain-search]': domain_search,
        'filter[origin]': origin,
        'filter[inet]': inet,
        'page[limit]': limit,
        'page[offset]': offset,
        'sort': sort
    }
    params = {}

    for token_key, token_value in tokens.items():
        if token_value is not None:
            params.update({token_key: token_value})

    return params


def get_cloud_assets(id_token, is_printing_page_results):
    """Method to call the Cloud Assets API using the ID token we got earlier.
    We use a loop to handle pagination. Cloud assets output is printed to
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
    next_url = CLOUD_ASSETS_URL
    params = construct_api_params()
    print('Calling {} endpoint...'.format(CLOUD_ASSETS_URL))
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
            next_url = response['pagination']['next']
            page_results = response['data']
            total_count = response['meta']['totalCount']
            if is_printing_page_results:
                pprint.pprint(page_results)
            results = results + page_results
            print('Retrieved {} Cloud Assets on this page, total so far: {} out of {}'
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
    Next, calls get_cloud_assets with ID Token to iterate through all pages of Cloud Assets and print
        results to standard out. Set the boolean to False to only print combined results at end.
   """
    input_token = sys.argv[1] if len(sys.argv) > 1 else sys.exit('Three args required; found 0')

    id_token = get_expander_id_token(input_token)
    get_cloud_assets(id_token, True)


if __name__ == '__main__':
    main()
