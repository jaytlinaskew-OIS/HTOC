import sys
from pathlib import Path

from htoc.core.bootstrap import ensure_htoc_on_path, find_htoc_src, htoc_src_dir


def test_htoc_src_dir_points_at_src_tree():
    src = htoc_src_dir()
    assert src.name == "src"
    assert (src / "htoc" / "core" / "bootstrap.py").is_file()


def test_find_htoc_src_from_repo_root():
    src = find_htoc_src(start=htoc_src_dir().parents[1])
    assert src == htoc_src_dir()


def test_ensure_htoc_on_path_is_idempotent():
    src = ensure_htoc_on_path()
    assert src.resolve() == htoc_src_dir().resolve()
    assert any(Path(entry).resolve() == src.resolve() for entry in sys.path)
    assert ensure_htoc_on_path().resolve() == src.resolve()
