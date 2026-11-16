"""Regressões do bloqueio da janela; sem criar instância Tk."""
from __future__ import annotations

from dailymessage.message_window import MessageView


class BrokenLabel:
    def configure(self, **kwargs):
        raise RuntimeError("Falha na atualização do widget")


class FakeMessageView:
    def __init__(self):
        self._end = -1
        self.total = 1
        self.time_done = False
        self._shown = None
        self.bar = BrokenLabel()
        self.clock = BrokenLabel()
        self.vars = []
        self.items_label = None
        self.released = False

    def winfo_exists(self):
        return True

    def _release_on_failure(self):
        self.released = True

    def _refresh(self):
        return MessageView._refresh(self)


class BrokenTranslator:
    def t(self, key):
        raise RuntimeError("Falha de tradução")


def test_tick_releases_on_widget_failure():
    view = FakeMessageView()
    MessageView._tick(view)
    assert view.released
    assert view.time_done


def test_refresh_releases_on_translation_failure():
    view = FakeMessageView()
    view.tr = BrokenTranslator()
    MessageView._refresh(view)
    assert view.released
