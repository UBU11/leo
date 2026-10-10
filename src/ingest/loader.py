from pathlib import Path
from typing import Protocol, runtime_checkable
from src.models import Lead


@runtime_checkable
class SeedLoader(Protocol):
    def load_seeds(self, source_path: Path | str) -> list[Lead]: ...
