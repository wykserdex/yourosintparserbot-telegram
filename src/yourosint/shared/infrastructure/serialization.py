"""JSON serialization helpers with datetime and dataclass support."""

import json
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any


class DomainJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder supporting datetime, Decimal, and dataclasses."""

    def default(self, o: Any) -> Any:
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        if isinstance(o, Decimal):
            return float(o)
        if is_dataclass(o) and not isinstance(o, type):
            return asdict(o)
        return super().default(o)


def to_json(obj: Any) -> str:
    """Serializes object to JSON string."""
    return json.dumps(obj, cls=DomainJSONEncoder)


def from_json(json_str: str) -> Any:
    """Deserializes JSON string."""
    return json.loads(json_str)
