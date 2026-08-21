"""Unit tests for Confidence value object."""

from decimal import Decimal

import pytest

from yourosint.contexts.intelligence.domain.confidence import Confidence


def test_valid_confidence():
    c = Confidence(Decimal("0.85"))
    assert c.is_high is True
    assert c.requires_review is False


def test_medium_confidence_requires_review():
    c = Confidence(Decimal("0.55"))
    assert c.is_high is False
    assert c.requires_review is True


def test_invalid_confidence_raises_error():
    with pytest.raises(ValueError, match="between 0.0 and 1.0"):
        Confidence(Decimal("1.5"))

    with pytest.raises(ValueError, match="between 0.0 and 1.0"):
        Confidence(Decimal("-0.1"))
