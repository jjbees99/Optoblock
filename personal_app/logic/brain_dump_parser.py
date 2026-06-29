from __future__ import annotations

import re
from dataclasses import dataclass


CATEGORIES = ["To-Do", "Shopping", "Projects / Learning", "Reminder Candidate", "Archive / Notes"]
SHOPPING_PATTERN = re.compile(
    r"\b(buy(?:ing)?|order(?:ing)?|get(?:ting)?|purchase|pick\s+up|shopping|groceries)\b",
    re.IGNORECASE,
)
SHOPPING_VERB_PATTERN = re.compile(
    r"^(?:buy(?:ing)?|order(?:ing)?|get(?:ting)?|purchase|pick\s+up|shopping(?:\s+for)?)\s+",
    re.IGNORECASE,
)
TODO_PATTERN = re.compile(
    r"\b(email(?:ing)?|send(?:ing)?|call(?:ing)?|message|reply|finish|check|book|write|clean|review)(?:ing)?\b",
    re.IGNORECASE,
)
PROJECT_PATTERN = re.compile(
    r"\b(look\s+into|research(?:ing)?|learn(?:ing)?|course|project|build(?:ing)?|develop(?:ing)?)\b",
    re.IGNORECASE,
)
ACTION_PATTERN = (
    r"(?:buy(?:ing)?|order(?:ing)?|get(?:ting)?|purchase|pick\s+up|email(?:ing)?|send(?:ing)?|"
    r"call(?:ing)?|message|reply|finish|check|book|write|clean|review(?:ing)?|look\s+into|"
    r"research(?:ing)?|learn(?:ing)?|build(?:ing)?|develop(?:ing)?)"
)
CONVERSATIONAL_PREFIX = (
    r"(?:(?:hey\s+)?(?:so\s+)?)?"
    r"(?:(?:(?:i(?:'m|\s+am)|we(?:'re|\s+are))\s+thinking\s+about|"
    r"(?:i|we)\s+(?:also\s+)?(?:need|have|want|must|should)\s+to)\s+)?"
)
TIME_PATTERN = re.compile(
    r"\b(tomorrow|tonight|later|next week|(?:by\s+)?(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday))\b",
    re.IGNORECASE,
)


@dataclass
class SuggestedItem:
    text: str
    category: str


class BrainDumpParser:
    def parse(self, transcript: str) -> list[SuggestedItem]:
        suggestions: list[SuggestedItem] = []
        seen: set[tuple[str, str]] = set()
        for block in re.split(r"[\n.!?;]+", transcript):
            block = block.strip(" -\t")
            if not block:
                continue
            for marker in TIME_PATTERN.findall(block):
                self._append(suggestions, seen, marker.capitalize(), "Reminder Candidate")
            cleaned = TIME_PATTERN.sub("", block).strip(" ,:-")
            parts = re.split(
                rf"\s*,\s*|\s+and\s+(?={CONVERSATIONAL_PREFIX}{ACTION_PATTERN}\b)",
                cleaned,
                flags=re.IGNORECASE,
            )
            previous_category = ""
            for part in parts:
                text = self._clean_clause(part)
                if not text:
                    continue
                category = self._category(text)
                if category == "Archive / Notes" and previous_category == "Shopping":
                    category = "Shopping"
                if category == "Shopping":
                    for item in self._shopping_items(text):
                        self._append(suggestions, seen, self._sentence_case(item), category)
                else:
                    self._append(suggestions, seen, self._sentence_case(text), category)
                previous_category = category
        return suggestions

    def _category(self, text: str) -> str:
        lowered = text.lower()
        if len(text) > 180:
            return "Archive / Notes"
        if PROJECT_PATTERN.search(lowered):
            return "Projects / Learning"
        if SHOPPING_PATTERN.search(lowered):
            return "Shopping"
        if TODO_PATTERN.search(lowered):
            return "To-Do"
        return "Archive / Notes"

    @staticmethod
    def _clean_clause(text: str) -> str:
        text = text.strip(" ,:-")
        text = re.sub(r"^(?:and\s+)?(?:hey\s+)?(?:so\s+)?", "", text, flags=re.IGNORECASE)
        text = re.sub(
            r"^(?:(?:i(?:'m|\s+am)|we(?:'re|\s+are))\s+thinking\s+about|"
            r"(?:i|we)\s+(?:also\s+)?(?:need|have|want|must|should)\s+to)\s+",
            "",
            text,
            flags=re.IGNORECASE,
        )
        # Spoken notes often contain several lead-ins. Keep the actionable phrase.
        action = re.search(ACTION_PATTERN, text, flags=re.IGNORECASE)
        if action:
            text = text[action.start():]
        replacements = {
            r"^buying\b": "Buy",
            r"^ordering\b": "Order",
            r"^getting\b": "Get",
            r"^emailing\b": "Email",
            r"^sending\b": "Send",
            r"^calling\b": "Call",
            r"^researching\b": "Research",
            r"^learning\b": "Learn",
            r"^building\b": "Build",
            r"^developing\b": "Develop",
        }
        for pattern, replacement in replacements.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        return text.strip()

    @staticmethod
    def _sentence_case(text: str) -> str:
        return text[:1].upper() + text[1:]

    @staticmethod
    def _shopping_items(text: str) -> list[str]:
        text = SHOPPING_VERB_PATTERN.sub("", text, count=1).strip()
        items = re.split(r"\s+and\s+", text, flags=re.IGNORECASE)
        cleaned = [re.sub(r"^(?:some|a|an|the)\s+", "", item.strip(), flags=re.IGNORECASE) for item in items]
        return [item for item in cleaned if item]

    @staticmethod
    def _append(items: list[SuggestedItem], seen: set[tuple[str, str]], text: str, category: str) -> None:
        key = (text.casefold(), category)
        if key not in seen:
            seen.add(key)
            items.append(SuggestedItem(text, category))
