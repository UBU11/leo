from typing import Protocol, runtime_checkable
from src.models import OutreachMessage


@runtime_checkable
class OutboundSender(Protocol):
    def send(self, message: OutreachMessage) -> bool: ...
