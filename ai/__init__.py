from datetime import datetime
from dateutil.parser import parse
from flask import current_app
from google.api_core.exceptions import InvalidArgument
from google.protobuf.struct_pb2 import Struct
from google.protobuf import json_format
import dialogflow
import uuid

# api.ai session ids per user.
SESSION_IDS = {}


class Action:
    def __init__(self, query_result):
        self.name = query_result.action
        self.date = None
        fulfillment = query_result.fulfillment_text
        self.fulfillment = fulfillment if fulfillment else None
        if self.name == 'history':
            date_param = query_result.parameters['date'] if 'date' in query_result.parameters else None
            # `date_param` should be a `Struct` of parsed date parameters.
            if date_param and isinstance(date_param, Struct):
                self.make_date(json_format.MessageToDict(date_param))
            elif date_param and current_app:
                self.name = None
                current_app.logger.error('The date parameters were parsed incorrectly: %s' % date_param)

    def make_date(self, params):
        self.year = None
        day = params.get('day')
        self.date = parse(day) if day else None
        years_ago = params.get('years_ago')
        year_exact = params.get('year_exact')
        if (year_exact or years_ago) and not day:
            self.date = datetime.today()
        if years_ago:
            self.year = self.date.year - years_ago
        if year_exact:
            self.year = year_exact
        if self.date.year < datetime.today().year and not year_exact and not years_ago:
            self.year = self.date.year
        if self.year:
            self.year = ("%dBC" if params.get('bc') else "%d") % self.year


class BotAI:
    '''Wrapper for api.ai which can understand questions about history'''

    def extract_action(self, recipient_id, message):
        query_result = self._query(recipient_id, message)
        # Check if the app context is available.
        if current_app:
            current_app.logger.debug('Dialogflow query: %s' % query_result)
        return Action(query_result.query_result)

    def _query(self, recipient_id, message):
        session_client = dialogflow.SessionsClient()
        session = session_client.session_path(
            current_app.config['DIALOGFLOW_PROJECT_ID'], SESSION_IDS.setdefault(recipient_id, str(uuid.uuid1())))
        text_input = dialogflow.types.TextInput(
            text=message, language_code=current_app.config['DIALOGFLOW_LANGUAGE_CODE'])
        query_input = dialogflow.types.QueryInput(text=text_input)
        try:
            return session_client.detect_intent(session=session, query_input=query_input)
        except InvalidArgument:
            raise
