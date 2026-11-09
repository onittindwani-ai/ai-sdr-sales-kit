"""Checks that the AI SDR Sales Kit is complete, honest and clean, and that its tool works.

Standard library only. Run from anywhere:

    python3 tests/check_kit.py

Exit code 0 means every check passed. Exit code 1 lists each problem found.
"""

from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOOL = ROOT / "tools" / "personalize.py"

sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "tools"))
import personalize  # noqa: E402

EXPECTED_ANSWERS = 25
EXPECTED_CATEGORIES = {
    "cost-and-setup": 5,
    "who-runs-it": 5,
    "results-and-trust": 5,
    "data": 5,
    "switching": 5,
}
REQUIRED_SECTIONS = [
    "## What they really mean",
    "## Say it out loud",
    "## Send it by email",
    "## Ask this next",
    "## When the tool is the better fit",
    "## Facts this answer uses",
]
REQUIRED_FILES = [
    "README.md",
    "QUICK-START-PROMPT.md",
    "SOURCES.md",
    "HONEST-LIMITS.md",
    "CHANGELOG.md",
    "LICENSE",
    "CLAUDE.md",
    "AGENTS.md",
    ".gitignore",
    ".github/workflows/check.yml",
    ".claude/skills/personalize-sdr-answers/SKILL.md",
    ".claude/commands/personalize-answers.md",
    ".claude/commands/practice-objections.md",
    "answers/README.md",
    "guides/who-to-sell-to.md",
    "templates/one-page-offer.md",
    "templates/comparison-sheet.md",
    "templates/discovery-call-script.md",
    "templates/config-template.json",
    "tools/personalize.py",
    "examples/synthetic-objections.json",
    "examples/sample-discovery-call.md",
]
REQUIRED_SOURCE_URLS = [
    "https://www.salesforce.com/news/stories/agentforce-job-ready-ai-agents/",
    "https://www.salesforce.com/sales/ai-sales-agent/outbound/",
    "https://www.salesforce.com/news/stories/agentic-marketing-teams-announcement/",
    "https://www.prnewswire.com/news-releases/apollo-named-flagship-data-partner-for-hunter-salesforces-new-outbound-sales-agent-302879231.html",
    "https://www.hubspot.com/products/sales/ai-prospecting-agent",
    "https://www.hubspot.com/company-news/hubspots-customer-agent-and-prospecting-agent-now-you-pay-when-the-task-is-complete",
    "https://www.clay.com/blog/sculpt-2026-recap",
    "https://www.linkedin.com/legal/user-agreement",
]
REPO_HOME = "https://github.com/onittindwani-ai/ai-sdr-sales-kit"
MAX_OFFER_WORDS = 400
SPOKEN_WORDS = (40, 130)
EMAIL_WORDS = (40, 140)
MIN_BETTER_FIT_WORDS = 20

# Dash characters that must never appear (written as codes so this file stays clean).
BANNED_DASHES = {chr(c): f"U+{c:04X}" for c in (0x2010, 0x2011, 0x2012, 0x2013, 0x2014, 0x2015, 0x2212, 0xFE58, 0xFF0D)}

# Patterns that look like real keys. Built from parts so this file does not match itself.
SECRET_PATTERNS = [
    ("OpenAI style key", re.compile("s" + r"k-[A-Za-z0-9_\-]{20,}")),
    ("GitHub token", re.compile("gh" + r"[pousr]_[A-Za-z0-9]{30,}")),
    ("AWS access key", re.compile("AK" + r"IA[0-9A-Z]{16}")),
    ("Slack token", re.compile("xo" + r"x[abpr]-[A-Za-z0-9\-]{10,}")),
    ("Private key block", re.compile("-----BEGIN " + r"[A-Z ]*PRIVATE KEY-----")),
]
EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
ALLOWED_EMAIL_DOMAINS = ("example.com", "example.org", "example.net", "example.test")

# Truth rules. Each is built so that this file does not trip its own scan.
HUNTER_PRICE = [
    re.compile("Hun" + r"ter[^.\n|]*\$\s?\d"),
    re.compile(r"\$\s?\d[^.\n|]*Hun" + "ter"),
]
HUNTER_LIVE = re.compile("Hun" + r"ter[^.\n|]*\b(is|now)\s+(generally available|live|available now)", re.IGNORECASE)
INVENTED_STAT = re.compile(r"\d\s*(%|percent\b)|\bclose rates? of\b|\b\d+x\b", re.IGNORECASE)
MONEY = re.compile(r"\$\s?(\d[\d,.]*)")
ATTACK_WORDS = re.compile(r"\b(scam|scammy|garbage|useless|terrible|rip ?off|joke of a|awful|trash)\b", re.IGNORECASE)

TEXT_SUFFIXES = {".md", ".py", ".yml", ".yaml", ".txt", ".json", ""}
SKIP_DIRS = {".git", "__pycache__", "output"}


def text_files() -> list[pathlib.Path]:
    files = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(ROOT).parts):
            continue
        if path.suffix.lower() in TEXT_SUFFIXES or path.name.startswith("."):
            files.append(path)
    return files


def answer_files() -> list[pathlib.Path]:
    return sorted((ROOT / "answers").glob("*/*.md"), key=lambda p: p.name)


def section_body(text: str, heading: str) -> str:
    start = text.find(heading)
    if start == -1:
        return ""
    rest = text[start + len(heading):]
    nxt = re.search(r"\n## ", rest)
    return rest[: nxt.start()] if nxt else rest


def words(text: str) -> int:
    return len(text.split())


def check_files(errors: list[str]) -> None:
    for name in REQUIRED_FILES:
        if not (ROOT / name).exists():
            errors.append(f"missing {name}")


def check_counts(errors: list[str]) -> None:
    files = answer_files()
    if len(files) != EXPECTED_ANSWERS:
        errors.append(f"answers: expected {EXPECTED_ANSWERS} files, found {len(files)}")
    for folder, expected in EXPECTED_CATEGORIES.items():
        found = len(list((ROOT / "answers" / folder).glob("*.md")))
        if found != expected:
            errors.append(f"answers/{folder}: expected {expected} files, found {found}")
    numbers = [int(p.name[:2]) for p in files if p.name[:2].isdigit()]
    if numbers != list(range(1, EXPECTED_ANSWERS + 1)):
        errors.append(f"answers: numbers are not 1 to {EXPECTED_ANSWERS} in order: {numbers}")


def check_email(rel: pathlib.PurePath, body: str, errors: list[str]) -> None:
    if not re.search(r"^Subject: .{5,}", body, re.MULTILINE):
        errors.append(f"{rel}: email has no Subject line")
    if not body.strip().endswith("{{your_name}}"):
        errors.append(f"{rel}: email does not end with {{{{your_name}}}}")
    low, high = EMAIL_WORDS
    if not low <= words(body) <= high:
        errors.append(f"{rel}: email is {words(body)} words, wanted {low} to {high}")


def check_answer(path: pathlib.Path, errors: list[str]) -> tuple[str, str]:
    rel = path.relative_to(ROOT)
    text = path.read_text(encoding="utf-8")
    title = re.match(r"# (\d{2})\. (.+)", text)
    if not title or title.group(1) != path.name[:2]:
        errors.append(f"{rel}: first line must be '# {path.name[:2]}. Title'")
    said = re.search(r'^\*\*They say:\*\* "(.+)"$', text, re.MULTILINE)
    if not said:
        errors.append(f"{rel}: missing the **They say:** line")
    for heading in REQUIRED_SECTIONS:
        if heading not in text:
            errors.append(f"{rel}: missing section '{heading}'")
        elif words(section_body(text, heading)) < 5:
            errors.append(f"{rel}: section '{heading}' looks empty")
    spoken = words(section_body(text, "## Say it out loud"))
    if not SPOKEN_WORDS[0] <= spoken <= SPOKEN_WORDS[1]:
        errors.append(f"{rel}: spoken answer is {spoken} words, wanted {SPOKEN_WORDS[0]} to {SPOKEN_WORDS[1]}")
    check_email(rel, section_body(text, "## Send it by email"), errors)
    if not section_body(text, "## Ask this next").strip().endswith(('?', '?"')):
        errors.append(f"{rel}: the follow up must be a question")
    if words(section_body(text, "## When the tool is the better fit")) < MIN_BETTER_FIT_WORDS:
        errors.append(f"{rel}: the honest 'better fit' section is too thin")
    return (title.group(2) if title else "", said.group(1) if said else "")


def check_answer_index(titles: list[str], errors: list[str]) -> None:
    path = ROOT / "answers" / "README.md"
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    for title in titles:
        if title and title not in text:
            errors.append(f"answers/README.md: does not list '{title}'")


def check_truth(errors: list[str]) -> None:
    for path in text_files():
        rel = path.relative_to(ROOT)
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if any(p.search(line) for p in HUNTER_PRICE):
                errors.append(f"{rel}:{lineno}: states a price next to the Salesforce agent")
            if str(rel) != "SOURCES.md" and HUNTER_LIVE.search(line):
                errors.append(f"{rel}:{lineno}: says the Salesforce agent is released")
    for path in answer_files():
        rel = path.relative_to(ROOT)
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if INVENTED_STAT.search(line):
                errors.append(f"{rel}:{lineno}: looks like a statistic")
            if ATTACK_WORDS.search(line):
                errors.append(f"{rel}:{lineno}: attack wording")
            if personalize.promises_guarantee(line):
                errors.append(f"{rel}:{lineno}: promises a guarantee")
            for amount in MONEY.findall(line):
                if amount.rstrip(".,") != "1":
                    errors.append(f"{rel}:{lineno}: dollar amount ${amount} is not a documented fact")
    sheet = (ROOT / "templates/comparison-sheet.md")
    if sheet.exists():
        text = sheet.read_text(encoding="utf-8")
        for needed in ("$1 for each lead", "Do not quote", "Not covered", "2026-11-09", "waitlist"):
            if needed not in text:
                errors.append(f"templates/comparison-sheet.md: should contain '{needed}'")


def check_sources(errors: list[str]) -> None:
    path = ROOT / "SOURCES.md"
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    numbers = {int(n) for n in re.findall(r"^### (\d+)\.", text, re.MULTILINE)}
    for url in REQUIRED_SOURCE_URLS:
        if url not in text:
            errors.append(f"SOURCES.md: missing {url}")
    if "2026-11-09" not in text:
        errors.append("SOURCES.md: no checked date")
    for doc in answer_files() + [ROOT / "templates/comparison-sheet.md", ROOT / "guides/who-to-sell-to.md"]:
        if not doc.exists():
            continue
        for ref in re.findall(r"\bsources? (\d+)\b", doc.read_text(encoding="utf-8"), re.IGNORECASE):
            if int(ref) not in numbers:
                errors.append(f"{doc.relative_to(ROOT)}: points at source {ref}, which SOURCES.md does not have")


def check_placeholders(errors: list[str]) -> None:
    known = set(personalize.FIELDS)
    fillable = answer_files() + [ROOT / "templates" / n for n in ("one-page-offer.md", "comparison-sheet.md", "discovery-call-script.md")]
    used: set[str] = set()
    for path in fillable:
        if not path.exists():
            continue
        found = set(re.findall(r"\{\{([a-z_]+)\}\}", path.read_text(encoding="utf-8")))
        used |= found
        for name in sorted(found - known):
            errors.append(f"{path.relative_to(ROOT)}: unknown placeholder {name}")
    for name in sorted(known - used):
        errors.append(f"tools/personalize.py: field {name} is never used")


def check_offer_length(errors: list[str]) -> None:
    path = ROOT / "templates/one-page-offer.md"
    if path.exists() and words(path.read_text(encoding="utf-8")) > MAX_OFFER_WORDS:
        errors.append(f"templates/one-page-offer.md: over {MAX_OFFER_WORDS} words, so not one page")


def check_synthetic(errors: list[str]) -> None:
    path = ROOT / "examples/synthetic-objections.json"
    if not path.exists():
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("label") != "SYNTHETIC. Made up practice lines, not real customers.":
        errors.append("examples/synthetic-objections.json: missing the synthetic label")
    items = data.get("items", [])
    per_answer: dict[int, int] = {}
    texts = set()
    for item in items:
        per_answer[item["answer"]] = per_answer.get(item["answer"], 0) + 1
        texts.add(item["text"])
        if item.get("synthetic") is not True:
            errors.append(f"synthetic-objections: item '{item['text'][:30]}' is not labelled synthetic")
        if item.get("category") not in EXPECTED_CATEGORIES:
            errors.append(f"synthetic-objections: bad category on '{item['text'][:30]}'")
    if len(items) != 50 or len(texts) != 50:
        errors.append(f"synthetic-objections: expected 50 distinct lines, found {len(texts)} of {len(items)}")
    if sorted(per_answer) != list(range(1, 26)) or set(per_answer.values()) != {2}:
        errors.append("synthetic-objections: every answer needs exactly 2 lines")
    for sample in ["examples/sample-discovery-call.md"]:
        target = ROOT / sample
        if target.exists() and "SYNTHETIC" not in target.read_text(encoding="utf-8"):
            errors.append(f"{sample}: not labelled SYNTHETIC")
    for config in sorted((ROOT / "examples/configs").glob("*.json")):
        if "ynthetic" not in json.loads(config.read_text(encoding="utf-8")).get("_note", ""):
            errors.append(f"{config.relative_to(ROOT)}: not labelled synthetic in _note")


def check_prompt_and_helpers(errors: list[str]) -> None:
    readme, quick = ROOT / "README.md", ROOT / "QUICK-START-PROMPT.md"
    if readme.exists() and quick.exists():
        block = re.search(r"```text\n(.+?)\n```", quick.read_text(encoding="utf-8"), re.DOTALL)
        if not block:
            errors.append("QUICK-START-PROMPT.md: no ```text prompt block")
        elif block.group(1) not in readme.read_text(encoding="utf-8"):
            errors.append("README.md: the quick start prompt differs from QUICK-START-PROMPT.md")
    skill = ROOT / ".claude/skills/personalize-sdr-answers/SKILL.md"
    if skill.exists():
        text = skill.read_text(encoding="utf-8")
        if not re.match(r"---\nname: personalize-sdr-answers\ndescription: .{40,}\n---", text):
            errors.append("SKILL.md: bad frontmatter")
        for needed in ("--audit", "--config", "25"):
            if needed not in text:
                errors.append(f"SKILL.md: should mention {needed}")
    for command in (ROOT / ".claude/commands").glob("*.md"):
        if not re.match(r"---\ndescription: .{20,}\n", command.read_text(encoding="utf-8")):
            errors.append(f"{command.name}: needs a description in its frontmatter")


def check_readme_counts(errors: list[str]) -> None:
    path = ROOT / "README.md"
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    configs = len(list((ROOT / "examples/configs").glob("*.json")))
    rows = {
        "Ready answers": EXPECTED_ANSWERS,
        "Answer categories": len(EXPECTED_CATEGORIES),
        "Practice lines (synthetic)": 50,
        "Worked example configs and playbooks (synthetic)": configs,
    }
    for label, count in rows.items():
        if f"| {label} | {count} |" not in text:
            errors.append(f"README.md: table row '{label}' should say {count}")


def check_links(errors: list[str]) -> None:
    for path in text_files():
        rel = path.relative_to(ROOT)
        text = path.read_text(encoding="utf-8")
        if path.suffix == ".md":
            for target in re.findall(r"\]\(([^)]+)\)", text):
                if target.startswith(("http://", "https://", "#", "mailto:")):
                    continue
                if not (path.parent / target.split("#")[0]).resolve().exists():
                    errors.append(f"{rel}: broken link to '{target}'")
        if path.name == "check_kit.py":
            continue
        for url in re.findall(r"https://github\.com/[^\s)\"'`]+", text):
            if url.rstrip(".,") != REPO_HOME:
                errors.append(f"{rel}: GitHub link is not the repo home page: {url}")


def check_clean_text(errors: list[str]) -> None:
    for path in text_files():
        rel = path.relative_to(ROOT)
        fenced = False
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for char, name in BANNED_DASHES.items():
                if char in line:
                    errors.append(f"{rel}:{lineno}: contains the dash {name}")
            if line.startswith("```"):
                fenced = not fenced
            if path.suffix == ".md" and not fenced and " - " in line.lstrip("- ").strip():
                errors.append(f"{rel}:{lineno}: a spaced hyphen is used as a dash")
            for name, pattern in SECRET_PATTERNS:
                if pattern.search(line):
                    errors.append(f"{rel}:{lineno}: looks like a {name}")
            for email in EMAIL_PATTERN.findall(line):
                if not email.lower().endswith(ALLOWED_EMAIL_DOMAINS):
                    errors.append(f"{rel}:{lineno}: contains an email address ({email})")


def run_tool(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-B", str(TOOL), *args],
        capture_output=True, text=True, cwd=str(ROOT), timeout=60,
    )


def expect(errors: list[str], name: str, condition: bool, detail: str = "") -> None:
    if not condition:
        errors.append(f"tool: {name} {detail}".rstrip())


def expect_refused(errors: list[str], name: str, result: subprocess.CompletedProcess, needle: str) -> None:
    combined = result.stdout + result.stderr
    expect(errors, name, result.returncode == 1 and needle in combined and "Traceback" not in combined, combined[:200])


def good_config() -> dict:
    configs = sorted((ROOT / "examples/configs").glob("*.json"))
    return json.loads(configs[0].read_text(encoding="utf-8")) if configs else {}


def check_tool_examples(errors: list[str], tmp: pathlib.Path) -> int:
    configs = sorted((ROOT / "examples/configs").glob("*.json"))
    expect(errors, "at least 3 example configs", len(configs) >= 3)
    for config in configs:
        out = tmp / f"{config.stem}.md"
        result = run_tool("--config", str(config), "--out", str(out))
        expect(errors, f"builds {config.name}", result.returncode == 0, result.stderr[:300])
        if not out.exists():
            continue
        text = out.read_text(encoding="utf-8")
        expect(errors, f"{config.name} has 25 answers", len(re.findall(r"^### Answer \d\d:", text, re.MULTILINE)) == 25)
        expect(errors, f"{config.name} has no leftover placeholders", "{{" not in text)
        values = json.loads(config.read_text(encoding="utf-8"))
        expect(errors, f"{config.name} uses the agency name", values["agency_name"] in text)
        expect(errors, f"{config.name} uses the niche", values["niche"] in text)
        shipped = ROOT / "examples/playbooks" / out.name
        expect(errors, f"{config.name} shipped playbook is current", shipped.exists() and shipped.read_text(encoding="utf-8") == text)
        audit = run_tool("--audit", str(out), "--config", str(config))
        expect(errors, f"{config.name} passes its audit", audit.returncode == 0, audit.stdout[:300])
    return len(configs)


def check_tool_refusals(errors: list[str], tmp: pathlib.Path) -> None:
    def config_with(**changes: object) -> str:
        path = tmp / "bad.json"
        path.write_text(json.dumps({**good_config(), **changes}), encoding="utf-8")
        return str(path)

    missing = {k: v for k, v in good_config().items() if k != "niche"}
    (tmp / "missing.json").write_text(json.dumps(missing), encoding="utf-8")
    expect_refused(errors, "refuses a missing field", run_tool("--check", "--config", str(tmp / "missing.json")), "niche")
    expect_refused(errors, "refuses a dash in a value", run_tool("--check", "--config", config_with(niche="a" + chr(0x2014) + "b")), "dash")
    expect_refused(errors, "refuses a guarantee", run_tool("--check", "--config", config_with(outcome="guaranteed meetings")), "guarantee")
    expect_refused(errors, "refuses a placeholder in a value", run_tool("--check", "--config", config_with(niche="{{buyer}}")), "{{")
    expect_refused(errors, "refuses an unfilled value", run_tool("--check", "--config", config_with(niche="REPLACE: who")), "niche")
    expect_refused(errors, "refuses a wrong type", run_tool("--check", "--config", config_with(niche=5)), "niche")
    (tmp / "broken.json").write_text("{not json", encoding="utf-8")
    expect_refused(errors, "explains broken JSON", run_tool("--check", "--config", str(tmp / "broken.json")), "JSON")
    expect_refused(errors, "explains a missing file", run_tool("--check", "--config", str(tmp / "nope.json")), "nope.json")

    blank_out = tmp / "blank.md"
    run_tool("--config", config_with(proof_line=""), "--out", str(blank_out))
    expect(errors, "blank proof uses the honest fallback", blank_out.exists() and personalize.FALLBACK_PROOF in blank_out.read_text(encoding="utf-8"))

    starter = tmp / "starter.json"
    expect(errors, "--init writes a starter", run_tool("--init", str(starter)).returncode == 0 and starter.exists())
    expect_refused(errors, "--init will not overwrite", run_tool("--init", str(starter)), "already exists")
    expect_refused(errors, "an unfilled starter is refused", run_tool("--check", "--config", str(starter)), "REPLACE")
    listing = run_tool("--list")
    expect(errors, "--list shows 25 rows", listing.returncode == 0 and len(listing.stdout.strip().splitlines()) == 25)


def audit_after(errors: list[str], tmp: pathlib.Path, config: pathlib.Path, base: str, name: str, changed: str, needle: str) -> None:
    expect(errors, f"negative control did not change the text ({name})", changed != base)
    path = tmp / "tampered.md"
    path.write_text(changed, encoding="utf-8")
    expect_refused(errors, f"audit catches {name}", run_tool("--audit", str(path), "--config", str(config)), needle)


def check_tool_audit(errors: list[str], tmp: pathlib.Path) -> None:
    configs = sorted((ROOT / "examples/configs").glob("*.json"))
    if not configs or not (tmp / f"{configs[0].stem}.md").exists():
        return
    config = configs[0]
    path = tmp / f"{config.stem}.md"
    base = path.read_text(encoding="utf-8")
    spoken = "#### Say it out loud\n\n"
    fit = "#### When the tool is the better fit\n\n"
    cases = [
        ("a missing answer", re.sub(r"^### Answer 25:.*?(?=^## )", "", base, count=1, flags=re.MULTILINE | re.DOTALL), "25"),
        ("a leftover placeholder", base.replace(spoken, spoken + "{{niche}} ", 1), "placeholder"),
        ("an invented percent", base.replace(spoken, spoken + "Clients see 37 percent more replies. ", 1), "statistic"),
        ("an invented number", base.replace(spoken, spoken + "We booked 412 calls last year. ", 1), "412"),
        ("a price next to the agent", base.replace(spoken, spoken + "Hun" + "ter costs $90 a month. ", 1), "price"),
        ("a release claim", base.replace(spoken, spoken + "Hun" + "ter is generally available. ", 1), "release"),
        ("a guarantee", base.replace(spoken, spoken + "We guarantee meetings. ", 1), "guarantee"),
        ("a dash", base.replace(spoken, spoken + "Yes" + chr(0x2013) + "no. ", 1), "dash"),
        ("an edited honest section", base.replace(fit, fit + "Tools are never better. ", 1), "better fit"),
    ]
    for name, changed, needle in cases:
        audit_after(errors, tmp, config, base, name, changed, needle)


def main() -> int:
    errors: list[str] = []
    check_files(errors)
    check_counts(errors)
    results = [check_answer(p, errors) for p in answer_files()]
    check_answer_index([title for title, _ in results], errors)
    said = [line for _, line in results if line]
    if len(set(said)) != len(said):
        errors.append("answers: two answers have the same 'They say' line")
    check_truth(errors)
    check_sources(errors)
    check_placeholders(errors)
    check_offer_length(errors)
    check_synthetic(errors)
    check_prompt_and_helpers(errors)
    check_readme_counts(errors)
    check_links(errors)
    check_clean_text(errors)
    with tempfile.TemporaryDirectory() as folder:
        tmp = pathlib.Path(folder)
        built = check_tool_examples(errors, tmp)
        check_tool_refusals(errors, tmp)
        check_tool_audit(errors, tmp)

    per_category = {f: len(list((ROOT / "answers" / f).glob("*.md"))) for f in EXPECTED_CATEGORIES}
    print(f"Answers: {len(answer_files())} ({', '.join(f'{k} {v}' for k, v in per_category.items())})")
    print(f"Example playbooks built and audited: {built}")
    print(f"Text files scanned: {len(text_files())}")
    if errors:
        print(f"\nFAILED with {len(errors)} problem(s):")
        for err in errors:
            print(f"  {err}")
        return 1
    print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
