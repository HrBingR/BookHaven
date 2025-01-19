from config.config import config
import jwt

def verify_token(token):
    try:
        return jwt.decode(token, config.SECRET_KEY, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return None