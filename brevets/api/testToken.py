from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature,
                          SignatureExpired)


def generate_auth_token(key, expiration=600):
    s = Serializer(key, expires_in=expiration)
    return s.dumps({'party': 'started'})


def verify_auth_token(key, token):
    s = Serializer(key)
    try:
        data = s.loads(token)
    except SignatureExpired:
        return False    # valid token, but expired
    except BadSignature:
        return False    # invalid token
    return True
