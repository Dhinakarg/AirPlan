"""Markdown documentation and link resolution compliance test suite."""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
EXCLUDED_DIRS = {".venv", ".pytest_cache", "node_modules", ".git"}


def _get_tracked_markdown_files() -> list[Path]:
    """Retrieve all tracked repository markdown documentation files.

    Returns:
        List of Path objects for all tracked markdown documents.
    """
    return [
        p
        for p in REPO_ROOT.rglob("*.md")
        if not any(excluded in p.parts for excluded in EXCLUDED_DIRS)
    ]


def test_markdown_files_have_no_file_uri_or_drive_letters() -> None:
    """Assert zero usage of file:// URIs or absolute drive-letter paths in markdown docs."""
    md_files = _get_tracked_markdown_files()
    assert len(md_files) >= 5, f"Expected at least 5 markdown files, found {len(md_files)}"

    violations: list[str] = []
    for md_file in md_files:
        content = md_file.read_text(encoding="utf-8")
        rel_path = md_file.relative_to(REPO_ROOT)
        if "file://" in content:
            violations.append(f"{rel_path}: contains forbidden 'file://' URI")
        if re.search(r"\b[A-Za-z]:[/\\]", content):
            violations.append(f"{rel_path}: contains forbidden drive-letter absolute path")

    assert not violations, "Markdown path violations found:\n" + "\n".join(violations)


def test_markdown_relative_links_resolve_to_existing_files() -> None:
    """Assert all relative markdown links resolve to existing files or directories."""
    md_files = _get_tracked_markdown_files()
    assert len(md_files) >= 5

    broken_links: list[str] = []
    for md_file in md_files:
        content = md_file.read_text(encoding="utf-8")
        rel_path = md_file.relative_to(REPO_ROOT)
        links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", content)

        for text, href in links:
            if href.startswith(("http://", "https://", "mailto:", "#")):
                continue
            clean_href = href.split("#")[0]
            if not clean_href:
                continue

            target_path = (md_file.parent / clean_href).resolve()
            repo_target = (REPO_ROOT / clean_href.lstrip("/")).resolve()

            if not target_path.exists() and not repo_target.exists():
                broken_links.append(f"{rel_path}: link [{text}]({href}) cannot be resolved")

    assert not broken_links, "Broken markdown links found:\n" + "\n".join(broken_links)
