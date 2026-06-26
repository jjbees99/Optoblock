def clipped(text: str, limit: int = 70) -> str:
    text = text or ""
    return text if len(text) <= limit else text[: limit - 1] + "..."
