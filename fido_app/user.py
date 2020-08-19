''' USER CLASS (for use with Flask-Login) '''

from flask_login import UserMixin


class User(UserMixin):
    def __init__(self, email, display_name, ukey, icon_url, credential_id, pub_key, sign_count, rp_id):
        self.email = email                  # str
        self.display_name = display_name    # str
        self.ukey = ukey                    # str
        self.icon_url = icon_url            # str
        self.credential_id = credential_id  # str
        self.pub_key = pub_key              # str
        self.sign_count = sign_count        # int
        self.rp_id = rp_id                  # str

    def __repr__(self):
        return 'User %s (Email: %s)' % (self.display_name, self.email)
