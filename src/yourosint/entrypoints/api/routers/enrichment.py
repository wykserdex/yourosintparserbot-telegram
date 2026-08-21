"""Enrichment Context Router."""

from typing import Any

from fastapi import APIRouter, Depends

from yourosint.bootstrap import Container

from ..dependencies import get_container

router = APIRouter(prefix="/enrichment", tags=["Enrichment"])


@router.get("/phone/{phone}")
async def lookup_phone_intelligence(
    phone: str, c: Container = Depends(get_container)
) -> dict[str, Any]:
    """Parse, validate, and extract carrier intelligence for phone number."""
    return c.phone_lookup.lookup_phone(phone)


@router.get("/network/{target}")
async def lookup_network_intelligence(
    target: str, c: Container = Depends(get_container)
) -> dict[str, Any]:
    """Lookup IP / Domain reputation and geolocation."""
    res = await c.network_lookup.lookup_network_ioc(target)
    return {
        "provider": res.provider,
        "target": res.target,
        "is_valid": res.is_valid,
        "risk_score": res.risk_score,
        "details": res.details,
    }
