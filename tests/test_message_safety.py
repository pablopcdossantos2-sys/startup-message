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
        self._typing = []
        self.items_label = None
        self.typing_label = None
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



class RecordingLabel:
    def __init__(self):
        self.text = ""

    def configure(self, **kwargs):
        self.text = kwargs.get("text", self.text)


class SimpleTranslator:
    def t(self, key, **kwargs):
        return key.format(**kwargs) if kwargs else key


def test_typing_only_cannot_unlock_until_timer_and_all_exact_answers():
    from dailymessage import retype

    class View:
        def __init__(self):
            self.time_done = False
            self._emergency_released = False
            self.locked = True
            self.vars = []
            self.items_label = None
            self.typing_label = RecordingLabel()
            self.status = RecordingLabel()
            self.tr = SimpleTranslator()
            self.accent = "accent"
            self.answers = ["", ""]
            self._typing = [
                (lambda i=i: self.answers[i], value, RecordingLabel())
                for i, value in enumerate(["Regra de ouro", "Texto\ncompleto"])
            ]
            self.states = []

        def _set_locked(self, value):
            self.locked = value
            self.states.append(value)

        def _release_on_failure(self):
            raise AssertionError("A transcrição não pode cair no watchdog")

    view = View()
    MessageView._refresh(view)
    assert view.locked
    view.answers = ["Regra de ouro", "Texto\ncompleto"]
    MessageView._refresh(view)
    assert view.locked  # Tempo continua obrigatório.
    view.time_done = True
    MessageView._refresh(view)
    assert not view.locked
    assert view.typing_label.text == "msg.typing_progress"
    view.answers[0] = "Regra de Ouro"
    MessageView._refresh(view)
    assert view.locked  # Alterar uma letra depois da confirmação revoga a liberação.


def test_retyping_and_checklist_are_both_mandatory():
    class Checkbox:
        def __init__(self):
            self.checked = False
        def get(self):
            return self.checked

    class View:
        def __init__(self):
            self.time_done = True
            self._emergency_released = False
            self.locked = True
            self.vars = [Checkbox()]
            self.items_label = RecordingLabel()
            self.typing_label = RecordingLabel()
            self.status = RecordingLabel()
            self.tr = SimpleTranslator()
            self.accent = "accent"
            self.answer = "regra"
            self._typing = [(lambda: self.answer, "regra", RecordingLabel())]
        def _set_locked(self, state):
            self.locked = state
        def _release_on_failure(self):
            raise AssertionError("Não deveria falhar")

    view = View()
    MessageView._refresh(view)
    assert view.locked
    view.vars[0].checked = True
    MessageView._refresh(view)
    assert not view.locked
    view.answer = ""
    MessageView._refresh(view)
    assert view.locked
