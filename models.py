from flask_login import UserMixin
import json
import os

USER_DB_FILE = 'users.json'

class User(UserMixin):
    def __init__(self, id, username, x_token=None, x_token_secret=None):
        self.id = id
        self.username = username
        self.x_token = x_token
        self.x_token_secret = x_token_secret

    @staticmethod
    def get(user_id):
        if os.path.exists(USER_DB_FILE):
            with open(USER_DB_FILE, 'r') as f:
                users = json.load(f)
                user_data = users.get(str(user_id))
                if user_data:
                    return User(
                        id=user_id,
                        username=user_data['username'],
                        x_token=user_data.get('x_token'),
                        x_token_secret=user_data.get('x_token_secret')
                    )
        return None

    def save(self):
        users = {}
        if os.path.exists(USER_DB_FILE):
            with open(USER_DB_FILE, 'r') as f:
                users = json.load(f)
        
        users[str(self.id)] = {
            'username': self.username,
            'x_token': self.x_token,
            'x_token_secret': self.x_token_secret
        }
        
        with open(USER_DB_FILE, 'w') as f:
            json.dump(users, f)

    @staticmethod
    def get_by_username(username):
        if os.path.exists(USER_DB_FILE):
            with open(USER_DB_FILE, 'r') as f:
                users = json.load(f)
                for user_id, user_data in users.items():
                    if user_data['username'] == username:
                        return User(
                            id=user_id,
                            username=user_data['username'],
                            x_token=user_data.get('x_token'),
                            x_token_secret=user_data.get('x_token_secret')
                        )
        return None
