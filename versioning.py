"""Versionamento MSIX e validação de tags para a Microsoft Store (stdlib apenas)."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

SOURCE = Path(__file__).resolve().parent / "src" / "dailymessage" / "__init__.py"
VERSION_PATTERN = re.compile(r'(?m)^__version__\s*=\s*"([^"]+)"\s*$')
SEMVER_PATTERN = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+")


def read_version(path: Path = SOURCE) -> str:
    match = VERSION_PATTERN.search(path.read_text(encoding="utf-8"))
    if not match:
        raise ValueError("Não foi encontrado __version__ no código do aplicativo.")
    return match.group(1)


def msix_version(version: str) -> str:
    """Valida X.Y.Z e retorna X.Y.Z.0, como exigido para pacotes da Store."""
    if not SEMVER_PATTERN.fullmatch(version):
        raise ValueError("Use __version__ no formato X.Y.Z, sem sufixos.")
    parts = tuple(int(part) for part in version.split("."))
    if not all(0 <= part <= 65535 for part in parts) or parts[0] == 0:
        raise ValueError("Cada componente MSIX deve caber em 0..65535; major deve ser maior que zero.")
    return ".".join(str(part) for part in parts) + ".0"


def validate_tag(version: str, tag: str) -> None:
    if tag != "v" + version:
        raise ValueError(f"Tag {tag!r} não corresponde a __version__={version!r}; esperado v{version}.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validar e imprimir a versão MSIX.")
    parser.add_argument("--tag", help="Tag Git obrigatória (vX.Y.Z)")
    args = parser.parse_args()
    version = read_version()
    rendered = msix_version(version)
    if args.tag:
        validate_tag(version, args.tag)
    print(rendered)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError) as exc:
        raise SystemExit(f"ERRO de versão: {exc}") from exc
