"""Feature flags for controlling progressive rollouts."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FeatureFlags:
    enable_pii_masking: bool = True
    enable_blind_index_rotation: bool = True
    enable_second_level_graph: bool = True
    enable_autopilot_discovery: bool = True
    enable_postgres_copy_engine: bool = True
