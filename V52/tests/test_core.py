#!/usr/bin/env python3
"""Tests unitaires et d'intégration pour MCC v52."""

from __future__ import annotations
import json
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mcc import MCCEngine, JournalMCC, KeyPair, create_manifest, sign_manifest, verify_manifest
from mcc.verifier import verify_journal


def test_engine_basic():
    engine = MCCEngine()
    state = engine.step(0.4, 0.7)
    assert state.step == 1
    assert 0.1 <= state.C <= 1.0
    assert state.sigma >= 0.0
    print("[OK] test_engine_basic")


def test_engine_run():
    engine = MCCEngine()
    history = engine.run(10)
    assert len(history) == 10
    assert history[-1].step == 10
    print("[OK] test_engine_run")


def test_journal_with_memory():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "j.jsonl"
        with JournalMCC(path, with_memory=True) as j:
            j.log({"step": 1, "val": 10})
            j.log({"step": 2, "val": 20})
            j.log({"step": 3, "val": 30})

        ok, errors = verify_journal(path, with_memory=True, expected_lines=3)
        assert ok, errors
        print("[OK] test_journal_with_memory")


def test_journal_without_memory():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "j.jsonl"
        with JournalMCC(path, with_memory=False) as j:
            j.log({"step": 1, "val": 10})
            j.log({"step": 2, "val": 20})

        ok, errors = verify_journal(path, with_memory=False, expected_lines=2)
        assert ok, errors
        print("[OK] test_journal_without_memory")


def test_falsification_detection():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "j.jsonl"
        with JournalMCC(path, with_memory=True) as j:
            j.log({"step": 1, "val": 10})
            j.log({"step": 2, "val": 20})
            j.log({"step": 3, "val": 30})

        # Falsification
        lines = path.read_text().splitlines()
        lines[1] = lines[1].replace('"val": 20', '"val": 999')
        path.write_text("\n".join(lines) + "\n")

        ok, errors = verify_journal(path, with_memory=True)
        assert not ok
        assert any("hash invalide" in e or "rupture" in e for e in errors)
        print("[OK] test_falsification_detection")


def test_signature_roundtrip():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        # Création d'un petit journal
        jpath = tmp / "j.jsonl"
        with JournalMCC(jpath, with_memory=True) as j:
            j.log({"step": 1, "val": 42})

        keypair = KeyPair.generate()
        manifest = create_manifest("test", {"main": jpath})
        sig = sign_manifest(manifest, keypair)

        assert verify_manifest(manifest, sig, keypair)

        # Falsification du manifeste
        manifest.journals["main"]["sha256"] = "0" * 64
        assert not verify_manifest(manifest, sig, keypair)
        print("[OK] test_signature_roundtrip")


def test_full_pipeline():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        engine = MCCEngine()
        history = engine.run(5)

        path_avec = tmp / "avec.jsonl"
        with JournalMCC(path_avec, with_memory=True) as j:
            for s in history:
                j.log(s.to_dict())

        ok, _ = verify_journal(path_avec, with_memory=True, expected_lines=5)
        assert ok
        print("[OK] test_full_pipeline")


if __name__ == "__main__":
    test_engine_basic()
    test_engine_run()
    test_journal_with_memory()
    test_journal_without_memory()
    test_falsification_detection()
    test_signature_roundtrip()
    test_full_pipeline()
    print("\nTous les tests sont passés.")
