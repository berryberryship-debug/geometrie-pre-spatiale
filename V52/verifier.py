"""
Vérificateur d'intégrité des journaux et des manifests.
"""

from __future__ import annotations
import json
import hashlib
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any

from .crypto import Manifest, KeyPair, verify_manifest, load_signature


def _sha256(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


@dataclass
class AuditReport:
    """Rapport d'audit complet."""

    journal_ok: bool = False
    chain_ok: bool = False
    completeness_ok: bool = False
    manifest_ok: bool = False
    signature_ok: bool = False
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        return (
            self.journal_ok
            and self.chain_ok
            and self.completeness_ok
            and self.manifest_ok
            and self.signature_ok
            and not self.errors
        )

    def summary(self) -> str:
        lines = [
            "=== Rapport d'audit MCC ===",
            f"  Journal valide      : {'OK' if self.journal_ok else 'ÉCHEC'}",
            f"  Chaînage intact     : {'OK' if self.chain_ok else 'ÉCHEC'}",
            f"  Complétude          : {'OK' if self.completeness_ok else 'ÉCHEC'}",
            f"  Manifeste cohérent  : {'OK' if self.manifest_ok else 'ÉCHEC'}",
            f"  Signature Ed25519   : {'OK' if self.signature_ok else 'ÉCHEC'}",
        ]
        if self.errors:
            lines.append("\nErreurs :")
            for e in self.errors:
                lines.append(f"  - {e}")
        if self.warnings:
            lines.append("\nAvertissements :")
            for w in self.warnings:
                lines.append(f"  - {w}")
        lines.append(f"\nRésultat global : {'SUCCÈS' if self.success else 'ÉCHEC'}")
        return "\n".join(lines)


def verify_journal(
    path: str | Path,
    with_memory: bool = True,
    expected_lines: Optional[int] = None,
) -> Tuple[bool, List[str]]:
    """
    Vérifie l'intégrité d'un journal.
    """
    path = Path(path)
    errors: List[str] = []

    if not path.exists():
        return False, [f"Fichier absent : {path}"]

    lines = [l.strip() for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]

    if expected_lines is not None and len(lines) != expected_lines:
        errors.append(
            f"Complétude : {len(lines)} lignes au lieu de {expected_lines}"
        )

    prev_hash: Optional[str] = None

    for i, line in enumerate(lines, start=1):
        try:
            entry = json.loads(line)
        except json.JSONDecodeError as e:
            errors.append(f"Ligne {i} : JSON invalide ({e})")
            continue

        stored_hash = entry.pop("hash", None)
        if stored_hash is None:
            errors.append(f"Ligne {i} : champ 'hash' manquant")
            continue

        # Vérification du chaînage
        if with_memory:
            expected_prev = prev_hash
            actual_prev = entry.get("prev_hash")
            if actual_prev != expected_prev:
                errors.append(
                    f"Ligne {i} : rupture de chaîne "
                    f"(prev_hash={actual_prev} ≠ attendu {expected_prev})"
                )
        else:
            if entry.get("prev_hash") is not None:
                errors.append(f"Ligne {i} : prev_hash doit être null en mode sans mémoire")
            entry["prev_hash"] = None

        # Recalcul du hash
        entry_str = json.dumps(entry, sort_keys=True, ensure_ascii=False)
        computed = _sha256(entry_str)
        if computed != stored_hash:
            errors.append(f"Ligne {i} : hash invalide")

        prev_hash = stored_hash

    return len(errors) == 0, errors


def full_audit(
    journal_paths: Dict[str, Path],
    manifest_path: Path,
    signature_path: Path,
    public_key_path: Path,
    expected_lines: int = 20,
) -> AuditReport:
    """
    Audit complet : journaux + manifeste + signature.
    """
    report = AuditReport()

    # 1. Vérification des journaux
    all_journals_ok = True
    for label, jpath in journal_paths.items():
        with_memory = "avec_memoire" in label or "memory" in label
        ok, errs = verify_journal(jpath, with_memory=with_memory, expected_lines=expected_lines)
        report.details[f"journal_{label}"] = {"ok": ok, "errors": errs}
        if not ok:
            all_journals_ok = False
            report.errors.extend([f"[{label}] {e}" for e in errs])

    report.journal_ok = all_journals_ok
    report.chain_ok = all_journals_ok
    report.completeness_ok = all_journals_ok

    # 2. Manifeste
    try:
        manifest = Manifest.load(manifest_path)
        report.details["manifest"] = manifest.to_dict()

        for label, info in manifest.journals.items():
            if label not in journal_paths:
                report.warnings.append(f"Journal '{label}' présent dans le manifeste mais pas fourni")
                continue
            actual_hash = hashlib.sha256(journal_paths[label].read_bytes()).hexdigest()
            if actual_hash != info["sha256"]:
                report.errors.append(
                    f"Hash du journal '{label}' ne correspond pas au manifeste"
                )
                report.manifest_ok = False
            else:
                report.manifest_ok = True

    except Exception as e:
        report.errors.append(f"Impossible de charger le manifeste : {e}")
        report.manifest_ok = False

    # 3. Signature
    try:
        keypair = KeyPair.load(public_path=public_key_path)
        signature = load_signature(signature_path)
        sig_ok = verify_manifest(manifest, signature, keypair)
        report.signature_ok = sig_ok
        if not sig_ok:
            report.errors.append("Signature Ed25519 invalide")
    except Exception as e:
        report.errors.append(f"Erreur de vérification de signature : {e}")
        report.signature_ok = False

    return report
