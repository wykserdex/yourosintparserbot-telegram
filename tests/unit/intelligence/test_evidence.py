"""Unit tests for Evidence provenance model."""

from decimal import Decimal

from yourosint.contexts.intelligence.domain.confidence import Confidence
from yourosint.contexts.intelligence.domain.evidence import Evidence


def test_evidence_instantiation():
    ev = Evidence(
        source_id="msg_101",
        source_type="telegram_channel",
        raw_context="Observed scam transaction on ton.org",
        content_hash="abc12345",
        confidence=Confidence(Decimal("0.90")),
    )
    assert ev.source_id == "msg_101"
    assert ev.confidence.is_high is True
    assert ev.extractor_version == "regex_v2.0"
