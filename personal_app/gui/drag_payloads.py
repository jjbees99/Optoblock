TASK_MIME_TYPE = "application/x-optoblock-task"


def encode_task(title: str) -> bytes:
    return title.strip().encode("utf-8")


def decode_task(payload: bytes) -> str:
    return bytes(payload).decode("utf-8").strip()
