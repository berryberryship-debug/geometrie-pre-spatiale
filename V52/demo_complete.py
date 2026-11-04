#!/usr/bin/env python3
"""
Démonstration complète du MCC v52.
"""

from __future__ import annotations
import sys
from pathlib import Path

# Ajoute le package parent au path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mcc import (
    MCCEngine,
    JournalMCC,
    KeyPair,
    create_manifest,
    sign_manifest,
    verify_manifest,
    save_signature,
    verify_journal,
    full_audit,
)
from mcc.crypto import Manifest


def main():
    print("=" * 70)
    print("  MCC v52 — Démonstration complète")
    print("=" * 70)

    out = Path("demo_output")
    out.mkdir(exist_ok=True)

    # 1. Génération des clés
    print("\n[1] Génération / chargement des clés Ed25519...")
    keypair = KeyPair.generate()
    keypair.save(
        private_path=out / "private_key.pem",
        public_path=out / "public_key.pem",
    )
    print("    → Clés sauvegardées dans demo_output/")

    # 2. Simulation du moteur
    print("\n[2] Simulation du moteur MCC (20 pas)...")
    engine = MCCEngine()
    history = engine.run(n_steps=20)
    print(f"    → {len(history)} états générés")
    print(f"    → État final : C={history[-1].C:.4f}  sigma={history[-1].sigma:.4f}")

    # 3. Journaux
    print("\n[3] Écriture des journaux...")
    path_avec = out / "journal_avec_memoire.jsonl"
    path_sans = out / "journal_sans_memoire.jsonl"

    with JournalMCC(path_avec, with_memory=True) as j:
        for state in history:
            j.log(state.to_dict())

    with JournalMCC(path_sans, with_memory=False) as j:
        for state in history:
            j.log(state.to_dict())

    print(f"    → {path_avec.name}")
    print(f"    → {path_sans.name}")

    # 4. Manifeste + signature
    print("\n[4] Création et signature du manifeste...")
    manifest = create_manifest(
        name="MCC_V52_DEMO",
        journals={
            "avec_memoire": path_avec,
            "sans_memoire": path_sans,
        },
        protocol_steps=20,
    )
    manifest.save(out / "manifest.json")

    signature = sign_manifest(manifest, keypair)
    save_signature(signature, out / "manifest.sig")
    print("    → manifest.json + manifest.sig créés")

    # 5. Vérification nominale
    print("\n[5] Vérification nominale...")
    ok_avec, err_avec = verify_journal(path_avec, with_memory=True, expected_lines=20)
    ok_sans, err_sans = verify_journal(path_sans, with_memory=False, expected_lines=20)
    sig_ok = verify_manifest(manifest, signature, keypair)

    print(f"    Journal avec mémoire : {'OK' if ok_avec else 'ÉCHEC'}")
    print(f"    Journal sans mémoire : {'OK' if ok_sans else 'ÉCHEC'}")
    print(f"    Signature Ed25519    : {'OK' if sig_ok else 'ÉCHEC'}")

    # 6. Test de falsification
    print("\n[6] Test de détection de falsification...")
    import re
    lines = path_avec.read_text().splitlines()
    falsified = re.sub(r'"M_c": [0-9.]+', '"M_c": 999.0', lines[5])
    lines[5] = falsified
    path_falsifie = out / "journal_falsifie.jsonl"
    path_falsifie.write_text("\n".join(lines) + "\n")

    ok_f, err_f = verify_journal(path_falsifie, with_memory=True)
    print(f"    Falsification détectée : {'OUI' if not ok_f else 'NON (!)'}")
    if err_f:
        print(f"    → {err_f[0]}")

    # 7. Audit complet
    print("\n[7] Audit complet...")
    report = full_audit(
        journal_paths={
            "avec_memoire": path_avec,
            "sans_memoire": path_sans,
        },
        manifest_path=out / "manifest.json",
        signature_path=out / "manifest.sig",
        public_key_path=out / "public_key.pem",
        expected_lines=20,
    )
    print(report.summary())

    print("\n" + "=" * 70)
    print("  Fichiers générés dans ./demo_output/")
    print("  (la clé privée est locale — ne jamais la publier)")
    print("=" * 70)


if __name__ == "__main__":
    main()
