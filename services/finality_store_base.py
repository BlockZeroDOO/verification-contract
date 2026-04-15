from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class FinalityStoreBase(ABC):
    @abstractmethod
    def read(self) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def write(self, payload: Dict[str, Any]) -> None:
        raise NotImplementedError

    @abstractmethod
    def upsert_request(self, request_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def patch_request(self, request_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def get_request(self, request_id: str) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def list_requests(self) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def export_state(self) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def import_state(self, payload: Dict[str, Any]) -> None:
        raise NotImplementedError
