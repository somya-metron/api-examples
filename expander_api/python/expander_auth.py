"""Python script that calls the Expander ID Token Endpoint

Usage: python expander_auth.py bearer_token_here

    This code authenticates to Expanse's Expander API using
    a Bearer token, and returns the ID Token.
    Bearer tokens are provided by Expanse when onboarding
    to the Expander API.

    Expander API Swagger Docs: https://api.expander.qadium.com/api/v1/docs/
    Expander API Knowledge Base: https://knowledgebase.expanse.co/expander-apis/
"""

import sys
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


def main():
    """Main Method

    Calls get_expander_id_token with CLI-provided bearer token to retrieve and print the ID Token.
   """
    input_token = sys.argv[1]
    id_token = get_expander_id_token(input_token)
    print(id_token)


if __name__ == '__main__':
    main()
