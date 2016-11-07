from bisect import bisect_left
from functools import partial

from history.utils import birth_template, death_template, event_template, year_to_int


class Container(tuple):
    '''Container class for the entries from http://history.muffinlabs.com/.'''

    def __new__(cls, data, wrapper, key=None, key_converter=None):
        assert bool(key) == bool(key_converter), \
            'Both `key` and `key_converter` have to be either set or unset'
        if key is not None:
            # Sanitize the data so that it is searchable.
            data = filter(lambda entry: key in entry and key_converter(entry[key]), data)
        return super(Container, cls).__new__(cls, tuple(data))

    def __init__(self, data, wrapper, key=None, key_converter=None):
        self.wrapper = wrapper
        self.key = key
        self.key_converter = key_converter
        if self.key is not None:
            self._keys = [self._to_int(getattr(entry, self.key)) for entry in self]

    def search(self, term):
        if self.key is not None:
            _term = self._to_int(term)
            i = 0
            r = []
            while i < len(self):
                i += bisect_left(self._keys[i:], _term)
                if i < len(self):
                    key = getattr(self[i], self.key)
                else:
                    return r
                if key == term:
                    r.append(self[i])
                else:
                    return r
                i += 1
            return r
        raise RuntimeError('Cannot perform the bisection - the key was not set')

    def _to_int(self, value):
        return self.key_converter(value)

    def __getitem__(self, key):
        if isinstance(key, slice):
            return [self[i] for i in range(*key.indices(len(self)))]
        return self.wrapper(super(Container, self).__getitem__(key))

    def __iter__(self):
        for item in super(Container, self).__iter__():
            yield self.wrapper(item)


class Results:
    '''Data structure that represents the results from http://history.muffinlabs.com/.'''

    def __init__(self, data, events=None, births=None, deaths=None):
        self._raw = data
        self.date = data['date']
        self.url = data['url']
        events_wrapper = partial(Entry, template=event_template)
        births_wrapper = partial(Entry, template=birth_template)
        deaths_wrapper = partial(Entry, template=death_template)
        self.events = Container(data['data']['Events'], events_wrapper, 'year', year_to_int) if events is None else \
            events
        self.births = Container(data['data']['Births'], births_wrapper, 'year', year_to_int) if births is None else \
            births
        self.deaths = Container(data['data']['Deaths'], deaths_wrapper, 'year', year_to_int) if deaths is None else \
            deaths

    def search(self, term):
        return Results(self._raw, self.events.search(term), self.births.search(term), self.deaths.search(term))

    def __iter__(self):
        for event in self.events:
            yield event
        for birth in self.births:
            yield birth
        for death in self.deaths:
            yield death

    def __getitem__(self, key):
        if isinstance(key, slice):
            return [self[i] for i in range(*key.indices(len(self)))]
        items = ('events', 'births', 'deaths')
        if key < 0:
            items = items[-1::-1]
            key *= -1
        for item in items:
            try:
                return getattr(self, item)[key]
            except IndexError:
                key -= len(getattr(self, item))
        raise IndexError('Results index is out of range')

    def __len__(self):
        return len(self.events) + len(self.births) + len(self.deaths)


class Entry:
    '''Data structure that represents a standalone entry - an event, a birth or a death.'''

    def __init__(self, entry, template):
        self.year = entry['year']
        self.text = entry['text']
        self.template = template
        self.links = Container(entry['links'], Link)

    def __str__(self):
        return self.template(self.year, self.text)

    def __repr__(self):
        return self.__str__()


class Link:
    '''Data structure that represents a link.'''

    def __init__(self, link):
        self.title = link['title']
        self.link = link['link']
