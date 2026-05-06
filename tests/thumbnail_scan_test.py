from __future__ import annotations

from pathlib import Path

from thumbnail_scan import scan_item_root


def _touch(p: Path, size: int = 1) -> None:
    p.write_bytes(b"x" * size)


def test_scan_item_root_ok_preview_jpg(tmp_path: Path):
    d = tmp_path / "123"
    d.mkdir()
    _touch(d / "preview.jpg", 10)
    r = scan_item_root(d)
    assert r.preview_candidates == ("preview.jpg",)
    assert "preview_wrong_extension" not in r.suspicious
    assert "preview_zero_bytes" not in r.suspicious


def test_scan_item_root_preview_wrong_extension(tmp_path: Path):
    d = tmp_path / "123"
    d.mkdir()
    _touch(d / "preview.bmp", 10)
    r = scan_item_root(d)
    assert "preview_wrong_extension" in r.suspicious


def test_scan_item_root_preview_zero_bytes(tmp_path: Path):
    d = tmp_path / "123"
    d.mkdir()
    _touch(d / "preview.jpg", 0)
    r = scan_item_root(d)
    assert "preview_zero_bytes" in r.suspicious


def test_scan_item_root_no_preview_but_has_images(tmp_path: Path):
    d = tmp_path / "123"
    d.mkdir()
    _touch(d / "something.png", 10)
    r = scan_item_root(d)
    assert "no_preview_named_file" in r.suspicious
    assert "no_preview_but_has_images" in r.suspicious


def test_scan_item_root_preview_is_directory(tmp_path: Path):
    d = tmp_path / "123"
    d.mkdir()
    (d / "preview.jpg").mkdir()
    r = scan_item_root(d)
    assert "preview_not_a_file" in r.suspicious
