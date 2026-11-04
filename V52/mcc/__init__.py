"""
MCC — Moteur de Cohérence Contextuelle
Version 52 (refonte propre et publique)

Un petit moteur de simulation d'états dynamiques
protégé par chaînage cryptographique + signatures Ed25519.
"""

__version__ = "52.0.0"
__author__ = "MCC Community"

from .engine import MCCEngine
from .journal import JournalMCC
from .crypto import (
    KeyPair,
    Manifest,
    create_manifest,
    sign_manifest,
    verify_manifest,
    save_signature,
    load_signature,
)
from .verifier import verify_journal, full_audit, AuditReport

__all__ = [
    "MCCEngine",
    "JournalMCC",
    "KeyPair",
    "Manifest",
    "create_manifest",
    "sign_manifest",
    "verify_manifest",
    "save_signature",
    "load_signature",
    "verify_journal",
    "full_audit",
    "AuditReport",
]
