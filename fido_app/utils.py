import os, sys, re
from flask import url_for, flash, make_response, jsonify

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

def get_json_error_redirect(error, redirect_url, status_code):
    '''Returns a JSON response object for a bad request that redirects the user to a given URL'''
    flash(error, 'error')
    return make_response(jsonify({'redirect': redirect_url, 'error': error}), status_code)


def get_json_success_redirect(message, redirect_url, status_code):
    '''Returns a JSON response object for a successful request that redirects the user to a given URL'''
    flash(message)
    return make_response(jsonify({'redirect': redirect_url, 'message': message}), status_code)