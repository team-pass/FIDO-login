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


def get_first_result(dbcursor):
    '''
    Returns the first result from the stored procedure that was just called, 
    or None if there were no results.
    '''
    results = list(dbcursor.stored_results())

    if len(results) == 0:
        return None

    first_result = results[0].fetchone()

    return first_result


def validate_email(email):
    '''
    Returns True if email is a properly formatted email address;
    returns False otherwise.
    '''    
    return isinstance(email, str) and re.search('^([a-z0-9]+[\._]?)*[a-z0-9]+@\w+\.\w+$', email) is not None


def validate_display_name(name):
    '''
    Returns True if name is a properly formatted display name,
    which at the moment means name contains at least one word character;
    returns False otherwise.
    '''
    return isinstance(name, str) and re.search('\w') is not None


def log(msg, sep='#', file_out=sys.stderr):
    '''
    Print message with timestamp to file (stderr by default);
    includes a sep argument to help distinguish log messages in the console.
    '''
    print('%s\n(%s) %s\n%s' % (sep * 64, time.ctime(), msg, sep * 64), file=file_out)
