"""Regressões de transcrição, incluindo bloqueio de colagem."""
from dailymessage import retype


def test_exact_case_and_punctuation_are_required():
    assert retype.matches("Acordar às 7h!", "Acordar às 7h!")
    assert not retype.matches("Acordar às 7h!", "acordar às 7h!")
    assert not retype.matches("Acordar às 7h!", "Acordar às 7h")
    assert not retype.matches("Acordar às 7h!", " Acordar às 7h!")
    assert not retype.matches("Acordar às 7h!", "Acordar às 7h! ")
    assert not retype.matches("Acordar às 7h!", "")
    assert not retype.matches("", "")


def test_long_multiline_normalizes_only_newlines_and_unicode():
    expected = "Primeira linha\nCafe\u0301\nÚltima linha"
    assert retype.matches(expected, "Primeira linha\r\nCafé\r\nÚltima linha")
    assert not retype.matches(expected, "Primeira linha Café Última linha")
    assert not retype.matches(expected, "Primeira linha\nCafé\nÚltima linha\n")


class FakeWidget:
    def __init__(self):
        self.events = {}

    def bind(self, sequence, callback, add=None):
        assert add == "+"
        self.events[sequence] = callback


def test_all_paste_commands_are_blocked_for_retype_fields():
    w = FakeWidget()
    retype.prevent_paste(w)
    assert set(w.events) == set(retype.PASTE_EVENTS)
    assert all(callback(object()) == "break" for callback in w.events.values())
