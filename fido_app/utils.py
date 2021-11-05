import os, sys, re

''' Contains useful utility functions for our Flask app '''


def ensure_environ_vars(required_vars):
    '''
    Throws an error if any variable in the provided list isn't 
    present in the environment. Does nothing otherwise.
    '''
    missing_fields = list(filter(lambda var: os.getenv(var) == None, required_vars))

    # If there are any missing fields, create a useful error message
    if len(missing_fields) > 0:
        missing_field_str = ''

        for field in missing_fields:
            missing_field_str += f'\n\t- {field}'

        raise EnvironmentError(
            f'Missing the following required environment variables: {missing_field_str}\nTo configure them in one place, use a `.env` file (see https://github.com/team-pass/FIDO-login/blob/master/CONTRIBUTING.md)'
        )


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
