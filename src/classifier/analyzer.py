from typing import Protocol, runtime_checkable
from src.models import GarmentAnalysis


@runtime_checkable
class BrandAnalyzer(Protocol):
    def analyze(self, domain: str, storefront_data: dict[str, str]) -> GarmentAnalysis: ...
