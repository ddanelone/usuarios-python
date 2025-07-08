# tests/test_core/test_security.py
from datetime import timedelta, datetime
from time import sleep
from app.core import security
from app.core.config import settings
from jose import jwt

def test_get_password_hash_and_verify_password():
    password = "MySecret123"
    hashed = security.get_password_hash(password)
    assert hashed != password
    assert security.verify_password(password, hashed)
    assert not security.verify_password("WrongPass", hashed)

def test_create_and_decode_access_token():
    data = {"sub": "test@example.com"}
    token = security.create_access_token(data)
    decoded = security.decode_access_token(token)
    assert decoded is not None
    assert decoded.get("sub") == data["sub"]
    assert "exp" in decoded

def test_create_access_token_custom_expiry():
    data = {"sub": "test@example.com"}
    token = security.create_access_token(data, expires_delta=timedelta(seconds=1))
    decoded = security.decode_access_token(token)
    assert decoded is not None
    sleep(2)
    decoded_expired = security.decode_access_token(token)
    assert decoded_expired is None

def test_decode_access_token_invalid_token():
    invalid_token = "this.is.not.a.token"
    decoded = security.decode_access_token(invalid_token)
    assert decoded is None

def test_create_and_verify_password_reset_token():
    email = "reset@example.com"
    token = security.create_password_reset_token(email, expires_minutes=1)
    decoded_email = security.verify_password_reset_token(token)
    assert decoded_email == email

def test_verify_password_reset_token_wrong_scope():
    # Create token with wrong scope
    payload = {
        "sub": "someone@example.com",
        "exp": datetime.utcnow().timestamp() + 60,
        "scope": "wrong_scope"
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    result = security.verify_password_reset_token(token)
    assert result is None

def test_verify_password_reset_token_expired():
    token = security.create_password_reset_token("someone@example.com", expires_minutes=-1)
    result = security.verify_password_reset_token(token)
    assert result is None