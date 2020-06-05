from ai import BotAI, Action
from app import app
from datetime import date
from google.protobuf.struct_pb2 import Struct
from unittest.mock import Mock, patch
import unittest


_parameters = Struct()
_parameters.update({
    'date': {
        'day': "1916-05-30"
    }
})
valid_response = Mock()
valid_response.action = 'history'
valid_response.parameters = _parameters

_parameters = Struct()
_parameters.update({
    'date': "battle in"
})
invalid_response = Mock()
invalid_response.action = 'history'
invalid_response.parameters = _parameters
invalid_response.fulfillment_text = "speech"

no_action = Mock()
no_action.action = None
no_action.fulfillment_text = "Hello world"


class TestAction(unittest.TestCase):
    '''Test action extraction from api.ai response'''

    def test_only_day_parsed(self):
        parameters = Struct()
        parameters.update({
            'date': {
                "day": "2017-03-20"
            }})
        r = Mock()
        r.action = 'history'
        r.parameters = parameters
        action = Action(r)
        self.assertEqual(action.date.year, 2017)
        self.assertEqual(action.date.month, 3)
        self.assertEqual(action.date.day, 20)

    @patch('ai.datetime')
    def test_exact_day_parsed(self, dt):
        today = Mock()
        today().year = 2014
        dt.today = today
        parameters = Struct()
        parameters.update({
            'date': {
                "day": "2015-03-20"
            }})
        r = Mock()
        r.action = 'history'
        r.parameters = parameters
        action = Action(r)
        self.assertEqual(action.date.year, 2015)
        self.assertEqual(action.date.month, 3)
        self.assertEqual(action.date.day, 20)

    def test_day_with_years_ago_parsed(self):
        parameters = Struct()
        parameters.update({
            'date': {
                "day": "2017-03-20",
                "years_ago": 75
            }})
        r = Mock()
        r.action = 'history'
        r.parameters = parameters
        action = Action(r)
        self.assertEqual(action.year, str(2017 - 75))
        self.assertEqual(action.date.month, 3)
        self.assertEqual(action.date.day, 20)

    def test_day_with_exact_year_parsed(self):
        parameters = Struct()
        parameters.update({
            'date': {
                "day": "2017-03-20",
                "year_exact": 1945
            }})
        r = Mock()
        r.action = 'history'
        r.parameters = parameters
        action = Action(r)
        self.assertEqual(action.year, "1945")
        self.assertEqual(action.date.month, 3)
        self.assertEqual(action.date.day, 20)

    def test_day_with_exact_year_bc_parsed(self):
        parameters = Struct()
        parameters.update({
            'date': {
                "day": "2017-03-20",
                "year_exact": 25,
                "bc": "BC"
            }})
        r = Mock()
        r.action = 'history'
        r.parameters = parameters
        action = Action(r)
        self.assertEqual(action.year, "25BC")
        self.assertEqual(action.date.month, 3)
        self.assertEqual(action.date.day, 20)

    def test_date_with_only_exact_year_parsed(self):
        parameters = Struct()
        parameters.update({
            'date': {
                "year_exact": 1910,
            }})
        r = Mock()
        r.action = 'history'
        r.parameters = parameters
        action = Action(r)
        self.assertEqual(action.year, "1910")
        self.assertEqual(action.date.month, date.today().month)
        self.assertEqual(action.date.day, date.today().day)

    def test_date_with_only_exact_ago_parsed(self):
        parameters = Struct()
        parameters.update({
            'date': {
                "years_ago": 10,
            }})
        r = Mock()
        r.action = 'history'
        r.parameters = parameters
        action = Action(r)
        self.assertEqual(action.year, str(date.today().year - 10))
        self.assertEqual(action.date.month, date.today().month)
        self.assertEqual(action.date.day, date.today().day)


class TestResponse(unittest.TestCase):
    '''Test parsing of api.ai response'''

    def when_dialogflow_returns(self, data):
        r = Mock()
        r.query_result = data
        patcher = patch('dialogflow.SessionsClient.detect_intent', return_value=r)
        patcher.start()

    def test_action_is_returned(self):
        bot = BotAI()
        self.when_dialogflow_returns(valid_response)
        with app.app_context():
            action = bot.extract_action(Mock(), "Yesterday 100 years ago?")
        self.assertEqual(action.name, 'history')

    def test_datetime_is_returned(self):
        bot = BotAI()
        self.when_dialogflow_returns(valid_response)
        with app.app_context():
            res = bot.extract_action(Mock(), "Yesterday 100 years ago?")
        self.assertEqual(res.date.year, 1916)
        self.assertEqual(res.date.month, 5)
        self.assertEqual(res.date.day, 30)

    def test_response_without_action(self):
        bot = BotAI()
        self.when_dialogflow_returns(no_action)
        with app.app_context():
            res = bot.extract_action(Mock(), "Let's drink some beer")
        self.assertIsNone(res.name)
        self.assertIsNone(res.date)
        self.assertIsNotNone(res.fulfillment)

    def test_response_invalid_action(self):
        bot = BotAI()
        self.when_dialogflow_returns(invalid_response)
        with app.app_context():
            res = bot.extract_action(Mock(), "Let's drink some beer")
        self.assertIsNone(res.name)
        self.assertIsNone(res.date)
        self.assertIsNotNone(res.fulfillment)


if __name__ == '__main__':
    unittest.main()
