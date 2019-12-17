"""Python script that calls the Expander Events API
Usage: python list_events.py start_date end_date bearer_token_here
    This code authenticates to Expanse's Expander API,
    and calls the Events API. Response is printed to stdout.
    Format of start and end dates should be YYYY-MM-DD
    Expander API Swagger Docs: https://api.expander.expanse.co/api/v1/docs/
    Expander API Knowledge Base: https://knowledgebase.expanse.co/expander-apis/
"""
import pprint
import sys
from datetime import datetime

import requests

BASE_URL = 'http://expander.expanse.co'
ID_TOKEN_URL = BASE_URL + '/api/v1/idtoken'
EVENTS_URL = BASE_URL + '/api/v1/events'


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


def check_date_params(start, end):
    """Checks that the date params are valid

    Args:
        start (str): Starting date for the call in format YYYY-MM-DD
        end (str): Ending date for the call in format YYYY-MM-DD
    """
    date_format = '%Y-%m-%d'
    if datetime.strptime(end, date_format) < datetime.strptime(start, date_format):
        sys.exit('end_date must be the same as or later than start_date')
    if datetime.strptime(end, date_format).date() == datetime.today().date():
        sys.exit('end_date must be earlier than today')


def construct_api_params(
        business_unit=None,
        event_type=None,
        limit=None,
        page_token=None
):
    """
    Constructs the parameters object for the API call. Note that startDateUtc and
    endDateUtc are not listed here (although they are parameters); this is because
    they are included already in the URL

    Args:
        business_unit (str): Comma separated list of business unit IDs
        event_type (str): Comma separated list of event types.
                          Allowed event types are: ON_PREM_EXPOSURE_APPEARANCE,ON_PREM_EXPOSURE_DISAPPEARANCE,
                          ON_PREM_EXPOSURE_REAPPEARANCE. Beta event types are: CLOUD_EXPOSURE_APPEARANCE,
                          CLOUD_EXPOSURE_DISAPPEARANCE,CLOUD_EXPOSURE_REAPPEARANCE
        limit (int): Number of events to be fetched per page of results. Max and default value is 10,000
        page_token (str): Page token of page
    Returns:
         dict: the params object to be sent to the API
    """
    tokens = {
        'businessUnit': business_unit,
        'eventType': event_type,
        'limit': limit,
        'pageToken': page_token
    }
    params = {}

    for token_key, token_value in tokens.items():
        if token_value is not None:
            params.update({token_key: token_value})

    return params


def get_events(id_token, start_date, end_date, is_printing_page_results):
    """Method to call the Events API using the ID token we got earlier.
    We use a loop to handle pagination. Events output is printed to
    stdout using pretty-print for formatting, and returned as a list of json
    objects.
   Args:
       id_token (str): The ID Token from authentication endpoint.
       start_date (str): The start date to search in format YYYY-MM-DD
       end_date (str): The end date to search in format YYYY-MM-DD
       is_printing_page_results(bool): Whether or not method will print results to stdout as it paginates API.
   Returns:
       list[dict]: A list of json objects, where each one is an event.
   Raises:
       RequestException: An error occurred when making the request.
   """

    # We paginate by looping and pulling the 'next_url' from each API response
    next_url = EVENTS_URL + '?startDateUtc={}&endDateUtc={}'.format(start_date, end_date)
    params = construct_api_params()
    print('Calling {} endpoint...'.format(EVENTS_URL))
    results = []
    while next_url is not None:
        try:
            response = requests.get(
                next_url,
                headers={
                    # Use ID token from prior request to call Events endpoint.
                    'Authorization': 'JWT ' + id_token
                },
                params=params).json()
            next_url = response['pagination']['next']
            page_results = response['data']
            if is_printing_page_results:
                pprint.pprint(page_results)
            results = results + page_results
            print('Retrieved {} Events on this page, total so far: {}'.format(len(page_results), len(results)))

            if next_url:
                print('Loading next page...')

        except requests.exceptions.RequestException as request_exception:
            sys.exit('Request returned an exception: ' + str(request_exception))

    if not is_printing_page_results:
        pprint.pprint(results)

    print('Process has completed: {} Total Events have been loaded'.format(len(results)))

    return results


def main():
    """Main Method
    First, calls get_expander_id_token with CLI-provided bearer token to retrieve the ID Token.
    Next, calls get_events with ID Token to iterate through all pages of Events and print
        results to standard out. Set the boolean to False to only print combined results at end.
   """
    start_date = sys.argv[1] if len(sys.argv) > 1 else sys.exit('Three args required; found 0')
    end_date = sys.argv[2] if len(sys.argv) > 2 else sys.exit('Three args required; found 1')
    input_token = sys.argv[3] if len(sys.argv) > 3 else sys.exit('Three args required; found 2')
    check_date_params(start_date, end_date)

    id_token = get_expander_id_token(input_token)
    get_events(id_token, start_date, end_date, True)


if __name__ == '__main__':
    main()
