# 🏛️ Architecture Specification — Yourosint v2

## 1. Overview
Yourosint v2 is built using a hybrid of **Domain-Driven Design (DDD) Bounded Contexts** and **Hexagonal Architecture (Ports & Adapters)** within each context.

```
                  ┌──────────────────────────────────────────────┐
                  │                 Entrypoints                  │
                  │   FastAPI Routers  │  Workers  │   CLI       │
                  └──────────────────────┬───────────────────────┘
                                         │
       ┌──────────────────┬──────────────┼──────────────┬──────────────────┐
       ▼                  ▼              ▼              ▼                  ▼
┌──────────────┐   ┌──────────────┐┌──────────────┐┌──────────────┐┌──────────────┐
│  Ingestion   │   │ Intelligence ││    Graph     ││  Enrichment  ││   Privacy    │
│   Context    │   │   Context    ││   Context    ││   Context    ││   Context    │
├──────────────┤   ├──────────────┤├──────────────┤├──────────────┤├──────────────┤
│Domain / Ports│   │Domain / Ports││Domain / Ports││Domain / Ports││Domain / Ports│
│ Adapters:    │   │ Adapters:    ││ Adapters:    ││ Adapters:    ││ Adapters:    │
│ Telegram     │   │ Extractor    ││ NetworkX     ││ Whois, GeoIP ││ HMAC BlindIdx│
│ SQLAlchemy   │   │ SQLAlchemy   ││ SQL CTE      ││ Phone Lib    ││ Sanitizer    │
└──────┬───────┘   └──────┬───────┘└──────┬───────┘└──────┬───────┘└──────┬───────┘
       │                  │               │               │               │
       └──────────────────┴───────────────┼───────────────┴───────────────┘
                                          ▼
                         ┌─────────────────────────────────┐
                         │      Shared Infrastructure      │
                         │  Database Session │ Event Bus   │
                         └─────────────────────────────────┘
```

## 2. Bounded Contexts Summary

1. **Ingestion Context:**
   - Pure domain: `Chat`, `RawMessage`, `IngestionCursor`.
   - Adapters: `AccountPool` (flood-wait shield, session rotation, RPM tracking), `SmartTelegramClient`, `TokenBucketRateLimiter`, `SQLAlchemyMessageRepository`.
2. **Intelligence Context:**
   - Pure domain: `IntelligenceEntity`, `Relation`, `Evidence` (provenance), `Confidence(Decimal)`.
   - Adapters: `RegexEntityExtractor`, `SQLAlchemyIntelligenceRepository`.
3. **Graph Context:**
   - Pure domain: `GraphNode`, `GraphEdge`, `InvestigationGraph`.
   - Adapters: Single-query SQL CTEs, `NetworkXGraphEngine`, layout algorithms.
4. **Enrichment Context:**
   - Pure domain: `EnrichmentRecord`, `ProviderResult`.
   - Adapters: `LibphonenumberAdapter`, `NetworkThreatIntelAdapter`.
5. **Privacy Context:**
   - Pure domain: `PIIType`, `PIIMaskResult`, `DataRetentionPolicy`.
   - Adapters: `HMACBlindIndexService`, `EnvKeyStore`, `PersonalDataSanitizer`.
