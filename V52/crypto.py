"""
Signature Ed25519 et manifeste d'intégrité.

Utilise uniquement la bibliothèque standard + cryptography.
La clé privée n'est jamais incluse dans les distributions publiques.
"""

from __future__ import annotations
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass
class KeyPair:
    private_key: Optional[Ed25519PrivateKey]
    public_key: Ed25519PublicKey

    @classmethod
    def generate(cls) -> "KeyPair":
        private = Ed25519PrivateKey.generate()
        return cls(private_key=private, public_key=private.public_key())

    @classmethod
    def load(
        cls,
        private_path: Optional[str | Path] = None,
        public_path: Optional[str | Path] = None,
    ) -> "KeyPair":
        private = None
        public = None

        if private_path and Path(private_path).exists():
            with open(private_path, "rb") as f:
                private = serialization.load_pem_private_key(f.read(), password=None)

        if public_path and Path(public_path).exists():
            with open(public_path, "rb") as f:
                public = serialization.load_pem_public_key(f.read())
        elif private is not None:
            public = private.public_key()

        if public is None:
            raise ValueError("Impossible de charger une clé publique")

        return cls(private_key=private, public_key=public)

    def save(
        self,
        private_path: Optional[str | Path] = None,
        public_path: Optional[str | Path] = None,
    ) -> None:
        if private_path and self.private_key:
            pem = self.private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
            Path(private_path).write_bytes(pem)

        if public_path:
            pem = self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            Path(public_path).write_bytes(pem)

    def sign(self, data: bytes) -> bytes:
        if self.private_key is None:
            raise RuntimeError("Clé privée absente — impossible de signer")
        return self.private_key.sign(data)

    def verify(self, data: bytes, signature: bytes) -> bool:
        try:
            self.public_key.verify(signature, data)
            return True
        except InvalidSignature:
            return False


@dataclass
class Manifest:
    """Manifeste d'intégrité d'un ou plusieurs journaux."""

    name: str
    version: str
    created_at: str
    journals: Dict[str, Dict[str, Any]]
    engine_version: str = "52.0.0"
    protocol_steps: int = 20

    def to_bytes(self) -> bytes:
        """Sérialisation canonique pour signature."""
        payload = {
            "name": self.name,
            "version": self.version,
            "created_at": self.created_at,
            "journals": self.journals,
            "engine_version": self.engine_version,
            "protocol_steps": self.protocol_steps,
        }
        return json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Manifest":
        return cls(**d)

    def save(self, path: str | Path) -> None:
        Path(path).write_text(
            json.dumps(self.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: str | Path) -> "Manifest":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.from_dict(data)


def create_manifest(
    name: str,
    journals: Dict[str, Path],
    version: str = "1.0",
    protocol_steps: int = 20,
) -> Manifest:
    """
    Crée un manifeste à partir de fichiers de journaux.
    """
    journal_info = {}
    for label, path in journals.items():
        path = Path(path)
        content = path.read_bytes()
        n_lines = content.count(b"\n")
        journal_info[label] = {
            "sha256": _sha256_bytes(content),
            "lines": n_lines,
            "path": str(path.name),
        }

    return Manifest(
        name=name,
        version=version,
        created_at=datetime.now(timezone.utc).isoformat(),
        journals=journal_info,
        protocol_steps=protocol_steps,
    )


def sign_manifest(manifest: Manifest, keypair: KeyPair) -> bytes:
    """Signe le manifeste et retourne la signature brute."""
    return keypair.sign(manifest.to_bytes())


def verify_manifest(
    manifest: Manifest,
    signature: bytes,
    keypair: KeyPair,
) -> bool:
    """Vérifie la signature d'un manifeste."""
    return keypair.verify(manifest.to_bytes(), signature)


def save_signature(signature: bytes, path: str | Path) -> None:
    Path(path).write_bytes(signature)


def load_signature(path: str | Path) -> bytes:
    return Path(path).read_bytes()
