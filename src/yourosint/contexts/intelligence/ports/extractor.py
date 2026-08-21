"""Intelligence Ports: Extractor Port."""

from typing import Protocol

from ..domain.entity import EntityType


class EntityExtractorPort(Protocol):
    """Port for entity extraction engines."""

    def extract_all(self, text: str) -> dict[EntityType, list[str]]: ...
