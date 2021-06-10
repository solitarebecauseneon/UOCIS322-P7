from itsdangerous import (TimedJSONWebSignatureSerializer \
                              as Serializer, BadSignature, \
                          SignatureExpired)
import time

SECRET_KEY = 'test1234@#$'


def generate_auth_token(expiration=600):
    s = Serializer(SECRET_KEY, expires_in=expiration)
    print(f"Token:{s.dumps({'id': 5, 'name': 'Ryan'})}")
    return s.dumps({'id': 5, 'name': 'Ryan'})


def verify_auth_token(token):
    s = Serializer(SECRET_KEY)
    try:
        data = s.loads(token)
    except SignatureExpired:
        return "Expired token!"  # valid token, but expired
    except BadSignature:
        return "Invalid token!"  # invalid token
    return f"Success! Welcome!"


if __name__ == "__main__":
    t = generate_auth_token(10)
    for i in range(1, 20):
        print(verify_auth_token(t))
        time.sleep(1)

    print(verify_auth_token("somerandomstring"))
