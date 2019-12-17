from datetime import datetime, timedelta

import pytest
import unittest
import responses
import requests

from python.list_events import get_expander_id_token, get_events, check_date_params, construct_api_params
from unittest.mock import patch, Mock


class ListEventsTest(unittest.TestCase):
    def test_get_expander_id_token_success(self):
        mock_get_patcher = patch('python.list_events.requests.get')
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
        mock_get_patcher = patch('python.list_events.requests.get')
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
        mock_get_patcher = patch('python.list_events.requests.get')
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

    def test_check_date_params_succeeds(self):
        start_date = datetime.today() - timedelta(days=5)
        end_date = datetime.today() - timedelta(days=2)
        check_date_params(str(start_date.date()), str(end_date.date()))

    def test_check_date_params_fails_later_start_date(self):
        start_date = datetime.today() - timedelta(days=2)
        end_date = datetime.today() - timedelta(days=5)

        with self.assertRaises(SystemExit) as sys_exit:
            check_date_params(str(start_date.date()), str(end_date.date()))

        self.assertIn('end_date must be the same as or later than start_date', str(sys_exit.exception))

    def test_check_date_params_fails_end_date_today(self):
        start_date = datetime.today()
        end_date = datetime.today()

        with self.assertRaises(SystemExit) as sys_exit:
            check_date_params(str(start_date.date()), str(end_date.date()))

        self.assertIn('end_date must be earlier than today', str(sys_exit.exception))

    def test_construct_api_params_succeeds_all_params(self):
        business_unit = "1,2,3,4,5,6,7,8,9"
        event_type = "ON_PREM_EXPOSURE_APPEARANCE,CLOUD_EXPOSURE_REAPPEARANCE"
        limit = 123
        page_token = "page_token"
        params = construct_api_params(business_unit, event_type, limit, page_token)
        expected = {
            'businessUnit': business_unit,
            'eventType': event_type,
            'limit': limit,
            'pageToken': page_token
        }

        assert params == expected

    def test_construct_api_params_succeeds_some_params(self):
        business_unit = "1,2,3,4,5,6,7,8,9"
        limit = 123
        params = construct_api_params(business_unit=business_unit, limit=limit)
        expected = {
            'businessUnit': business_unit,
            'limit': limit
        }

        assert params == expected

    def test_construct_api_params_succeeds_no_params(self):
        params = construct_api_params()
        expected = {}

        assert params == expected

    @responses.activate
    def test_get_events_success(self):
        # create mock id token and responses
        mock_id_token = 'example_id_token'
        mock_events_response = {
            'data': [
                {
                    'id': 'event_id',
                }
            ],
            'pagination': {
                'next': "https://expander.expanse.co/api/v1/events"
                        "?startDateUtc=2019-12-01&endDateUtc=2019-12-01&limit=100&offset=100",
                'prev': None
            }
        }

        mock_events_response_2 = {
            'data': [
                {
                    'id': 'event_id_two',
                }
            ],
            'pagination': {
                'next': None,
                'prev': "https://expander.expanse.co/api/v1/events"
                        "?startDateUtc=2019-12-01&endDateUtc=2019-12-01&limit=100&offset=0",
            }
        }

        # expected results, based on mocked responses
        expected_results = [{'id': 'event_id'}, {'id': 'event_id_two'}]

        # Mocking the event get requests to return a response with mock response and status code 200
        responses.add(
            responses.GET, 'http://expander.expanse.co/api/v1/events?startDateUtc=2019-12-01&endDateUtc=2019-12-01',
            json=mock_events_response, status=200)

        # We also need to mock the paginated 'next' api call.
        responses.add(
            responses.GET, 'https://expander.expanse.co/api/v1/events'
                           '?startDateUtc=2019-12-01&endDateUtc=2019-12-01&limit=100&offset=100',
            json=mock_events_response_2, status=200)

        # Call the service, which will send a request
        results = get_events(mock_id_token, '2019-12-01', '2019-12-01', False)

        # Capture stdout print statements
        captured = self.capsys.readouterr()

        self.assertIn('Calling http://expander.expanse.co/api/v1/events endpoint...', captured.out)
        self.assertIn('Retrieved 1 Events on this page, total so far: 1', captured.out)
        self.assertIn('event_id', captured.out)
        self.assertEqual(results, expected_results)

    def test_get_events_exception(self):
        mock_get_patcher = patch('python.list_events.requests.get')
        mock_id_token = 'example_id_token'
        mock_events_response = requests.exceptions.ConnectionError()

        # Start patching 'requests.get'
        mock_get = mock_get_patcher.start()

        # Configure the mock to return a response with status code 200.
        mock_get.side_effect = mock_events_response

        # given API request runs into an exception, then we should exit and output exception
        with self.assertRaises(SystemExit) as actual_sys_exit:
            get_events(mock_id_token, '2019-12-01', '2019-12-01', False)

        # Capture stdout print statements
        captured = self.capsys.readouterr()

        # Stop patching 'requests'
        mock_get_patcher.stop()

        self.assertIn('Calling http://expander.expanse.co/api/v1/events endpoint...', captured.out)
        self.assertIn('Request returned an exception:', str(actual_sys_exit.exception))

    @pytest.fixture(autouse=True)
    def capsys(self, capsys):
        self.capsys = capsys


if __name__ == '__main__':
    unittest.main()
