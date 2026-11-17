"""Comparação rigorosa de transcrições e bloqueio de colagem nos campos de resposta.

A origem do texto é exibida em CTkLabel não selecionável. Os campos de
resposta não oferecem comando de colagem de clipboard ou seleção primária.
Não constitui proteção contra automação externa que simule teclas.
"""
from __future__ import annotations

import unicodedata

PASTE_EVENTS = (
    "<<Paste>>",
    "<<PasteSelection>>",
    "<Control-KeyPress-v>",
    "<Control-KeyPress-V>",
    "<Control-Shift-KeyPress-v>",
    "<Control-Shift-KeyPress-V>",
    "<Shift-KeyPress-Insert>",
    "<Shift-KeyPress-F10>",  # Menu de contexto pelo teclado.
    "<KeyPress-Menu>",  # Tecla de menu contextual do Windows.
    "<Button-2>",  # Colagem por seleção primária.
    "<Button-3>",  # Evita menu de contexto com opção Colar.
)


def matches(expected: str, entered: str) -> bool:
    """Exige texto integral exato (maiúsculas, pontuação e espaçamento).

    Apenas formas Unicode canonicamente equivalentes e CRLF/LF são equiparadas,
    permitindo acentos digitados por diferentes teclados e quebra de linha do Tk.
    """
    def canonical(value: str) -> str:
        return unicodedata.normalize("NFC", value.replace("\r\n", "\n").replace("\r", "\n"))

    return bool(expected) and canonical(entered) == canonical(expected)


def prevent_paste(widget) -> None:
    """Bloqueia os atalhos e eventos Tk de colar; não interfere na digitação."""
    for sequence in PASTE_EVENTS:
        widget.bind(sequence, lambda _event: "break", add="+")
