import os

''' Contains useful utility functions for our Flask app '''


def ensure_environ_vars(required_vars):
    '''
    Throws an error if any variable in the provided list isn't 
    present in the environment. Does nothing otherwise.
    '''
    missing_fields = filter(lambda var: os.getenv(var) == None, required_vars)
    num_missing_fields = len(list(missing_fields))

    # If there are any missing fields, create a useful error message
    if num_missing_fields > 0:
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
