# 🛰️ Yourosint v2 — OSINT & Threat Intel Graph Platform

> **Modern, High-Performance OSINT & Intelligence Graph Platform for Telegram.**
> Engineered with Clean Layered Architecture, PostgreSQL GIN Trigram Indexing, HMAC-SHA256 Blind Indexing, and Single-Query SQL CTE Network Graph Analysis.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com)
[![SQLAlchemy 2.0](https://img.shields.io/badge/SQLAlchemy-2.0%20Async-d71f00.svg)](https://www.sqlalchemy.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🌟 Highlights & Key Features

- **🏛️ Clean Layered Architecture (`src/yourosint/`):**
  - **Domain:** Pure Pydantic v2 entities (`Object`, `Relation`, `Evidence`, `Message`, `TelegramAccount`) and immutable value objects (`BlindIndexValue`, `NormalizedPhone`, `NormalizedEmail`).
  - **Application (Use Cases):** `ParseChatUseCase`, `SearchEntitiesUseCase`, `BuildGraphUseCase`, `ExtractObjectsUseCase`, `DiscoverChatsUseCase`, `EnrichEntityUseCase`.
  - **Ports & Adapters:** Decoupled protocol interfaces (`ObjectStorePort`, `MessageRepositoryPort`, `AccountPoolPort`, `BlindIndexPort`).
  - **Infrastructure:** Async SQLAlchemy 2.0 + Alembic, PostgreSQL `pg_trgm` & `tsvector` GIN indexes, NetworkX graph engine, Telethon client adapter.
- **🛡️ Golden AccountPool Orchestration:**
  - Dynamic lease-based account rotation across multiple Telegram sessions.
  - Automatic handling of `FloodWaitError` with backoff timers, cooling states, and periodic health-check heartbeats (`_health_check_loop`).
  - Sliding-window RPM rate limiter and intelligent chat affinity routing.
- **⚡ Single-Query SQL CTE Network Graph:**
  - One query `WITH target_ids → all_users → enriched_users` with `LATERAL` joins eliminates N+1 queries.
  - Generates rich multi-level social interaction and correlation graphs in sub-50ms.
- **🔒 Zero-Knowledge Blind Indexing & Data Masking:**
  - Protects sensitive intelligence data (phone numbers, emails, credit cards) using HMAC-SHA256 keyed digests and NFKC Unicode normalization.
  - Supports key versioning and rotation without data exposure.
- **🔎 Multi-Modal Intelligence Extraction:**
  - Automatic extraction & validation of emails, domains, public IPs (RFC 1918 filtered), phones (E.164 normalized), credit cards (Luhn validated), Bitcoin & Ethereum wallet addresses.
  - Built-in PII filter (`PersonalDataFilter`) to prevent leaking sensitive personal records into logs.
- **🤖 Autonomous Autopilot & Multi-Source Discovery:**
  - Automatic discovery via Telegram global search, `@UniversalSearchSmartBot`, `@MotherSearchBot`, and `@letstgbot`.
  - Continuous discovery, ingestion queue, entity extraction, and threat enrichment pipeline.
- **🖥️ Dual Web Dashboard Experience:**
  - Built-in reactive Web UI at `/dashboard` powered by Tailwind CSS & SVG graph visualizer.
  - Next.js 15 + Tailwind modern frontend located in `web/`.

---

## 🏗️ Architecture Layout

```
yourosint-v2/
├── src/yourosint/
│   ├── domain/               # Core entities, enums, value objects, exceptions (Pydantic v2)
│   ├── application/          # Use cases (ParseChat, SearchEntities, BuildGraph, ExtractObjects)
│   ├── ports/                # DatabasePort, TelegramPort, ExtractorPort, BlindIndexPort
│   ├── infrastructure/
│   │   ├── persistence/      # SQLAlchemy 2.0 async ORM, repositories, Alembic, COPY engine
│   │   ├── telegram/         # SmartTelegramClient, AccountPool, SmartParser, PII filters
│   │   ├── privacy/          # BlindIndexService (HMAC-SHA256, NFKC, key rotation, masking)
│   │   ├── graph/            # NetworkX graph engine, layout algorithms, topology exporter
│   │   └── enrichment/       # Threat intel lookup, Phone validator, IP/Domain WHOIS & Geo
│   ├── workers/              # AutopilotWorker, BackgroundEnrichmentWorker
│   └── api/                  # FastAPI 0.110+ REST API & Embedded Intelligence Console
├── alembic/                  # Database migration scripts with PostgreSQL GIN indexes
├── tests/                    # Comprehensive test suite (unit + integration, 25+ tests)
├── web/                      # Next.js 15 frontend application
├── scripts/                  # Seed demo data and standalone worker scripts
└── pyproject.toml            # Project configuration, ruff, mypy, pytest
```

---

## 🚀 Quick Start

### 1. Installation

```bash
cd yourosint-v2
pip install -e .
```

### 2. Environment Setup

Copy example environment variables:
```bash
cp .env.example .env
```

### 3. Seed Demo Data (Optional)

```bash
python scripts/seed.py
```

### 4. Run REST API & Dashboard

```bash
uvicorn yourosint.api.app:app --host 0.0.0.0 --port 8000 --reload
```

Open your browser at:
- **Interactive Dashboard:** `http://localhost:8000/dashboard`
- **Swagger Documentation:** `http://localhost:8000/docs`

---

## 🧪 Running Tests & Quality Checks

Run the complete test suite:
```bash
pytest
```

Run linter and formatter (Ruff):
```bash
ruff check .
ruff format --check .
```

---

## 🔌 API Endpoints Summary

| Method | Route | Description |
|---|---|---|
| `GET` | `/api/v1/health` | Service health and liveness probe |
| `GET` | `/api/v1/stats` | Aggregated messages, users, chats & entity statistics |
| `GET` | `/api/v1/search` | Multi-index search (Trigram, TSVector, Blind Index, Exact) |
| `GET` | `/api/v1/graph/user/{username}` | Interaction network graph computed via SQL CTE |
| `GET` | `/api/v1/objects` | List and filter intelligence entities |
| `POST` | `/api/v1/objects` | Create or update intelligence entity with provenance |
| `GET` | `/api/v1/objects/{id}/relations` | Connected graph relations for entity |
| `GET` | `/api/v1/objects/{id}/evidence` | Verifiable provenance records |
| `POST` | `/api/v1/parser/parse` | Ingest Telegram channel & extract entities |
| `GET` | `/api/v1/accounts/stats` | Real-time AccountPool status & RPM metrics |
| `POST` | `/api/v1/accounts/{name}/rotate` | Rotate account session |
| `POST` | `/api/v1/autopilot/control` | Start or stop background discovery & parsing worker |

---

## 📜 License

MIT License © 2026 wykse.
