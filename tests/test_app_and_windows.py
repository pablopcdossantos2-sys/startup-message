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
