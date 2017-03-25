from unittest.mock import Mock, patch
from ai import BotAI, Action
from datetime import date
import unittest
from json import loads


valid_response = """{
    "id": "c22bb38a-52d2-4b6f-adb8-a55055e8f106",
    "result": {
        "action": "history",
        "actionIncomplete": false,
        "contexts": [],
        "parameters": {
             "date": {
                "day": "1916-05-30"
             }
        },
        "resolvedQuery": "Yesterday 100 years ago?",
        "score": 1.0,
        "source": "agent"
    },
    "status": {
        "code": 200,
        "errorType": "success"
    },
    "timestamp": "2016-05-30T20:30:37.258Z"
}"""

invalid_response = """{
    "id": "cd3573f7-d576-4593-b482-f6c948925512",
    "timestamp": "2017-03-25T10:11:24.669Z",
    "lang": "en",
    "result": {
        "source": "agent",
        "resolvedQuery": "Why at rhe battle in the 1510 the Spanish wins?",
        "action": "history",
        "actionIncomplete": false,
        "parameters": {
            "date": "battle in"
        },
        "contexts": [],
        "metadata": {
            "intentId": "e1b89aa6-1d3e-4004-ab3f-96aad93445b1",
            "webhookUsed": "false",
            "webhookForSlotFillingUsed": "false",
            "intentName": "history"
        },
        "fulfillment": {
            "speech": ""
        },
        "score": 1
    },
    "status": {
        "code": 200,
        "errorType": "success"
    },
    "sessionId": "12f2cb24-ebb4-4506-acdb-eebc4c2bcd79"
}"""

no_action = """{
    "id": "fc38998b-0987-4969-83b1-525f6001f0b4",
    "result": {
        "contexts": [],
        "fulfillment": {
            "speech": "Hello world"
        },
        "metadata": {},
        "resolvedQuery": "Let's drink some beer?",
        "score": 0.0,
        "source": "agent"
    },
    "status": {
        "code": 200,
        "errorType": "success"
    },
    "timestamp": "2016-05-30T20:36:19.428Z"
}"""


class TestAction(unittest.TestCase):
    '''Test action extraction from api.ai response'''

    def test_only_day_parsed(self):
        action = Action({'action': 'history', 'parameters': {
            'date': {
                "day": "2017-03-20"
            }}})
        self.assertEqual(action.date.year, 2017)
        self.assertEqual(action.date.month, 3)
        self.assertEqual(action.date.day, 20)

    @patch('ai.datetime')
    def test_exact_day_parsed(self, dt):
        today = Mock()
        today().year = 2014
        dt.today = today
        action = Action({'action': 'history', 'parameters': {
            'date': {
                "day": "2015-03-20"
            }}})
        self.assertEqual(action.date.year, 2015)
        self.assertEqual(action.date.month, 3)
        self.assertEqual(action.date.day, 20)

    def test_day_with_years_ago_parsed(self):
        action = Action({'action': 'history', 'parameters': {
            'date': {
                "day": "2017-03-20",
                "years_ago": 75
            }}})
        self.assertEqual(action.year, str(2017 - 75))
        self.assertEqual(action.date.month, 3)
        self.assertEqual(action.date.day, 20)

    def test_day_with_exact_year_parsed(self):
        action = Action({'action': 'history', 'parameters': {
            'date': {
                "day": "2017-03-20",
                "year_exact": 1945
            }}})
        self.assertEqual(action.year, "1945")
        self.assertEqual(action.date.month, 3)
        self.assertEqual(action.date.day, 20)

    def test_day_with_exact_year_bc_parsed(self):
        action = Action({'action': 'history', 'parameters': {
            'date': {
                "day": "2017-03-20",
                "year_exact": 25,
                "bc": "BC"
            }}})
        self.assertEqual(action.year, "25BC")
        self.assertEqual(action.date.month, 3)
        self.assertEqual(action.date.day, 20)

    def test_date_with_only_exact_year_parsed(self):
        action = Action({'action': 'history', 'parameters': {
            'date': {
                "year_exact": 1910,
            }}})
        self.assertEqual(action.year, "1910")
        self.assertEqual(action.date.month, date.today().month)
        self.assertEqual(action.date.day, date.today().day)

    def test_date_with_only_exact_ago_parsed(self):
        action = Action({'action': 'history', 'parameters': {
            'date': {
                "years_ago": 10,
            }}})
        self.assertEqual(action.year, str(date.today().year - 10))
        self.assertEqual(action.date.month, date.today().month)
        self.assertEqual(action.date.day, date.today().day)


class TestResponse(unittest.TestCase):
    '''Test parsing of api.ai response'''

    def when_get_returns(self, data):
        r = Mock()
        r.status_code = 200
        r.json.return_value = data
        patcher = patch('requests.get', return_value=r)
        patcher.start()

    def test_action_is_returned(self):
        bot = BotAI('TOKEN')
        self.when_get_returns(loads(valid_response))
        action = bot.extract_action(Mock(), "Yesterday 100 years ago?")
        self.assertEqual(action.name, 'history')

    def test_datetime_is_returned(self):
        bot = BotAI('TOKEN')
        self.when_get_returns(loads(valid_response))
        res = bot.extract_action(Mock(), "Yesterday 100 years ago?")
        self.assertEqual(res.date.year, 1916)
        self.assertEqual(res.date.month, 5)
        self.assertEqual(res.date.day, 30)

    def test_response_without_action(self):
        bot = BotAI('TOKEN')
        self.when_get_returns(loads(no_action))
        res = bot.extract_action(Mock(), "Let's drink some beer")
        self.assertIsNone(res.name)
        self.assertIsNone(res.date)
        self.assertIsNotNone(res.fulfillment)

    def test_response_invalid_action(self):
        bot = BotAI('TOKEN')
        self.when_get_returns(loads(invalid_response))
        res = bot.extract_action(Mock(), "Let's drink some beer")
        self.assertEqual(res.name, 'history')
        self.assertIsNone(res.date)
        self.assertIsNotNone(res.fulfillment)


if __name__ == '__main__':
    unittest.main()
