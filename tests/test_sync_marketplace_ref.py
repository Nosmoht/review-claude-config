"""Unit tests for `scripts/sync_marketplace_ref.py`.

The script propagates `plugin.json#version` to two fields in
`marketplace.json` while preserving the file's hand-formatted style.
Each test sets up an isolated temp dir as CWD, populates the two
fixture files, runs the script's `main()`, and asserts on the
post-write file content."""

from __future__ import annotations

import json
import pathlib
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))


PLUGIN_FIXTURE = """{
  "name": "claude-config",
  "version": "__VERSION__",
  "description": "demo"
}
"""

MARKETPLACE_FIXTURE = """{
  "name": "ntbc-plugins",
  "owner": { "name": "ntbc", "email": "demo@example.com" },
  "metadata": {
    "description": "Personal Claude Code plugin catalog",
    "version": "1.0.0"
  },
  "plugins": [
    {
      "name": "claude-config",
      "source": {
        "source": "github",
        "repo": "Nosmoht/review-claude-config",
        "ref": "__REF__"
      },
      "description": "demo",
      "version": "__VERSION__",
      "category": "review",
      "tags": ["review", "audit", "quality"]
    }
  ]
}
"""


def _render_plugin(version: str) -> str:
    return PLUGIN_FIXTURE.replace("__VERSION__", version)


def _render_marketplace(version: str, ref: str) -> str:
    return MARKETPLACE_FIXTURE.replace("__VERSION__", version).replace(
        "__REF__", ref
    )


def _setup_files(
    tmp_path: pathlib.Path,
    plugin_version: str,
    marketplace_version: str,
    marketplace_ref: str,
) -> None:
    plugin_dir = tmp_path / ".claude-plugin"
    plugin_dir.mkdir()
    (plugin_dir / "plugin.json").write_text(
        _render_plugin(plugin_version), encoding="utf-8"
    )
    (plugin_dir / "marketplace.json").write_text(
        _render_marketplace(marketplace_version, marketplace_ref), encoding="utf-8"
    )


def _run(monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> int:
    monkeypatch.chdir(tmp_path)
    import sync_marketplace_ref

    return sync_marketplace_ref.main()


def _read_marketplace(tmp_path: pathlib.Path) -> dict:
    return json.loads(
        (tmp_path / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8")
    )


class TestSync:
    def test_idempotent_on_synced_state(
        self,
        tmp_path: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _setup_files(
            tmp_path,
            plugin_version="2.1.0",
            marketplace_version="2.1.0",
            marketplace_ref="v2.1.0",
        )

        rc = _run(monkeypatch, tmp_path)

        assert rc == 0
        assert "already in sync" in capsys.readouterr().out

    def test_bumps_stable_minor_version(
        self, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _setup_files(
            tmp_path,
            plugin_version="2.2.0",
            marketplace_version="2.1.0",
            marketplace_ref="v2.1.0",
        )

        rc = _run(monkeypatch, tmp_path)
        data = _read_marketplace(tmp_path)

        assert rc == 0
        assert data["plugins"][0]["version"] == "2.2.0"
        assert data["plugins"][0]["source"]["ref"] == "v2.2.0"

    def test_bumps_prerelease_version(
        self, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _setup_files(
            tmp_path,
            plugin_version="3.0.0-rc.1",
            marketplace_version="2.1.0",
            marketplace_ref="v2.1.0",
        )

        rc = _run(monkeypatch, tmp_path)
        data = _read_marketplace(tmp_path)

        assert rc == 0
        assert data["plugins"][0]["version"] == "3.0.0-rc.1"
        assert data["plugins"][0]["source"]["ref"] == "v3.0.0-rc.1"

    def test_bumps_build_metadata_version(
        self, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _setup_files(
            tmp_path,
            plugin_version="2.2.0+build.5",
            marketplace_version="2.1.0",
            marketplace_ref="v2.1.0",
        )

        rc = _run(monkeypatch, tmp_path)
        data = _read_marketplace(tmp_path)

        assert rc == 0
        assert data["plugins"][0]["version"] == "2.2.0+build.5"
        assert data["plugins"][0]["source"]["ref"] == "v2.2.0+build.5"

    def test_preserves_metadata_version(
        self, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The marketplace-catalog version (metadata.version="1.0.0") must NEVER
        be touched, even when plugin.version is bumped."""
        _setup_files(
            tmp_path,
            plugin_version="9.9.9",
            marketplace_version="2.1.0",
            marketplace_ref="v2.1.0",
        )

        _run(monkeypatch, tmp_path)
        data = _read_marketplace(tmp_path)

        assert data["metadata"]["version"] == "1.0.0"

    def test_preserves_inline_format(
        self, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Inline `tags: [...]` and `owner: { ... }` arrays/objects must remain
        single-line — that's the whole point of the regex-targeted approach."""
        _setup_files(
            tmp_path,
            plugin_version="2.2.0",
            marketplace_version="2.1.0",
            marketplace_ref="v2.1.0",
        )

        _run(monkeypatch, tmp_path)
        text = (tmp_path / ".claude-plugin" / "marketplace.json").read_text(
            encoding="utf-8"
        )

        assert '"owner": { "name": "ntbc", "email": "demo@example.com" }' in text
        assert '"tags": ["review", "audit", "quality"]' in text


class TestFailure:
    def test_fails_on_missing_plugin_json(
        self,
        tmp_path: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        plugin_dir = tmp_path / ".claude-plugin"
        plugin_dir.mkdir()
        (plugin_dir / "marketplace.json").write_text(
            _render_marketplace("2.1.0", "v2.1.0"), encoding="utf-8"
        )

        rc = _run(monkeypatch, tmp_path)

        assert rc == 1
        assert "required file missing" in capsys.readouterr().err

    def test_fails_on_missing_marketplace_json(
        self,
        tmp_path: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        plugin_dir = tmp_path / ".claude-plugin"
        plugin_dir.mkdir()
        (plugin_dir / "plugin.json").write_text(
            _render_plugin("2.1.0"), encoding="utf-8"
        )

        rc = _run(monkeypatch, tmp_path)

        assert rc == 1
        assert "required file missing" in capsys.readouterr().err

    def test_fails_on_missing_source_ref_field(
        self,
        tmp_path: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Structural drift: someone removed source.ref from marketplace.json.
        The script must fail loudly (n_subs == 0) instead of silently passing."""
        _setup_files(
            tmp_path,
            plugin_version="2.2.0",
            marketplace_version="2.1.0",
            marketplace_ref="v2.1.0",
        )
        marketplace_path = tmp_path / ".claude-plugin" / "marketplace.json"
        broken = marketplace_path.read_text(encoding="utf-8").replace(
            '"ref": "v2.1.0"', '"branch": "main"'
        )
        marketplace_path.write_text(broken, encoding="utf-8")

        rc = _run(monkeypatch, tmp_path)

        assert rc == 1
        assert "structural drift" in capsys.readouterr().err

    def test_fails_on_missing_plugins_array(
        self,
        tmp_path: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """If marketplace.json has no top-level `plugins` array, the script
        cannot locate the version field and must fail."""
        plugin_dir = tmp_path / ".claude-plugin"
        plugin_dir.mkdir()
        (plugin_dir / "plugin.json").write_text(
            _render_plugin("2.2.0"), encoding="utf-8"
        )
        (plugin_dir / "marketplace.json").write_text(
            json.dumps({"name": "demo", "metadata": {"version": "1.0.0"}}, indent=2),
            encoding="utf-8",
        )

        rc = _run(monkeypatch, tmp_path)

        assert rc == 1
        assert "cannot locate 'plugins' array" in capsys.readouterr().err
