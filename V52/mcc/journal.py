"""
Journal cryptographique pour le MCC.

Deux modes :
  - with_memory=True  → chaînage SHA-256 (chaque entrée inclut le hash précédent)
  - with_memory=False → chaque entrée est hashée isolément
"""

from __future__ import annotations
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, Iterator


def _sha256(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


class JournalMCC:
    """
    Journal append-only avec intégrité cryptographique.
    """

    def __init__(self, path: str | Path, with_memory: bool = True):
        self.path = Path(path)
        self.with_memory = with_memory
        self.previous_hash: Optional[str] = None
        self._file = open(self.path, "w", encoding="utf-8")
        self._count = 0

    def log(self, state: Dict[str, Any]) -> str:
        """
        Ajoute une entrée au journal et retourne son hash.
        """
        entry = dict(state)  # copie défensive

        if self.with_memory:
            entry["prev_hash"] = self.previous_hash
        else:
            entry["prev_hash"] = None

        # On calcule le hash sur l'entrée SANS le champ "hash"
        entry_str = json.dumps(entry, sort_keys=True, ensure_ascii=False)
        current_hash = _sha256(entry_str)
        entry["hash"] = current_hash

        self._file.write(json.dumps(entry, ensure_ascii=False) + "\n")
        self._file.flush()

        self.previous_hash = current_hash
        self._count += 1
        return current_hash

    def close(self) -> None:
        if self._file and not self._file.closed:
            self._file.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    @property
    def count(self) -> int:
        return self._count

    @staticmethod
    def read(path: str | Path) -> list[Dict[str, Any]]:
        """Lit un journal existant."""
        entries = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
        return entries

    @staticmethod
    def iterate(path: str | Path) -> Iterator[Dict[str, Any]]:
        """Itère sur un journal sans tout charger en mémoire."""
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    yield json.loads(line)
