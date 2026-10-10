from typing import Protocol, runtime_checkable


@runtime_checkable
class StoreCrawler(Protocol):
    def crawl(self, domain: str) -> dict[str, str]: ...
