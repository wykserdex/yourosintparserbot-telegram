# ADR 0002: Keyed HMAC-SHA256 Blind Indexing for Sensitive IOCs

## Status
Accepted

## Context
OSINT platforms frequently encounter sensitive personal information (phones, personal emails, payment cards). Storing raw sensitive values poses compliance and breach risks. Simple unkeyed SHA-256 is vulnerable to rainbow table attacks.

## Decision
We implement Keyed HMAC-SHA256 Blind Indexing with NFKC Unicode normalization and key versioning:
`blind_index = f"{version}:{hmac_sha256(key, normalized_val)}"`

## Consequences
- Queries can find duplicate entities across chats without decrypting or storing plaintext.
- Key rotation is supported via transition indexing.
