"""Regressões da geometria, modo de inicialização e identidade MSIX."""
from __future__ import annotations

import ctypes
import sys
from types import SimpleNamespace

from dailymessage import app, uiutil, winapi


def test_launch_detection_respects_flags(monkeypatch):
    monkeypatch.setattr(sys, "executable", r"C:\\Apps\\StartupMessageRunner.exe")
    assert app._is_startup_launch([])
    assert not app._is_startup_launch(["--settings"])
    monkeypatch.setattr(sys, "executable", r"C:\\Apps\\StartupMessage.exe")
    assert app._is_startup_launch(["--startup"])
    assert not app._is_startup_launch([])


class FakeWindow:
    def __init__(self):
        self.position = ""
        self.size = ""
        self.minimum = None

    def _get_window_scaling(self):
        return 1.0

    def winfo_screenwidth(self):
        return 1920

    def winfo_screenheight(self):
        return 1080

    def geometry(self, value):
        self.size = value

    def minsize(self, width, height):
        self.minimum = (width, height)

    def wm_geometry(self, value):
        self.position = value


def test_fits_inside_work_area(monkeypatch):
    monkeypatch.setattr(winapi, "primary_work_area", lambda: (0, 0, 1920, 1040))
    win = FakeWindow()
    uiutil.fit_and_center(win, 640, 2000, fill_height_for_large=True)
    assert win.size == "640x1040"
    assert win.position == "+640+0"


def test_package_api_errors_not_treated_as_packaged(monkeypatch):
    monkeypatch.setattr(winapi, "IS_WINDOWS", True)
    for code, expected in ((15700, False), (87, False), (0, True), (122, True)):
        fake = SimpleNamespace(kernel32=SimpleNamespace(
            GetCurrentPackageFullName=lambda length, buffer, code=code: code
        ))
        monkeypatch.setattr(ctypes, "windll", fake, raising=False)
        assert winapi.is_packaged() is expected


class FakeWinFunction:
    def __init__(self, return_value):
        self.return_value = return_value
        self.calls = []

    def __call__(self, *args):
        self.calls.append(args)
        return self.return_value


class FakeUser32:
    def __init__(self, minimized):
        self.FindWindowW = FakeWinFunction(123)
        self.IsIconic = FakeWinFunction(minimized)
        self.ShowWindow = FakeWinFunction(1)
        self.SetForegroundWindow = FakeWinFunction(1)


def test_activating_existing_maximized_window_keeps_its_size(monkeypatch):
    monkeypatch.setattr(winapi, "IS_WINDOWS", True)
    u = FakeUser32(minimized=False)
    monkeypatch.setattr(winapi, "_u32", lambda: u)
    assert winapi.activate_existing_settings()
    assert u.ShowWindow.calls == []
    assert u.SetForegroundWindow.calls == [(123,)]


def test_activating_minimized_window_restores_it(monkeypatch):
    monkeypatch.setattr(winapi, "IS_WINDOWS", True)
    u = FakeUser32(minimized=True)
    monkeypatch.setattr(winapi, "_u32", lambda: u)
    assert winapi.activate_existing_settings()
    assert u.ShowWindow.calls == [(123, winapi.SW_RESTORE)]


def test_bring_to_front_does_not_unmaximize(monkeypatch):
    monkeypatch.setattr(winapi, "IS_WINDOWS", True)
    u = FakeUser32(minimized=False)
    monkeypatch.setattr(winapi, "_u32", lambda: u)
    winapi.bring_to_front(123)
    assert not u.ShowWindow.calls
    assert u.SetForegroundWindow.calls == [(123,)]
