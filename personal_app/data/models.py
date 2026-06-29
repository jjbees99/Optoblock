from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Option:
    label: str
    value: str


@dataclass
class DashboardModule:
    id: str
    title: str
    type: str
    x: int
    y: int
    width: int = 1
    height: int = 1
    content: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DashboardModule":
        return cls(
            id=str(data["id"]),
            title=str(data.get("title", data["id"])),
            type=str(data.get("type", data["id"])),
            x=int(data.get("x", 0)),
            y=int(data.get("y", 0)),
            width=int(data.get("width", 1)),
            height=int(data.get("height", 1)),
            content=dict(data.get("content") or {}),
        )
