"""Unit tests for PII sanitization."""

from yourosint.contexts.privacy.application.mask_pii import PersonalDataSanitizer


def test_pii_sanitizer_removes_sensitive_data():
    sanitizer = PersonalDataSanitizer()
    text = "User passport: 4509 123456 and phone +79991234567"
    res = sanitizer.sanitize(text)
    assert res.has_pii is True
    assert "[PASSPORT MASKED]" in res.sanitized_text
    assert "[PHONE MASKED]" in res.sanitized_text
