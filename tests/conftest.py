"""Shared pytest fixtures for validate_schema and frontmatter tests."""

from __future__ import annotations

import sys
import pathlib

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))


@pytest.fixture
def md_file(tmp_path):
    """Create a markdown file with given content. Returns pathlib.Path."""

    def _create(content, name="test.md"):
        p = tmp_path / name
        p.write_text(content)
        return p

    return _create


@pytest.fixture(autouse=True)
def _clear_validate_schema_caches():
    """Defensive: clear lru_caches in validate_schema between tests.

    Prevents a test that re-writes a schema at the same tmp_path from
    seeing stale cached schema content from a prior test.
    """
    yield
    try:
        import validate_schema  # noqa: PLC0415

        validate_schema._load_schema_cached.cache_clear()
    except (ImportError, AttributeError):
        pass  # validate_schema not yet imported in this test session
