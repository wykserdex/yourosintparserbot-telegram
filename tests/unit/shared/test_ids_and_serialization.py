"""Unit tests for shared infrastructure and domain primitives."""

from datetime import UTC, datetime
from decimal import Decimal

from yourosint.shared.application.result import Result
from yourosint.shared.infrastructure.clock import FrozenClock, SystemClock
from yourosint.shared.infrastructure.ids import deterministic_id, generate_uuid
from yourosint.shared.infrastructure.serialization import from_json, to_json


def test_uuid_generation():
    u1 = generate_uuid()
    u2 = generate_uuid()
    assert u1 != u2
    assert len(u1) == 36


def test_deterministic_id():
    d1 = deterministic_id("entity", "Email", "Target@Example.com")
    d2 = deterministic_id("entity", "email", "target@example.com")
    assert d1 == d2
    assert d1.startswith("entity_")


def test_clock():
    sys_clock = SystemClock()
    assert sys_clock.now() is not None

    fixed_time = datetime(2026, 8, 21, 12, 0, 0, tzinfo=UTC)
    frozen_clock = FrozenClock(fixed_time)
    assert frozen_clock.now() == fixed_time


def test_result_monad():
    res_ok = Result.ok(42)
    assert res_ok.is_success is True
    assert res_ok.unwrap() == 42

    res_fail = Result.fail(ValueError("Invalid token"))
    assert res_fail.is_success is False


def test_serialization():
    payload = {
        "timestamp": datetime(2026, 8, 21, 10, 0, 0, tzinfo=UTC),
        "confidence": Decimal("0.85"),
    }
    serialized = to_json(payload)
    assert "2026-08-21T10:00:00+00:00" in serialized
    deserialized = from_json(serialized)
    assert deserialized["confidence"] == 0.85
