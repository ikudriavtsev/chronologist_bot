import re


YEAR_REGEXP = re.compile('(\s\([bd]{1}\.\s(\w*?)\))')
SANITIZE_REGEXP = re.compile('\s+')


def year_to_int(value):
    '''Converts a year string to an integer, uses negative numbers in case of BC.'''
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return -int(value.split()[0])
    except ValueError:
        pass


def event_template(year, text):
    '''Formats the event representation.'''
    text = SANITIZE_REGEXP.sub(' ', text)
    message = 'Year {year}: {text}'.format(year=year, text=text)
    return add_ellipsis(message, 320)


def birth_template(year, text):
    '''Formats the birth entry representation.'''
    text = SANITIZE_REGEXP.sub(' ', text)
    if YEAR_REGEXP.search(text):
        message = YEAR_REGEXP.sub(r' was born in {year} this date (died in \2)'.format(year=year), text).strip()
    else:
        message = '{text} was born in {year} this date'.format(text=text, year=year).strip()
    return add_ellipsis(message, 320)


def death_template(year, text):
    '''Formats the death entry representation.'''
    text = SANITIZE_REGEXP.sub(' ', text)
    message = YEAR_REGEXP.sub(r' died in {year} this date (born in \2)'.format(year=year), text).strip()
    return add_ellipsis(message, 320)


def add_ellipsis(text, limit):
    return '{text}...'.format(text=text[:limit - 3]) if len(text) > limit else text
