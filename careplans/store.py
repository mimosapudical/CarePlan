from dataclasses import dataclass, field
from threading import Lock
from typing import Any


@dataclass
class CarePlanRecord:
    id: str
    status: str = "pending"
    history: list[str] = field(default_factory=list)
    payload: dict[str, Any] = field(default_factory=dict)
    care_plan: dict[str, list[str]] | None = None
    error: str | None = None


CARE_PLAN_STORE: dict[str, CarePlanRecord] = {}
STORE_LOCK = Lock()
