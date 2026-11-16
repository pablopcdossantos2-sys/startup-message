"""Gera ícones PLACEHOLDER (substitua pela arte final antes de publicar na Store).

Uso: python packaging/make_assets.py [--force]
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
MSIX_ASSETS = ROOT / "packaging" / "Assets"
PLACEHOLDER_MARKER = ASSETS / "PLACEHOLDER_ASSETS.txt"
S = 1024


def master() -> Image.Image:
    top, bottom = (99, 102, 241), (139, 92, 246)
    grad = Image.new("RGB", (S, S))
    gd = ImageDraw.Draw(grad)
    for y in range(S):
        t = y / (S - 1)
        gd.line([(0, y), (S, y)], fill=tuple(round(top[i] * (1 - t) + bottom[i] * t) for i in range(3)))
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, S - 1, S - 1), radius=int(S * 0.22), fill=255)
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    img.paste(grad, (0, 0), mask)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((210, 250, 814, 654), radius=110, fill=(255, 255, 255, 255))
    d.polygon([(330, 640), (330, 780), (470, 650)], fill=(255, 255, 255, 255))
    for cx in (370, 512, 654):
        d.ellipse((cx - 38, 422, cx + 38, 498), fill=(99, 102, 241, 255))
    return img


def main() -> None:
    expected = [ASSETS / "icon.ico", ASSETS / "icon.png"]
    expected.extend(MSIX_ASSETS / f"{name}.png" for name in
                    ("StoreLogo", "Square44x44Logo", "Square71x71Logo",
                     "Square150x150Logo", "Square310x310Logo", "Wide310x150Logo"))
    present = [path.exists() for path in expected]
    if all(present) and "--force" not in sys.argv:
        print("Todos os assets já existem (use --force para sobrescrever).")
        return
    if any(present) and "--force" not in sys.argv:
        raise SystemExit(
            "Conjunto de ícones incompleto: forneça todos os arquivos finais "
            "ou use --force para gerar placeholders explicitamente."
        )
    ASSETS.mkdir(exist_ok=True)
    MSIX_ASSETS.mkdir(parents=True, exist_ok=True)
    img = master()
    img.save(ASSETS / "icon.png")
    img.save(ASSETS / "icon.ico", sizes=[(s, s) for s in (16, 24, 32, 48, 64, 128, 256)])
    sizes = {"StoreLogo": 50, "Square44x44Logo": 44, "Square71x71Logo": 71,
             "Square150x150Logo": 150, "Square310x310Logo": 310}
    for name, size in sizes.items():
        img.resize((size, size), Image.Resampling.LANCZOS).save(MSIX_ASSETS / f"{name}.png")
    wide = Image.new("RGBA", (310, 150), (0, 0, 0, 0))
    icon = img.resize((130, 130), Image.Resampling.LANCZOS)
    wide.paste(icon, ((310 - 130) // 2, 10), icon)
    wide.save(MSIX_ASSETS / "Wide310x150Logo.png")
    PLACEHOLDER_MARKER.write_text(
        "Ícones provisórios gerados automaticamente. "
        "Substitua-os pela arte final e remova este marcador apenas após aprovação.\n",
        encoding="utf-8",
    )
    print("Assets provisórios gerados: não enviar à Microsoft Store.")


def check_store_assets() -> None:
    """Rejeita conjunto incompleto e qualquer arte gerada por este script."""
    expected = [ASSETS / "icon.ico", ASSETS / "icon.png"]
    expected.extend(MSIX_ASSETS / f"{name}.png" for name in
                    ("StoreLogo", "Square44x44Logo", "Square71x71Logo",
                     "Square150x150Logo", "Square310x310Logo", "Wide310x150Logo"))
    missing = [path.name for path in expected if not path.is_file()]
    if missing:
        raise ValueError("Arquivos de identidade visual ausentes: " + ", ".join(missing))
    if PLACEHOLDER_MARKER.exists():
        raise ValueError("Ícones provisórios detectados: aprovação de arte final pendente.")
    for path in expected:
        try:
            with Image.open(path) as img:
                img.verify()
        except (OSError, ValueError) as exc:
            raise ValueError(f"Ícone inválido: {path.name}") from exc
    # O marcador pode ser apagado por engano; confira também o desenho padrão.
    with Image.open(ASSETS / "icon.png") as icon:
        if icon.convert("RGBA").size == (S, S):
            if icon.convert("RGBA").tobytes() == master().tobytes():
                raise ValueError("O icon.png ainda é o placeholder gerado automaticamente.")
    print("Assets estruturais conferidos. Aprovação humana continua necessária.")


if __name__ == "__main__":
    if "--check-store" in sys.argv:
        try:
            check_store_assets()
        except ValueError as exc:
            raise SystemExit(f"ARTE NÃO APROVADA: {exc}") from exc
    else:
        main()
