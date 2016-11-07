from history.models import Results
from history.utils import year_to_int

from urllib.parse import urljoin
import requests


class API:
    '''Simple wrapper around http://history.muffinlabs.com/.'''

    def __init__(self, base_url='http://history.muffinlabs.com'):
        self.base_url = base_url

    def today(self):
        '''Get the todays events.'''
        endpoint = urljoin(self.base_url, 'date')
        return self._fetch(endpoint)

    def date(self, month, day, year=None):
        '''Get the events for the specific date.'''
        assert 1 <= month <= 12
        assert 1 <= day <= 31
        endpoint = urljoin(self.base_url, 'date/{month}/{day}'.format(month=month, day=day))
        if year is not None:
            assert isinstance(year, str)
            assert isinstance(year_to_int(year), int)
            return self._fetch(endpoint).search(year)
        return self._fetch(endpoint)

    def _fetch(self, endpoint):
        '''Helper method to communicate with the data provider.'''
        r = requests.get(endpoint)
        if r.status_code == requests.codes.ok:
            return Results(r.json())
        raise ValueError('Got invalid status code {status_code} when trying to access the endpoint {endpoint}'
                         .format(endpoint=endpoint, status_code=r.status_code))
