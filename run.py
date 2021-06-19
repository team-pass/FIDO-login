'''RUN THIS TO START BACKEND CODE'''
import os
from dotenv import load_dotenv
from fido_app import app

load_dotenv()

if __name__ == '__main__':
    # SSL context is needed because creating biometric credentials requires HTTPS :)
    app.run(host=os.environ['RP_ID'], debug=True, ssl_context='adhoc')
