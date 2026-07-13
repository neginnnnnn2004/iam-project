from django.core.signing import TimestampSigner, SignatureExpired, BadSignature

def generate_reset_token(username):
    signer = TimestampSigner()
    token = signer.sign(username)
    return token

def verify_reset_token(token, max_age_seconds=600):
    signer = TimestampSigner()
    try:
        username = signer.unsign(token, max_age_seconds)
        return username
    except (BadSignature, SignatureExpired):
        return None