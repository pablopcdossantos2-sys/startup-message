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
        self._emergency_released = False
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


class EmergencyWindow:
    def __init__(self):
        self.destroyed = False
        self.close_handler = None

    def protocol(self, _name, handler):
        self.close_handler = handler

    def attributes(self, *_args):
        pass

    def destroy(self):
        self.destroyed = True


class EmergencyButton:
    def __init__(self, broken=False):
        self.broken = broken
        self.state = "disabled"

    def configure(self, **kwargs):
        if self.broken:
            raise RuntimeError("Botão indisponível")
        self.state = kwargs.get("state", self.state)


class ChecklistVar:
    def __init__(self, checked=False):
        self.checked = checked

    def get(self):
        return self.checked


def emergency_view(*, broken_button=False):
    view = FakeMessageView()
    view.win = EmergencyWindow()
    view.ok = EmergencyButton(broken=broken_button)
    view.accent = "#000000"
    view.accent_hover = "#111111"
    view.locked = True
    view.tr = BrokenTranslator()
    return view


def test_emergency_release_cannot_relock_after_checklist_event(monkeypatch):
    from dailymessage import winapi
    monkeypatch.setattr(winapi, "IS_WINDOWS", False)
    view = emergency_view()
    MessageView._release_on_failure(view)
    assert view.time_done
    assert not view.locked
    assert view._emergency_released
    assert view.ok.state == "normal"
    assert view.win.close_handler is not None

    # Item obrigatório ainda pendente: _refresh e _set_locked não podem reativar o bloqueio.
    view.vars = [ChecklistVar(False)]
    MessageView._refresh(view)
    MessageView._set_locked(view, True)
    MessageView._tick(view)
    assert view._emergency_released
    assert not view.locked
    assert view.ok.state == "normal"


def test_emergency_release_closes_window_if_button_cannot_be_restored(monkeypatch):
    from dailymessage import winapi
    monkeypatch.setattr(winapi, "IS_WINDOWS", False)
    view = emergency_view(broken_button=True)
    MessageView._release_on_failure(view)
    assert view.win.destroyed
    assert view._emergency_released
    assert not view.locked
