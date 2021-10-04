import re

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
