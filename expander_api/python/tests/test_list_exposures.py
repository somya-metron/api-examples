import pytest
import unittest
import responses
import requests

from python.list_exposures import get_expander_id_token, get_exposures, construct_api_params
from unittest.mock import patch, Mock


class ListExposuresTest(unittest.TestCase):
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

    def test_construct_api_params_succeeds_all_params(self):
        accept = 'application/json'
        limit = 100
        offset = 100
        exposure_type = 'a,b,c,d,e,f,g'
        inet = '192.168.1.2'
        content = 'content'
        activity_status = 'active,inactive'
        last_event_time = '2019-11-15T11:22:123Z'
        last_event_window = '2019-11-15T11:22:123Z'
        severity = 'critical'
        event_type = 'appearance,reappearance,disappearance'
        provider = 'Akamai Technologies,Amazon Web Services'
        cloud = False
        tag = '1,2,3,4,5,6,7,8,9'
        business_unit = '11,22,33,44,55,66,77,88,99'
        port_number = '8080,9090'
        sort = 'id'
        params = construct_api_params(accept, limit, offset, exposure_type, inet, content, activity_status,
                                      last_event_time, last_event_window, severity, event_type, provider, cloud,
                                      tag, business_unit, port_number, sort)
        expected = {
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

        assert params == expected

    def test_construct_api_params_succeeds_some_params(self):
        content = 'content'
        activity_status = 'active,inactive'
        last_event_time = '2019-11-15T11:22:123Z'
        last_event_window = '2019-11-15T11:22:123Z'
        severity = 'critical'
        event_type = 'appearance,reappearance,disappearance'
        params = construct_api_params(content=content,activity_status=activity_status,last_event_time=last_event_time,
                                      last_event_window=last_event_window,severity=severity,event_type=event_type)
        expected = {
            'content': content,
            'activityStatus': activity_status,
            'lastEventTime': last_event_time,
            'lastEventWindow': last_event_window,
            'severity': severity,
            'eventType': event_type
        }

        assert params == expected

    def test_construct_api_params_succeeds_no_params(self):
        params = construct_api_params()
        expected = {}

        assert params == expected

    @responses.activate
    def test_get_exposures_success(self):
        # create mock id token and responses
        mock_id_token = 'example_id_token'
        mock_exposures_response = {
            'data': [
                {
                    'id': 'exposure_id',
                }
            ],
            'pagination': {
                'next': "https://expander.expanse.co/api/v2/exposures/ip-ports?limit=100&offset=1",
                'prev': None
            },
            "meta": {
                "totalCount": 2
            }
        }

        mock_exposures_response_2 = {
            'data': [
                {
                    'id': 'exposure_id_two',
                }
            ],
            'pagination': {
                'next': None,
                'prev': "https://expander.expanse.co/api/v2/exposures/ip-ports?limit=100&offset=0"
            },
            "meta": {
                "totalCount": 2
            }
        }

        # expected results, based on mocked responses
        expected_results = [{'id': 'exposure_id'}, {'id': 'exposure_id_two'}]

        # Mocking the exposure get requests to return a response with mock response and status code 200
        responses.add(responses.GET, 'http://expander.expanse.co/api/v2/exposures/ip-ports',
                      json=mock_exposures_response, status=200)

        # We also need to mock the paginated 'next' api call.
        responses.add(responses.GET, 'https://expander.expanse.co/api/v2/exposures/ip-ports?limit=100&offset=1',
                      json=mock_exposures_response_2, status=200)

        # Call the service, which will send a request
        results = get_exposures(mock_id_token, False)

        # Capture stdout print statements
        captured = self.capsys.readouterr()

        self.assertIn('Calling v2/exposures/ip-ports endpoint...', captured.out)
        self.assertIn('Retrieved 1 Exposures on this page, total so far: 1 out of 2', captured.out)
        self.assertIn('Retrieved 1 Exposures on this page, total so far: 2 out of 2', captured.out)
        self.assertIn('Process has completed: 2 Total Exposures have been loaded', captured.out)
        self.assertIn('exposure_id', captured.out)
        self.assertEqual(results, expected_results)

    def test_get_exposures_exception(self):
        mock_get_patcher = patch('python.list_exposures.requests.get')
        mock_id_token = 'example_id_token'
        mock_exposures_response = requests.exceptions.ConnectionError()

        # Start patching 'requests.get'
        mock_get = mock_get_patcher.start()

        # Configure the mock to return a response with status code 200.
        mock_get.side_effect = mock_exposures_response

        # given API request runs into an exception, then we should exit and output exception
        with self.assertRaises(SystemExit) as actual_sys_exit:
            get_exposures(mock_id_token, False)

        # Capture stdout print statements
        captured = self.capsys.readouterr()

        # Stop patching 'requests'
        mock_get_patcher.stop()

        self.assertIn('Calling v2/exposures/ip-ports endpoint...', captured.out)
        self.assertIn('Request returned an exception:', str(actual_sys_exit.exception))

    @pytest.fixture(autouse=True)
    def capsys(self, capsys):
        self.capsys = capsys


if __name__ == '__main__':
    unittest.main()
