import pytest
import unittest
import responses
import requests

from python.list_on_prem_assets import get_expander_id_token, get_assets, construct_api_params
from unittest.mock import patch, Mock


class ListAssetsTest(unittest.TestCase):
    def test_get_expander_id_token_success(self):
        mock_get_patcher = patch('python.list_on_prem_assets.requests.get')
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
        mock_get_patcher = patch('python.list_on_prem_assets.requests.get')
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
        mock_get_patcher = patch('python.list_on_prem_assets.requests.get')
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

    def test_construct_api_params_succeeds_all_params(self):
        limit = 100
        offset = 100
        sort = 'id'
        business_units = 'a,b,c,d,e'
        business_unit_names = 'asdf,bnm,cvbn,dfgh,erty'
        inet = '192.168.1.2'
        tags = '1,2,3,4,5'
        tag_names = '1234,2345,3456,4567,5678'
        include = 'severityCounts,attributionReasons'
        params = construct_api_params(limit,offset, sort, business_units, business_unit_names,
                                      inet, tags, tag_names, include)
        expected = {
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

        assert params == expected

    def test_construct_api_params_succeeds_some_params(self):
        business_units = 'a,b,c,d,e'
        business_unit_names = 'asdf,bnm,cvbn,dfgh,erty'
        inet = '192.168.1.2'
        tags = '1,2,3,4,5'
        params = construct_api_params(business_units=business_units, business_unit_names=business_unit_names,
                                      inet=inet, tags=tags)
        expected = {
            'business-units': business_units,
            'business-unit-names': business_unit_names,
            'inet': inet,
            'tags': tags
        }

        assert params == expected

    def test_construct_api_params_succeeds_no_params(self):
        params = construct_api_params()
        expected = {}

        assert params == expected

    @responses.activate
    def test_get_assets_success(self):
        # create mock id token and responses
        mock_id_token = 'example_id_token'
        mock_assets_response = {
            'data': [
                {
                    'id': 'asset_id',
                }
            ],
            'pagination': {
                'next': "http://expander.expanse.co/api/v2/ip-range?limit=100&offset=100",
                'prev': None
            },
            'meta': {
                'totalCount': 2,
            }
        }

        mock_assets_response_2 = {
            'data': [
                {
                    'id': 'asset_id_two',
                }
            ],
            'pagination': {
                'next': None,
                'prev': "http://expander.expanse.co/api/v2/ip-range?limit=100&offset=0",
            },
            'meta': {
                'totalCount': 2,
            }
        }

        # expected results, based on mocked responses
        expected_results = [{'id': 'asset_id'}, {'id': 'asset_id_two'}]

        # Mocking the paginated 'next' api call.
        responses.add(
            responses.GET, 'http://expander.expanse.co/api/v2/ip-range?limit=100&offset=100',
            json=mock_assets_response_2, status=200)

        # Mocking the asset get requests to return a response with mock response and status code 200
        responses.add(
            responses.GET, 'http://expander.expanse.co/api/v2/ip-range',
            json=mock_assets_response, status=200)

        # Call the service, which will send a request
        results = get_assets(mock_id_token, False)

        # Capture stdout print statements
        captured = self.capsys.readouterr()

        self.assertIn('Calling http://expander.expanse.co/api/v2/ip-range endpoint...', captured.out)
        self.assertIn('Retrieved 1 Assets on this page, total so far: 1 out of 2', captured.out)
        self.assertIn('Retrieved 1 Assets on this page, total so far: 2 out of 2', captured.out)
        self.assertNotIn('Retrieved 1 Assets on this page, total so far: 3 out of 2', captured.out)
        self.assertIn('asset_id', captured.out)
        self.assertEqual(results, expected_results)

    def test_get_assets_exception(self):
        mock_get_patcher = patch('python.list_on_prem_assets.requests.get')
        mock_id_token = 'example_id_token'
        mock_assets_response = requests.exceptions.ConnectionError()

        # Start patching 'requests.get'
        mock_get = mock_get_patcher.start()

        # Configure the mock to return a response with status code 200.
        mock_get.side_effect = mock_assets_response

        # given API request runs into an exception, then we should exit and output exception
        with self.assertRaises(SystemExit) as actual_sys_exit:
            get_assets(mock_id_token, False)

        # Capture stdout print statements
        captured = self.capsys.readouterr()

        # Stop patching 'requests'
        mock_get_patcher.stop()

        self.assertIn('Calling http://expander.expanse.co/api/v2/ip-range endpoint...', captured.out)
        self.assertIn('Request returned an exception:', str(actual_sys_exit.exception))

    @pytest.fixture(autouse=True)
    def capsys(self, capsys):
        self.capsys = capsys


if __name__ == '__main__':
    unittest.main()
