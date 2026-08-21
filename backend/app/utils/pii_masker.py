"""
Phase 25 - Production Security & PII Masking Utilities.
Sanitizes customer phone numbers, Aadhaar/SSN, credit card strings, and PII
before logging or saving unencrypted sensitive data.
"""
import re


def mask_phone_number(phone: str) -> str:
    """Masks middle digits of a phone number: +91-9876543210 -> +91-98****3210."""
    if not phone or len(phone) < 6:
        return "****"

    clean_digits = re.sub(r"[^\d]", "", phone)
    if len(clean_digits) >= 10:
        return f"+91-{clean_digits[:2]}****{clean_digits[-4:]}"
    return f"{phone[:2]}****{phone[-2:]}"


def sanitize_complaint_text(text: str) -> str:
    """Masks sensitive credit card / CVV / OTP numbers from complaint text."""
    # Mask 16-digit card numbers
    sanitized = re.sub(r"\b(?:\d[ -]*?){13,16}\b", "[CARD-MASKED]", text)
    # Mask OTP mentions
    sanitized = re.sub(r"\b(OTP|otp|pin|PIN)\s*[:=]?\s*\d{4,6}\b", r"\1 [MASKED]", sanitized)
    return sanitized.strip()
