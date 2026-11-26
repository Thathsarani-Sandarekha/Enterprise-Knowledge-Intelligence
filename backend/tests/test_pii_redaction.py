"""Helper-level PII checks; not evidence of complete application PII protection."""
from app.services.pii_redaction import redact_log_text


def test_redacts_email_ssn_and_us_phone():
    value = 'Email jane@example.com; SSN 123-45-6789; call (415) 555-0199.'
    result = redact_log_text(value)
    for secret in ('jane@example.com', '123-45-6789', '(415) 555-0199'):
        assert secret not in result
    assert '[REDACTED_EMAIL]' in result
    assert '[REDACTED_SSN]' in result
    assert '[REDACTED_PHONE]' in result


def test_redacts_groq_api_key():
    value = 'api_key=gsk_1234567890abcdef1234567890'
    result = redact_log_text(value)
    assert 'gsk_1234567890abcdef1234567890' not in result


def test_preserves_business_terms_and_material_codes():
    value = 'UPH-FR-220 at SGR-2025 costs USD 145 per yard.'
    assert redact_log_text(value) == value
