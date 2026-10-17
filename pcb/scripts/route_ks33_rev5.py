#!/usr/bin/env python3
"""Route a Rev5 KS-33 board with Freerouting."""

from pathlib import Path
import argparse
import hashlib
import subprocess
import tempfile

import pcbnew


REQUIRED_FREEROUTING_SHA256 = (
    "f6f51bb02245e8e717f9359bd260cc9c5c0b1bc0acc8b7cb2cd5b8ffeb5de3c7"
)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("board")
    parser.add_argument("--java", required=True)
    parser.add_argument("--freerouting-jar", required=True)
    parser.add_argument("--passes", type=int, default=100)
    parser.add_argument("--threads", type=int, default=6)
    args = parser.parse_args()

    board_path = Path(args.board).resolve()
    java_path = Path(args.java).resolve()
    jar_path = Path(args.freerouting_jar).resolve()
    if not java_path.is_file():
        raise RuntimeError(f"Java executable not found: {java_path}")
    if not jar_path.is_file():
        raise RuntimeError(f"Freerouting JAR not found: {jar_path}")
    jar_hash = sha256(jar_path)
    if jar_hash != REQUIRED_FREEROUTING_SHA256:
        raise RuntimeError(
            "Freerouting JAR checksum mismatch: "
            f"expected {REQUIRED_FREEROUTING_SHA256}, got {jar_hash}"
        )

    board = pcbnew.LoadBoard(str(board_path))

    with tempfile.TemporaryDirectory(prefix="delta-omega-route-") as temp:
        dsn_path = Path(temp) / f"{board_path.stem}.dsn"
        ses_path = Path(temp) / f"{board_path.stem}.ses"

        if not pcbnew.ExportSpecctraDSN(board, str(dsn_path)):
            raise RuntimeError("KiCad could not export Specctra DSN")

        command = [str(java_path), "-jar", str(jar_path)]
        subprocess.run(
            command
            + [
                "-de",
                str(dsn_path),
                "-do",
                str(ses_path),
                "--router.autorouter.max_passes",
                str(args.passes),
                "-mt",
                str(args.threads),
                "-l",
                "en",
            ],
            check=True,
        )

        if not ses_path.exists():
            raise RuntimeError("Freerouting did not create a session file")
        if not pcbnew.ImportSpecctraSES(board, str(ses_path)):
            raise RuntimeError("KiCad could not import Specctra session")

    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(str(board_path), board)
    print(f"routed {board_path}")


if __name__ == "__main__":
    main()
