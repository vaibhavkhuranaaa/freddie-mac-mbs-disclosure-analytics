#!/usr/bin/env python3
"""Bootstrap and validate a portable evidence-led project repository."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


KIT_ROOT = Path(__file__).resolve().parents[1]
SIGNATURE_FILE = ".project/graph-source.sha256"


@dataclass(frozen=True)
class Charter:
    title: str
    slug: str
    category: str
    industry: str
    data_boundary: str
    first_demo: str
    public_target: str


def field(markdown: str, label: str) -> str:
    match = re.search(rf"^[-*]\s*\*\*{re.escape(label)}:\*\*\s*(.+)$", markdown, re.MULTILINE)
    return match.group(1).strip() if match else ""


def slugify(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return re.sub(r"-{2,}", "-", value)


def category_slug(value: str) -> str:
    normalized = slugify(value)
    aliases = {
        "data-science-analytics": "analytics",
        "data-science-analytics-data-science": "analytics",
        "analytics": "analytics",
        "business-intelligence": "business-intelligence",
        "ai": "ai",
        "engineering": "data-engineering",
        "data-engineering": "data-engineering",
        "full-stack": "full-stack",
    }
    return aliases.get(normalized, normalized)


def parse_charter(path: Path) -> Charter:
    markdown = path.read_text(encoding="utf-8")
    title_match = re.search(r"^#\s+(.+)$", markdown, re.MULTILINE)
    if not title_match:
        raise ValueError("Charter needs a top-level # title.")
    title = title_match.group(1).strip()
    category_industry = field(markdown, "Category / industry")
    if not category_industry or "/" not in category_industry:
        raise ValueError("Charter needs '**Category / industry:** <category> / <industry>'.")
    raw_category, industry = (part.strip() for part in category_industry.split("/", 1))
    public_target = field(markdown, "Public URL target")
    target_match = re.search(r"/projects/([a-z0-9-]+)", public_target)
    slug = target_match.group(1) if target_match else slugify(title)
    data_boundary = field(markdown, "Data classification") or "Not yet specified"
    first_demo = field(markdown, "First-demo workflow") or field(markdown, "Demo status") or "Define the first representative workflow"
    return Charter(title, slug, category_slug(raw_category), industry, data_boundary, first_demo, public_target)


def render(template: str, charter: Charter) -> str:
    values = {
        "TITLE": charter.title,
        "SLUG": charter.slug,
        "CATEGORY": charter.category,
        "INDUSTRY": charter.industry,
        "DATA_BOUNDARY": charter.data_boundary,
        "FIRST_DEMO": charter.first_demo,
        "PUBLIC_TARGET": charter.public_target or f"/projects/{charter.slug}",
    }
    for key, value in values.items():
        template = template.replace(f"{{{{{key}}}}}", value)
    return template


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def run(command: list[str], cwd: Path) -> None:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    if result.returncode:
        message = result.stderr.strip() or result.stdout.strip() or "command failed"
        raise RuntimeError(f"{' '.join(command)}: {message}")


def copy_adapter(source: str, destination: Path) -> None:
    write(destination, (KIT_ROOT / "adapters" / source).read_text(encoding="utf-8"))


def project_files(charter: Charter) -> dict[str, str]:
    architecture = f"""# Architecture decision\n\n## Approved status\n\n- Status: `draft — human approval required`\n- Initial delivery: local-first\n- Cloud authority: none\n\n## Project\n\n- Title: {charter.title}\n- Category / industry: {charter.category} / {charter.industry}\n- Data boundary: {charter.data_boundary}\n- First demo: {charter.first_demo}\n\n## Options to compare before approval\n\n| Option | Cost | Use now? | Scale trigger |\n| --- | --- | --- | --- |\n| Local native or Docker Compose | $0 | Recommended baseline | None; use for first demo |\n| Vercel or comparable web host | Low | Only for a static/web-only shareable demo | Recruiter-facing interactive UI |\n| Azure or AWS container path | Variable | Only with approval | Persistent API, scheduled work, or multiple users |\n| Warehouse/lakehouse | Variable | Not a baseline dependency | Demonstrated volume, governance, or warehouse need |\n\n## Honest public wording\n\nDescribe scalable alternatives as planned architecture until they are deployed and verified.\n"""
    milestones = f"""version: 1\nproject: {charter.slug}\nstatus: planned\nmilestones:\n  - id: M1\n    title: Define data and baseline\n    status: unblocked\n    acceptance:\n      - Document the representative data boundary.\n      - Add a reproducible baseline and versioned evaluation inputs.\n  - id: M2\n    title: Build one end-to-end local workflow\n    status: blocked_by_M1\n    acceptance:\n      - A reviewer can complete the first-demo workflow locally.\n      - UI/API states are clear and safe.\n  - id: M3\n    title: Prove quality and first-demo readiness\n    status: blocked_by_M2\n    acceptance:\n      - Tests, evaluation, documentation, architecture, cost, and limitations are current.\n  - id: M4\n    title: Decide deployment\n    status: blocked_by_M3\n    acceptance:\n      - Human approves provider, cost, exposure, and teardown when deployment is useful.\n  - id: M5\n    title: Verify and publish\n    status: blocked_by_M4\n    acceptance:\n      - Deployed revision proves its exact source SHA.\n      - Public facts link to verified evidence.\n"""
    return {
        "README.md": f"# {charter.title}\n\nStatus: planned. This repository starts from a local-first, evidence-led delivery plan.\n\n## Project\n\n- Decision owner: define in `PROJECT.md`.\n- Data boundary: {charter.data_boundary}\n- First demo: {charter.first_demo}\n\nRead `AGENTS.md` and `.project/` before contributing.\n",
        "AGENTS.md": f"# Project delivery rules\n\n## Read first\n\nRead `PROJECT.md`, `.project/architecture.md`, `.project/milestones.yml`, `.project/state.md`, and `.project/handoff.md` before editing. Complete only the first unblocked milestone.\n\n## Rules\n\n- Preserve unrelated work and never overwrite existing files without instruction.\n- Use public, synthetic, anonymized, or licensed data only: {charter.data_boundary}\n- Use the smallest credible design; remove stale code and unjustified abstractions.\n- Apply `DESIGN.md` to all user-facing work.\n- Keep secrets outside source; commit variable names only in `.env.example`.\n- Use conventional commits and configured human Git identity. Never add AI/model author or co-author trailers.\n- Do not put AI/model names in Git branch names.\n- Do not create paid resources, change public visibility, deploy, roll back, or publish without explicit human approval recorded in `.project/approvals.yml`.\n- Update architecture, evidence, state, and handoff when verified facts change.\n- Run `project-kit check` before claiming a milestone is complete.\n",
        "DESIGN.md": "# User-facing design rules\n\n- Use Impeccable/design-taste guidance for every screen, dashboard, demo, and public project page.\n- Use a professional, readable font available in the selected platform.\n- Make hierarchy, loading, empty, error, and refusal states clear.\n- Build responsive, keyboard-accessible interfaces; never hide essential meaning behind color alone.\n- Use visuals to explain the project workflow, architecture, or evaluation—not as decoration.\n",
        ".env.example": "# Add variable names only. Never commit credentials.\n",
        ".project/architecture.md": architecture,
        ".project/milestones.yml": milestones,
        ".project/evidence.yml": "version: 1\nevidence: []\n",
        ".project/approvals.yml": "version: 1\narchitecture: pending\ncloud: not-requested\npublication: not-requested\n",
        ".project/state.md": "# Current state\n\n- Lifecycle: scaffolded\n- Deployment: local\n- Publication: absent\n- Contract health: pending architecture approval\n",
        ".project/handoff.md": "# Handoff\n\n## Next action\n\nReview and approve the architecture comparison in `.project/architecture.md`.\n\n## Recovery\n\nNo implementation, cloud resource, or public release has been created.\n",
        "architecture/system.mmd": f"flowchart LR\n  A[Representative data] --> B[Validate and prepare]\n  B --> C[{charter.title}]\n  C --> D[Decision-focused output]\n  C --> E[Evaluation evidence]\n",
        "docs/rules/category.md": (KIT_ROOT / "rules" / "category" / f"{charter.category}.md").read_text(encoding="utf-8") if (KIT_ROOT / "rules" / "category" / f"{charter.category}.md").exists() else "# Category rules\n\nAdd category-specific delivery rules before implementation.\n",
        "docs/rules/industry.md": (KIT_ROOT / "rules" / "industry" / f"{slugify(charter.industry)}.md").read_text(encoding="utf-8") if (KIT_ROOT / "rules" / "industry" / f"{slugify(charter.industry)}.md").exists() else "# Industry rules\n\nAdd industry-specific data and claim constraints before implementation.\n",
        "portfolio/project.json": json.dumps({"version": 1, "slug": charter.slug, "title": charter.title, "status": "draft", "source": {"dataBoundary": charter.data_boundary}, "evidence": []}, indent=2),
        ".github/workflows/quality.yml": "name: quality\non: [push, pull_request]\njobs:\n  project-records:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - uses: actions/setup-python@v5\n        with:\n          python-version: '3.11'\n      - run: python3 scripts/project_kit.py check\n",
    }


def normalize_catalog_links(markdown: str) -> str:
    markdown = re.sub(r"\]\(\.\./\.\./case-studies/[^)]+\)", "](case-study.md)", markdown)
    return re.sub(r"\]\(\.\./\.\./projects/[^)]+\)", "](charter.md)", markdown)


def import_charters(args: argparse.Namespace) -> None:
    source = Path(args.source).expanduser().resolve()
    projects = source / "projects"
    case_studies = source / "case-studies"
    destination = Path(args.destination).expanduser().resolve()
    if not projects.is_dir() or not case_studies.is_dir():
        raise ValueError("Source needs projects/ and case-studies/ directories.")
    if destination.exists():
        if not args.replace:
            raise ValueError(f"Catalog already exists: {destination}. Use --replace to refresh it.")
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    entries = []
    seen_slugs: set[str] = set()
    for charter_path in sorted(projects.rglob("*.md")):
        relative = charter_path.relative_to(projects)
        case_study_path = case_studies / relative
        if not case_study_path.is_file():
            raise ValueError(f"Missing matching case study: {case_study_path}")
        charter = parse_charter(charter_path)
        if charter.slug in seen_slugs:
            raise ValueError(f"Duplicate project slug: {charter.slug}")
        seen_slugs.add(charter.slug)
        project_dir = destination / charter.slug
        project_dir.mkdir()
        write(project_dir / "charter.md", normalize_catalog_links(charter_path.read_text(encoding="utf-8")))
        write(project_dir / "case-study.md", normalize_catalog_links(case_study_path.read_text(encoding="utf-8")))
        entries.append({
            "slug": charter.slug,
            "title": charter.title,
            "category": charter.category,
            "industry": charter.industry,
            "charter": f"{charter.slug}/charter.md",
            "caseStudy": f"{charter.slug}/case-study.md",
        })
    write(destination / "index.json", json.dumps({"version": 1, "projects": entries}, indent=2))
    print(f"Imported {len(entries)} charter/case-study pairs into: {destination}")


def bootstrap(args: argparse.Namespace) -> None:
    charter_path = Path(args.charter).expanduser().resolve()
    workspace = Path(args.workspace).expanduser().resolve()
    if not charter_path.is_file():
        raise ValueError(f"Charter not found: {charter_path}")
    if not workspace.is_dir():
        raise ValueError(f"Workspace not found: {workspace}")
    charter = parse_charter(charter_path)
    destination = workspace / charter.slug
    if destination.exists():
        raise ValueError(f"Refusing to overwrite existing destination: {destination}")
    destination.mkdir()
    try:
        write(destination / "PROJECT.md", charter_path.read_text(encoding="utf-8"))
        if args.case_study:
            case_study = Path(args.case_study).expanduser().resolve()
            if not case_study.is_file():
                raise ValueError(f"Case study not found: {case_study}")
            write(destination / "CASE-STUDY.md", case_study.read_text(encoding="utf-8"))
        for relative, content in project_files(charter).items():
            write(destination / relative, content)
        destination_script = destination / "scripts" / "project_kit.py"
        destination_script.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(Path(__file__), destination_script)
        destination_script.chmod(0o755)
        copy_adapter("CLAUDE.md", destination / "CLAUDE.md")
        copy_adapter("copilot-instructions.md", destination / ".github" / "copilot-instructions.md")
        copy_adapter("cursor-rule.mdc", destination / ".cursor" / "rules" / "project-delivery.mdc")
        write(destination / ".gitignore", "__pycache__/\n*.py[cod]\n.env\n.DS_Store\n")
        if not args.skip_git:
            run(["git", "init", "-b", "main"], destination)
            run(["git", "add", "."], destination)
            run(["git", "commit", "-m", "chore: bootstrap project foundation"], destination)
        if args.create_github:
            if args.skip_git:
                raise ValueError("GitHub creation requires Git; omit --skip-git.")
            if not args.github_owner:
                raise ValueError("GitHub creation requires --github-owner.")
            run(["gh", "repo", "create", f"{args.github_owner}/{charter.slug}", "--private", "--source", str(destination), "--remote", "origin", "--push"], destination)
    except Exception:
        shutil.rmtree(destination, ignore_errors=True)
        raise
    print(f"Initialized: {destination}")
    print("Next: review .project/architecture.md and record a human architecture approval before implementation.")


def check(_: argparse.Namespace) -> None:
    root = Path.cwd()
    required = [
        "PROJECT.md",
        "CASE-STUDY.md",
        "AGENTS.md",
        "DESIGN.md",
        ".project/architecture.md",
        ".project/data.md",
        ".project/evaluation.md",
        ".project/milestones.yml",
        ".project/evidence.yml",
        ".project/approvals.yml",
        ".project/state.md",
        ".project/handoff.md",
        ".project/publication.md",
        SIGNATURE_FILE,
        "architecture/system.mmd",
        "docs/data-dictionary.md",
        "docs/metric-glossary.md",
        "graphify-out/graph.json",
        "portfolio/project.json",
    ]
    missing = [name for name in required if not (root / name).is_file()]
    if missing:
        raise ValueError("Missing project records: " + ", ".join(missing))
    milestones = (root / ".project/milestones.yml").read_text(encoding="utf-8")
    if "milestones:" not in milestones or "acceptance:" not in milestones:
        raise ValueError("milestones.yml needs milestones and acceptance criteria")
    manifest = json.loads((root / "portfolio/project.json").read_text(encoding="utf-8"))
    if manifest.get("status") not in {
        "draft",
        "first-demo",
        "trust-foundation",
        "issuance-workflow",
        "analyst-product",
        "release-candidate",
        "live-verified",
    }:
        raise ValueError("portfolio/project.json has an invalid status")
    signature = (root / SIGNATURE_FILE).read_text(encoding="utf-8").strip()
    if signature != source_signature(root):
        raise ValueError("Graphify is stale. Run: python3 scripts/project_kit.py graph-sync")
    print("Project records: pass")


def source_signature(root: Path) -> str:
    digest = hashlib.sha256()
    excluded_parts = {
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".venv",
        "__pycache__",
        "graphify-out",
        "local",
        "node_modules",
        "venv",
    }
    excluded_files = {SIGNATURE_FILE, ".DS_Store"}
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative_path = path.relative_to(root)
        relative = relative_path.as_posix()
        if relative in excluded_files or any(part in excluded_parts for part in relative_path.parts):
            continue
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def graph_sync(_: argparse.Namespace) -> None:
    root = Path.cwd()
    run(["graphify", "update", "."], root)
    write(root / SIGNATURE_FILE, source_signature(root))
    print("Graphify: current")


def main() -> int:
    parser = argparse.ArgumentParser(prog="project-kit")
    subparsers = parser.add_subparsers(dest="command", required=True)
    bootstrap_parser = subparsers.add_parser("bootstrap", help="create a minimal project from a charter")
    bootstrap_parser.add_argument("--charter", required=True)
    bootstrap_parser.add_argument("--case-study")
    bootstrap_parser.add_argument("--workspace", required=True)
    bootstrap_parser.add_argument("--create-github", action="store_true")
    bootstrap_parser.add_argument("--github-owner")
    bootstrap_parser.add_argument("--skip-git", action="store_true")
    bootstrap_parser.set_defaults(handler=bootstrap)
    catalog_parser = subparsers.add_parser("import-charters", help="copy paired charters into an independent catalog")
    catalog_parser.add_argument("--source", required=True, help="directory containing projects/ and case-studies/")
    catalog_parser.add_argument("--destination", default=str(KIT_ROOT / "charters"))
    catalog_parser.add_argument("--replace", action="store_true")
    catalog_parser.set_defaults(handler=import_charters)
    check_parser = subparsers.add_parser("check", help="validate initialized project records")
    check_parser.set_defaults(handler=check)
    graph_parser = subparsers.add_parser("graph-sync", help="refresh Graphify and stamp source freshness")
    graph_parser.set_defaults(handler=graph_sync)
    args = parser.parse_args()
    try:
        args.handler(args)
    except (ValueError, RuntimeError) as error:
        print(f"project-kit: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
