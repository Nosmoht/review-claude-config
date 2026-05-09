import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "bin" / "repo-slug.sh"


def slug(target: str) -> str:
    result = subprocess.run(
        ["bash", str(SCRIPT), target],
        capture_output=True, text=True, check=True,
    )
    return result.stdout


def test_camelcase_lowercased():
    assert slug("/tmp/FlugFunkApp") == "flugfunkapp"


def test_kebab_preserved():
    assert slug("/tmp/review-claude-config") == "review-claude-config"


def test_uppercase_only():
    assert slug("/tmp/FOO") == "foo"


def test_trailing_slash():
    assert slug("/tmp/MyRepo/") == "myrepo"


def test_underscores_stripped():
    # Documented behavior: tr -cd strips _; my_repo and myrepo collide.
    # Risk acknowledged in repo-identification.md "Collision Detection".
    assert slug("/tmp/my_repo") == "myrepo"


def test_dots_stripped():
    assert slug("/tmp/my.repo") == "myrepo"


def test_already_canonical():
    assert slug("/tmp/flugfunkapp") == "flugfunkapp"


def test_default_to_cwd(tmp_path, monkeypatch):
    target = tmp_path / "TestRepo"
    target.mkdir()
    monkeypatch.chdir(target)
    result = subprocess.run(
        ["bash", str(SCRIPT)],  # no arg -> defaults to $(pwd)
        capture_output=True, text=True, check=True,
    )
    assert result.stdout == "testrepo"


def test_empty_after_sanitize_fails():
    # All-special-chars basename -> empty slug -> exit 1
    result = subprocess.run(
        ["bash", str(SCRIPT), "/tmp/!!!"],
        capture_output=True, text=True,
    )
    assert result.returncode == 1
    assert "empty slug" in result.stderr


def test_shell_metachar_no_injection(tmp_path):
    # Stronger form -- explicit assertion that the marker file is not created.
    marker = tmp_path / "repo-slug-injection-canary"
    target = f"/tmp/foo;touch {marker}"
    subprocess.run(
        ["bash", str(SCRIPT), target],
        capture_output=True, text=True,
    )
    assert not marker.exists(), "command injection occurred via $1"


def test_newline_in_basename():
    # Embedded newline in basename should not break the sanitize.
    # tr -cd 'a-z0-9-' strips \n; result is the alphanumeric remainder.
    target = "/tmp/foo\nbar"
    result = subprocess.run(
        ["bash", str(SCRIPT), target],
        capture_output=True, text=True, check=True,
    )
    assert result.stdout == "foobar"
