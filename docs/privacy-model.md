# 🔒 Privacy & Data Protection Model

## 1. Zero-Knowledge Search via Blind Indexing
- Sensitive values (bank cards, phone numbers, emails) are transformed via HMAC-SHA256.
- Database index lookups match on `blind_index = "v1:<hex>"`.
- Plaintext data is never written to log files or persistent search indexes.

## 2. PII Sanitization
- `PersonalDataSanitizer` scans all raw message streams for passport numbers, tax IDs (INN), insurance numbers (SNILS), and replaces them with `[TYPE MASKED]`.

## 3. Provenance & Evidence
- Every extracted intelligence artifact contains a cryptographic `content_hash`, timestamp, and confidence score.
