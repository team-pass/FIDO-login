import re
from datetime import date

''' Contains useful utility functions for our Flask app '''
def get_database_uri_from(env):
    '''
    Use values from the environment to determine a Database URI per the SQLAlchemy schema.
    See https://docs.sqlalchemy.org/en/14/core/engines.html#database-urls for specifics.
    '''

    # SQLite URLs use a local file on disk with no login info
    if env["DB_PROTOCOL"] == 'sqlite':
        return f'sqlite:///{env["DB_NAME"]}'
    
    return f'{env["DB_PROTOCOL"]}://{env["DB_USERNAME"]}:{env["DB_PASSWORD"]}@{env["DB_HOST"]}/{env["DB_NAME"]}'

def validate_email(email):
    '''
    Returns True if email is a properly formatted email address;
    returns False otherwise.
    '''
    return (
        isinstance(email, str)
        and re.search(r'^([a-z0-9]+[\._]?)*[a-z0-9]+@\w+\.\w+$', email) is not None
    )


def get_display_name(email):
    '''Returns the first part of an email as a display name'''
    return email[: email.index('@')]


def get_elapsed_days(startDate, endDate=date.today()):
    '''
    Returns the number of days between the provided start and end dates.
    Defaults to returning the number of days between the start date and today.
    '''
    return (endDate - startDate).days


def append_to_login_bitfield(bitfield, days_since_last_login):
    '''
    Insert (`days_since_last_login` - 1) deactivated bits to the front (most significant) end
    of the existing `bitfield` integer. Insert one activated bit to the very front.
    Returns the updated `bitfield` integer.
    '''
    if days_since_last_login <= 0:
        return bitfield
    
    return bitfield + (1 << (bitfield.bit_length() + days_since_last_login - 1))


def get_credit(login_bitfield):
    '''
    Returns a float representing the amount of monetary credit earned from the given
    series of user logins. Effectively just counts the number of 1s in the integer.
    '''
    return 1.0 * bin(login_bitfield).count('1')
