from datetime import datetime
from dateutil.parser import parse
from flask import current_app
from urllib.parse import urljoin
import requests
import uuid


# api.ai session ids per user.
SESSION_IDS = {}


class Action:
    def __init__(self, data):
        self.name = data.get('action')
        self.date = None
        fulfillment = data.get('fulfillment')
        self.fulfillment = fulfillment.get('speech') if fulfillment else None
        date_param = data.get('parameters').get('date') if data.get('parameters') else None
        self.make_date(date_param) if date_param else None

    def make_date(self, params):
        self.year = None
        day = params.get('day')
        self.date = parse(day) if day else None
        years_ago = params.get('years_ago')
        year_exact = params.get('year_exact')
        if (year_exact or years_ago) and not day:
            self.date = datetime.today()
        if years_ago:
            self.year = self.date.year - years_ago if self.date else datetime.today().year - years_ago
        if year_exact:
            self.year = year_exact
        if self.date.year < datetime.today().year:
            self.year = self.date.year
        if self.year:
            self.year = ("%dBC" if params.get('bc') else "%d") % self.year


class BotAI:
    '''Wrapper for api.ai which can understand questions about history'''

    def __init__(self, token, api_url='https://api.api.ai'):
        self.api_url = api_url
        self.token = token

    def extract_action(self, recipient_id, message):
        json = self._query(recipient_id, message)
        # Check if the app context is available.
        if current_app:
            current_app.logger.debug('api.ai query: %s' % json)
        return Action(json['result'])

    def _query(self, recipient_id, message):
        url = urljoin(self.api_url,
                      'v1/query?v=20150910&query={query}&lang=en&sessionId={session_id}'
                      .format(query=message, session_id=SESSION_IDS.setdefault(recipient_id, str(uuid.uuid1()))))
        headers = {'Authorization': 'Bearer %s' % self.token}
        r = requests.get(url, headers=headers)
        if r.status_code == requests.codes.ok:
            return r.json()
        raise ValueError('Got invalid status code {status_code} when trying to access the endpoint {endpoint} with json \
            response {response}'.format(endpoint=url, response=r.json(), status_code=r.status_code))
