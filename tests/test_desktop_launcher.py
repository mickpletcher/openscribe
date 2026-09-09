from pathlib import Path

from openscribe.cli import desktop
from openscribe.desktop_launcher import build_parser, main, run


def test_desktop_launcher_forwards_project(monkeypatch, tmp_path: Path) -> None:
    opened = []
    monkeypatch.setattr("openscribe.desktop.launch", opened.append)

    assert main(["--project", str(tmp_path)]) == 0
    assert opened == [tmp_path]


def test_desktop_launcher_smoke_test_does_not_open_window(monkeypatch) -> None:
    opened = []
    monkeypatch.setattr("openscribe.desktop.launch", opened.append)

    assert main(["--smoke-test"]) == 0
    assert opened == []


def test_desktop_launcher_help_names_project_option() -> None:
    assert "--project" in build_parser().format_help()


def test_desktop_launcher_smoke_failure_returns_nonzero(monkeypatch, tmp_path: Path) -> None:
    def fail(_argv):
        raise RuntimeError("broken desktop")

    monkeypatch.setattr("openscribe.desktop_launcher.main", fail)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))

    assert run(["--smoke-test"]) == 1
    assert "broken desktop" in (tmp_path / "OpenScribe" / "openscribe-error.log").read_text(encoding="utf-8")


def test_packaged_cli_launches_sibling_desktop(monkeypatch, tmp_path: Path) -> None:
    cli = tmp_path / "openscribe-cli.exe"
    packaged_desktop = tmp_path / "OpenScribe.exe"
    packaged_desktop.touch()
    launched = []
    monkeypatch.setattr("openscribe.cli.sys.frozen", True, raising=False)
    monkeypatch.setattr("openscribe.cli.sys.executable", str(cli))
    monkeypatch.setattr("openscribe.cli.subprocess.Popen", launched.append)

    desktop(tmp_path / "project")

    assert launched == [[str(packaged_desktop), "--project", str(tmp_path / "project")]]
