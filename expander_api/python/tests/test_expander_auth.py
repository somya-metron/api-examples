import pytest
import unittest
import requests

from python.expander_auth import get_expander_id_token
from unittest.mock import patch, Mock


class ExpanderAuthTest(unittest.TestCase):
    def test_get_expander_id_token_success(self):
        mock_get_patcher = patch('python.list_exposures.requests.get')
        mock_bearer_token = 'example_bearer_token'
        mock_id_token_response = {
            'token': 'example_token'
        }

        # Start patching 'requests.get'.
        mock_get = mock_get_patcher.start()

        # Configure the mock to return a response with status code 200.
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = mock_id_token_response

        # Call the service, which will send a request
        id_token_response = get_expander_id_token(mock_bearer_token)

        # Capture stdout print statements
        captured = self.capsys.readouterr()

        # Stop patching 'requests'.
        mock_get_patcher.stop()

        # Assert that the method printed Success message and parsed the token from response
        self.assertEqual(captured.out, 'Calling /api/v1/idtoken endpoint...\nSuccessfully Authenticated\n')
        self.assertEqual(id_token_response, 'example_token')

    def test_get_expander_id_token_error(self):
        mock_get_patcher = patch('python.list_exposures.requests.get')
        mock_bearer_token = 'example_bearer_token'
        mock_id_token_response = {
            'error': 'Could not get an id token based on the given refresh token'
        }

        # Start patching 'requests.get'
        mock_get = mock_get_patcher.start()

        # Configure the mock to return a response with status code 200
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = mock_id_token_response

        # given user has invalid bearer token, when they run our script with it, then we should output correct 'error'
        with self.assertRaises(SystemExit) as actual_sys_exit:
            get_expander_id_token(mock_bearer_token)

        self.assertEqual(str(actual_sys_exit.exception),
                         'API returned an error: Could not get an id token based on the given refresh token')

        # Stop patching 'requests'.
        mock_get_patcher.stop()

    def test_get_expander_id_token_exception(self):
        mock_get_patcher = patch('python.list_exposures.requests.get')
        mock_bearer_token = 'example_bearer_token'
        mock_id_token_response = requests.exceptions.ConnectionError()

        # Start patching 'requests.get'
        mock_get = mock_get_patcher.start()

        # Configure the mock to return an exception
        mock_get.side_effect = mock_id_token_response

        # given API request runs into an exception, then we should exit and output exception
        with self.assertRaises(SystemExit) as actual_sys_exit:
            get_expander_id_token(mock_bearer_token)

        self.assertIn('Request returned an exception:', str(actual_sys_exit.exception))

        # Stop patching 'requests'
        mock_get_patcher.stop()

    @pytest.fixture(autouse=True)
    def capsys(self, capsys):
        self.capsys = capsys


if __name__ == '__main__':
    unittest.main()
