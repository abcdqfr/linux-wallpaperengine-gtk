from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "linux-wallpaperengine-gtk.py"


def _get_class_function(tree: ast.AST, class_name: str, fn_name: str) -> ast.FunctionDef:
    for node in getattr(tree, "body", []):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == fn_name:
                    return item
    raise AssertionError(f"Could not find {class_name}.{fn_name}() in {MAIN}")


def _contains_settings_dialog_close(fn: ast.FunctionDef) -> bool:
    """
    Guard rail: quitting should break SettingsDialog.run() modal loops by closing
    an open dialog referenced by self._settings_dialog.
    """
    # We accept either dlg = getattr(self, "_settings_dialog", None) or direct uses.
    # Required evidence:
    # - references _settings_dialog somewhere in _quit_now
    # - calls response(...) AND destroy() (best-effort close)
    saw_attr = False
    saw_response = False
    saw_destroy = False

    for node in ast.walk(fn):
        if isinstance(node, ast.Constant) and node.value == "_settings_dialog":
            saw_attr = True
        if isinstance(node, ast.Attribute) and node.attr == "_settings_dialog":
            saw_attr = True
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "response":
                saw_response = True
            elif node.func.attr == "destroy":
                saw_destroy = True

    return saw_attr and saw_response and saw_destroy


def _contains_settings_dialog_tracking(fn: ast.FunctionDef) -> bool:
    """
    Guard rail: opening Settings should stash a reference on self so quit can close it.
    """
    for node in ast.walk(fn):
        if isinstance(node, ast.Attribute) and node.attr == "_settings_dialog":
            return True
    return False


def test_quit_closes_open_settings_dialog():
    tree = ast.parse(MAIN.read_text(encoding="utf-8"))
    fn = _get_class_function(tree, "WallpaperWindow", "_quit_now")
    assert _contains_settings_dialog_close(fn), (
        "Expected WallpaperWindow._quit_now() to close an open settings dialog "
        "via response(...) + destroy() on self._settings_dialog (prevents quit hang)."
    )


def test_opening_settings_tracks_dialog_for_quit():
    tree = ast.parse(MAIN.read_text(encoding="utf-8"))
    fn = _get_class_function(tree, "WallpaperWindow", "on_settings_clicked")
    assert _contains_settings_dialog_tracking(fn), (
        "Expected WallpaperWindow.on_settings_clicked() to assign self._settings_dialog "
        "so quit can break the modal loop."
    )
