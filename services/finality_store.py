from __future__ import annotations

from finality_store_base import FinalityStoreBase
from finality_store_file import FileFinalityStore
from finality_store_sqlite import SQLiteFinalityStore


FinalityStore = FileFinalityStore


def build_finality_store(
    *,
    state_backend: str = "file",
    state_file: str = "runtime/finality-state.json",
    state_db: str = "runtime/finality-state.sqlite3",
) -> FinalityStoreBase:
    if state_backend == "file":
        return FileFinalityStore(state_file)

    if state_backend == "sqlite":
        return SQLiteFinalityStore(state_db)

    raise ValueError(f"unsupported finality state backend: {state_backend}")
