# ADR 0001: Adoption of Bounded Contexts with Hexagonal Architecture

## Status
Accepted

## Context
In monolithic OSINT scrapers and bots, layers quickly degrade into anti-patterns with mixed responsibilities. Changes in Telegram parsing break entity extraction, and changes in database schemas break graph rendering.

## Decision
We organize `yourosint` into five isolated Bounded Contexts:
1. `ingestion` (Raw Telegram message ingestion, account pool, cursors)
2. `intelligence` (Entities, relationships, provenance evidence, confidence)
3. `graph` (Network analytics, interaction topology, CTEs)
4. `enrichment` (External lookups: GeoIP, WHOIS, phone carrier)
5. `privacy` (HMAC blind indexing, key rotation, PII sanitization)

Each context contains its own `domain/`, `application/`, `ports/`, and `adapters/`.

## Consequences
- Zero coupling between Telegram protocol dependencies and graph analytical algorithms.
- Clear separation between Commands (writes) and Queries (reads).
- Independent testing and maintenance.
