# tests/test_core/test_config.py
from app.core import config
from datetime import timedelta

def test_settings_lockout_duration():
    s = config.settings
    assert isinstance(s.lockout_duration, timedelta)
    assert s.lockout_duration.total_seconds() == s.LOCKOUT_TIME
