'''WSGI Entrypoint (RUN THIS TO START BACKEND CODE)'''
import os, logging
from dotenv import load_dotenv
from fido_app import app

load_dotenv()

if __name__ == '__main__':
    # Run the app in debug mode
    # The SSL context is needed because creating biometric credentials requires HTTPS :)
    app.run(host=os.environ['RP_ID'], ssl_context='adhoc')
else:
    # Wire Flask logs to gunicorn
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
