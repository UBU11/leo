from typing import Protocol, runtime_checkable


@runtime_checkable
class ReviewServer(Protocol):
    def run(self, host: str = "127.0.0.1", port: int = 8000) -> None: ...
