"""Command & Handler: PII sanitization."""

import re
from dataclasses import dataclass

from ....shared.application.command import Command, CommandHandler
from ..domain.pii import PIIMaskResult


class PersonalDataSanitizer:
    """PII sanitization engine to prevent leaking sensitive personal data into logs and UI."""

    def __init__(self):
        self.patterns = [
            (re.compile(r"\b\d{4}\s*\d{6}\b", re.IGNORECASE), "PASSPORT"),
            (re.compile(r"\b\d{2}\s?\d{2}\s?\d{6}\b", re.IGNORECASE), "PASSPORT"),
            (re.compile(r"[A-Z]{2}\s?\d{6}\b", re.IGNORECASE), "PASSPORT"),
            (
                re.compile(
                    r"\+?\d{1,3}[\s\-]?\(?\d{1,4}\)?[\s\-]?\d{1,4}[\s\-]?\d{1,4}[\s\-]?\d{1,4}",
                    re.IGNORECASE,
                ),
                "PHONE",
            ),
            (
                re.compile(
                    r"8[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}", re.IGNORECASE
                ),
                "PHONE",
            ),
            (
                re.compile(
                    r"\+7[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}", re.IGNORECASE
                ),
                "PHONE",
            ),
            (re.compile(r"\b\d{2}\.\d{2}\.\d{4}\b", re.IGNORECASE), "BIRTH_DATE"),
            (re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", re.IGNORECASE), "EMAIL"),
            (re.compile(r"\b\d{3}-\d{3}-\d{3}\s?\d{2}\b", re.IGNORECASE), "SNILS"),
            (re.compile(r"\b\d{10}\b", re.IGNORECASE), "INN"),
            (re.compile(r"\b\d{12}\b", re.IGNORECASE), "INN"),
        ]

    def sanitize(self, text: str) -> PIIMaskResult:
        if not text:
            return PIIMaskResult(sanitized_text="", detected_pii=[], has_pii=False)

        cleaned = text
        found = []
        for pattern, label in self.patterns:
            matches = pattern.findall(cleaned)
            for match in matches:
                if match:
                    found.append(f"{label}: {match}")
                    cleaned = re.sub(
                        re.escape(match), f"[{label} MASKED]", cleaned, flags=re.IGNORECASE
                    )

        return PIIMaskResult(sanitized_text=cleaned, detected_pii=found, has_pii=bool(found))


@dataclass(frozen=True, slots=True)
class MaskPIICommand(Command):
    text: str


class MaskPIIHandler(CommandHandler[PIIMaskResult]):
    def __init__(self, sanitizer: PersonalDataSanitizer | None = None):
        self.sanitizer = sanitizer or PersonalDataSanitizer()

    async def handle(self, cmd: MaskPIICommand) -> PIIMaskResult:
        return self.sanitizer.sanitize(cmd.text)
