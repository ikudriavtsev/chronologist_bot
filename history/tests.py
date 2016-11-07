from copy import deepcopy
from json import load
from unittest.mock import Mock, patch
import os
import unittest

from history import API
from history.models import Entry, Results


CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
with(open(os.path.join(CURRENT_DIR, 'fixtures', 'data.json'))) as data:
    DATA = load(data)

EVENTS_LENGTH = 3
BIRTHS_LENGTH = 4
DEATHS_LENGTH = 3
DATA_LENGTH = EVENTS_LENGTH + BIRTHS_LENGTH + DEATHS_LENGTH

with(open(os.path.join(CURRENT_DIR, 'fixtures', 'corrupted.json'))) as corrupted:
    CORRUPTED = load(corrupted)


class TestModels(unittest.TestCase):
    '''Test the models.'''

    def setUp(self):
        self.results = Results(DATA)

    def test_results_length(self):
        self.assertEqual(len(self.results), DATA_LENGTH)

    def test_results_valid(self):
        self.assertEqual('Death of Simeon I the Great, the first Bulgarian to be recognized as Emperor.',
                         self.results[0].text)

    def test_results_type(self):
        self.assertTrue(all(map(lambda entry: isinstance(entry, Entry), self.results)))

    def test_results_slice(self):
        self.assertEqual(len(self.results[-3:]), 3)

    def test_results_raises(self):
        with self.assertRaises(IndexError):
            self.results[DATA_LENGTH]

    def test_results_search(self):
        self.assertEqual(len(self.results.search('927')), 2)

    def test_results_search_valid(self):
        self.assertEqual('Death of Simeon I the Great, the first Bulgarian to be recognized as Emperor.',
                         self.results.search('927')[0].text)

    def test_results_search_type(self):
        self.assertTrue(all(map(lambda entry: isinstance(entry, Entry), self.results.search('927'))))

    def test_results_search_slice(self):
        self.assertEqual(len(self.results.search('927')[-2:]), 2)

    def test_results_search_raises(self):
        with self.assertRaises(IndexError):
            self.results.search('927')[3]

    def test_events_length(self):
        self.assertEqual(len(self.results.events), EVENTS_LENGTH)

    def test_births_length(self):
        self.assertEqual(len(self.results.births), BIRTHS_LENGTH)

    def test_deaths_length(self):
        self.assertEqual(len(self.results.deaths), DEATHS_LENGTH)

    def test_events_slice(self):
        self.assertEqual(len(self.results.events[1:3]), 2)

    def test_iter_deaths(self):
        count = 0
        for death in self.results.deaths:
            count += 1
        self.assertEqual(count, DEATHS_LENGTH)

    def test_entry_type(self):
        self.assertTrue(all(map(lambda entry: isinstance(entry, Entry), self.results.births)))

    def test_entry_type_slice(self):
        self.assertTrue(all(map(lambda entry: isinstance(entry, Entry), self.results.events[1:])))

    def test_death_text(self):
        self.assertEqual('Ordoño I of Asturias (b. 831)',
                         self.results.deaths[1].text)

    def test_link_text(self):
        self.assertEqual('Malcolm IV of Scotland', self.results.events[2].links[0].title)

    def test_search_events(self):
        self.assertEqual('Death of Simeon I the Great, the first Bulgarian to be recognized as Emperor.',
                         self.results.events.search('927')[0].text)

    def test_search_births_empty_left(self):
        self.assertEqual([], self.results.births.search('1234'))

    def test_search_births_empty_right(self):
        self.assertEqual([], self.results.births.search('1534'))

    def test_search_deaths_bc(self):
        self.assertEqual('Procopius, Roman usurper (b. 325)', self.results.deaths.search('366 BC')[0].text)

    def test_search_events_double_left(self):
        data = deepcopy(DATA)
        data['data']['Events'].insert(0, data['data']['Events'][0])
        results = Results(data)
        self.assertEqual(2, len(results.events.search(results.events[0].year)))

    def test_search_births_double_right(self):
        data = deepcopy(DATA)
        data['data']['Births'].insert(2, data['data']['Births'][2])
        results = Results(data)
        self.assertEqual(2, len(results.births.search(results.births[2].year)))

    def test_search_results_double_left(self):
        data = deepcopy(DATA)
        data['data']['Deaths'].insert(0, data['data']['Deaths'][0])
        results = Results(data)
        self.assertEqual(2, len(results.search(results.deaths[0].year)))

    def test_search_results_double_right(self):
        data = deepcopy(DATA)
        data['data']['Events'].insert(2, data['data']['Events'][2])
        results = Results(data)
        self.assertEqual(2, len(results.search(results.deaths[2].year)))

    def test_search_corrupted_data(self):
        results = Results(CORRUPTED)
        self.assertEqual(2, len(results.search('2003')))

    def test_search_data_repr(self):
        self.assertEqual('Agnes of Hesse was born in 1527 this date (died in 1555)',
                         str(self.results.search('1527')[0]))

    def test_search_data_no_death_repr(self):
        self.assertEqual('Michele Bartoli, Italian cyclist was born in 1970 this date',
                         str(self.results.search('1970')[0]))

    def test_search_corrupted_data_repr(self):
        results = Results(CORRUPTED)
        self.assertEqual('conspirators in the assassination of Abraham Lincoln – George Atzerodt died in 1865 this date'
                         ' (born in 1833) – David Herold died in 1865 this date (born in 1842) – Lewis Payne died in '
                         '1865 this date (born in 1844) – Mary Surratt died in 1865 this date (born in 1823)',
                         str(results.search('1865')[0]))

    def test_search_links_raises(self):
        with self.assertRaises(RuntimeError):
            self.results.deaths[0].links.search('foo')

    def test__to_int(self):
        self.assertEqual(1234, self.results.events._to_int('1234'))

    def test__to_int_bc(self):
        self.assertEqual(-1234, self.results.events._to_int('1234 BC'))


class TestAPI(unittest.TestCase):
    '''Test the API.'''

    def setUp(self):
        self.api = API()
        r = Mock()
        r.status_code = 200
        r.json.return_value = DATA
        patcher = patch('requests.get', return_value=r)
        patcher.start()

    def test_today_results(self):
        self.assertTrue(isinstance(self.api.today(), Results))

    def test_today_results_valid(self):
        self.assertEqual(len(self.api.today()), DATA_LENGTH)

    def test_today_results_entries(self):
        self.assertTrue(all(map(lambda entry: isinstance(entry, Entry), self.api.today())))

    def test_date_results(self):
        self.assertTrue(isinstance(self.api.date(2, 4), Results))

    def test_date_results_year(self):
        self.assertTrue(isinstance(self.api.date(2, 4, '927'), Results))

    def test_date_results_valid(self):
        self.assertEqual(len(self.api.date(2, 4)), DATA_LENGTH)

    def test_date_results_year_valid(self):
        self.assertEqual(len(self.api.date(2, 4, '927')), 2)

    def test_date_results_entries(self):
        self.assertTrue(all(map(lambda entry: isinstance(entry, Entry), self.api.date(2, 4))))

    def test_date_results_year_entries(self):
        self.assertTrue(all(map(lambda entry: isinstance(entry, Entry), self.api.date(2, 4, '927'))))

    def test_date_raises_invalid_month(self):
        with self.assertRaises(AssertionError):
            self.api.date(13, 4)

    def test_date_raises_invalid_day(self):
        with self.assertRaises(AssertionError):
            self.api.date(2, 32)

    def test_date_raises_invalid_year(self):
        with self.assertRaises(AssertionError):
            self.api.date(2, 4, '927BC')

    def test_date_raises_type_month(self):
        with self.assertRaises(TypeError):
            self.api.date('2', 4)

    def test_date_raises_type_day(self):
        with self.assertRaises(TypeError):
            self.api.date(2, '4')

    def test_date_raises_type_year(self):
            with self.assertRaises(AssertionError):
                self.api.date(2, 4, 927)

    def test_today_invalid_status_code(self):
        r = Mock()
        r.status_code = 500
        patcher = patch('requests.get', return_value=r)
        patcher.start()
        with self.assertRaises(ValueError):
            self.api.today()

    def test_date_invalid_status_code(self):
        r = Mock()
        r.status_code = 500
        patcher = patch('requests.get', return_value=r)
        patcher.start()
        with self.assertRaises(ValueError):
            self.api.date(2, 4)


if __name__ == '__main__':
    unittest.main()
