#!/usr/bin/env python3
"""Fill the 25 answers from your details and write one personalised playbook.

Standard library only. Nothing here sends anything or touches the network.

Usage:
    python3 tools/personalize.py --init my-config.json
    python3 tools/personalize.py --check --config my-config.json
    python3 tools/personalize.py --config my-config.json --out output/my-playbook.md
    python3 tools/personalize.py --audit output/my-playbook-final.md --config my-config.json
    python3 tools/personalize.py --list
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
FACTS_CHECKED = "2026-11-09"
EXPECTED_ANSWERS = 25
STARTER = ROOT / "templates" / "config-template.json"

FIELDS = {
    "agency_name": "Your agency's name",
    "your_name": "The name you sign emails with",
    "niche": "Who you sell to, as a plural phrase",
    "buyer": "The person who says yes, as a singular job title",
    "their_customers": "Who your clients want to reach",
    "offer_name": "What you call your service",
    "outcome": "The result in plain words",
    "booked_call": "Exactly what counts, written to the client, for example a call on your calendar with...",
    "channels": "How you reach people",
    "setup_time": "How long until outreach starts",
    "monthly_price": "Your real price",
    "contract_terms": "Your real terms",
    "report_rhythm": "How often you report",
    "approval_step": "What the client approves, as a clause starting with 'you', without saying when",
    "data_exit": "What the client keeps if they leave, as a clause starting with 'you'",
    "proof_line": "One or two true sentences of proof. Leave empty if you have none yet",
}
OPTIONAL_FIELDS = {"proof_line"}
FALLBACK_PROOF = (
    "We are early, so I will not show you numbers I do not have. "
    "What I can show you is every message and every reply as it happens."
)

CATEGORIES = (
    ("cost-and-setup", "Cost and setup"),
    ("who-runs-it", "Who runs it"),
    ("results-and-trust", "Results and trust"),
    ("data", "Data"),
    ("switching", "Switching"),
)
SECTIONS = (
    "What they really mean",
    "Say it out loud",
    "Send it by email",
    "Ask this next",
    "When the tool is the better fit",
    "Facts this answer uses",
)
LOCKED_SECTIONS = ("When the tool is the better fit", "Facts this answer uses")
TEMPLATES = (
    ("Comparison sheet", "templates/comparison-sheet.md"),
    ("One page offer", "templates/one-page-offer.md"),
    ("Discovery call script", "templates/discovery-call-script.md"),
)

DASHES = {chr(c) for c in (0x2010, 0x2011, 0x2012, 0x2013, 0x2014, 0x2015, 0x2212, 0xFE58, 0xFF0D)}
PLACEHOLDER = re.compile(r"\{\{([a-z_]+)\}\}")
NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")
STATISTIC = re.compile(r"\d\s*(%|percent\b)|\bclose rates? of\b|\b\d+x\b", re.IGNORECASE)
AGENT = "Hun" + "ter"
AGENT_PRICE = (re.compile(AGENT + r"[^.\n|]*\$\s?\d"), re.compile(r"\$\s?\d[^.\n|]*" + AGENT))
AGENT_RELEASED = re.compile(AGENT + r"[^.\n|]*\b(is|now)\s+(generally available|live|available now)", re.IGNORECASE)
GUARANTEE = re.compile(r"guarantee", re.IGNORECASE)
NEGATION = re.compile(r"\b(no|not|never|cannot|can't|won't|don't|without)\b|\?", re.IGNORECASE)


class KitError(Exception):
    """A problem the user can fix. Printed plainly, never as a traceback."""


def load_config(path: pathlib.Path) -> dict:
    if not path.exists():
        raise KitError(f"I cannot find {path}. Make one with: python3 tools/personalize.py --init {path.name}")
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise KitError(f"{path.name} is not valid JSON (line {error.lineno}): {error.msg}") from error
    if not isinstance(config, dict):
        raise KitError(f"{path.name} must be one JSON object with your details.")
    return config


def field_problems(name: str, value: object) -> list[str]:
    if not isinstance(value, str):
        return [f"{name}: must be text in quotes."]
    problems = []
    if value.strip().upper().startswith("REPLACE"):
        problems.append(f"{name}: still says REPLACE. Put your real detail here.")
    if not value.strip() and name not in OPTIONAL_FIELDS:
        problems.append(f"{name}: is empty. {FIELDS[name]}.")
    if "{{" in value or "}}" in value:
        problems.append(f"{name}: must not contain {{{{ or }}}}.")
    if DASHES & set(value):
        problems.append(f"{name}: contains a long dash. Use a comma or a full stop.")
    if name != "proof_line" and GUARANTEE.search(value):
        problems.append(f"{name}: says guarantee. These answers never promise results; state your real terms instead.")
    return problems


def validate_config(config: dict) -> dict:
    problems = [f"{name}: is missing. {FIELDS[name]}." for name in FIELDS if name not in config and name not in OPTIONAL_FIELDS]
    for name, value in config.items():
        if name in FIELDS:
            problems.extend(field_problems(name, value))
    if problems:
        raise KitError("Your details need fixing:\n  " + "\n  ".join(problems))
    values = {name: config.get(name, "").strip() for name in FIELDS}
    return {**values, "proof_line": values["proof_line"] or FALLBACK_PROOF}


def fill(text: str, values: dict, source: str) -> str:
    def swap(match: re.Match) -> str:
        if match.group(1) not in values:
            raise KitError(f"{source} uses an unknown placeholder: {match.group(1)}")
        return values[match.group(1)]

    return PLACEHOLDER.sub(swap, text)


def split_sections(body: str, marker: str) -> dict:
    parts = re.split(rf"^{marker} (.+)$", body, flags=re.MULTILINE)
    return {parts[i].strip(): parts[i + 1].strip() for i in range(1, len(parts) - 1, 2)}


def parse_answer(path: pathlib.Path, label: str) -> dict:
    text = path.read_text(encoding="utf-8")
    title = re.match(r"# (\d{2})\. (.+)", text)
    said = re.search(r'^\*\*They say:\*\* (.+)$', text, re.MULTILINE)
    sections = split_sections(text, "##")
    missing = [name for name in SECTIONS if name not in sections]
    if not title or not said or missing:
        raise KitError(f"{path} is damaged. Missing: {missing or 'its title or They say line'}")
    return {
        "number": int(title.group(1)),
        "title": title.group(2).strip(),
        "said": said.group(1).strip(),
        "category": label,
        "sections": sections,
    }


def load_answers() -> list:
    answers = [
        parse_answer(path, label)
        for folder, label in CATEGORIES
        for path in sorted((ROOT / "answers" / folder).glob("*.md"))
    ]
    if [a["number"] for a in answers] != list(range(1, EXPECTED_ANSWERS + 1)):
        raise KitError(f"The answers folder should hold answers 1 to {EXPECTED_ANSWERS} in order.")
    return answers


def render_answer(answer: dict) -> str:
    lines = [f"### Answer {answer['number']:02d}: {answer['title']}", "", f"**They say:** {answer['said']}", ""]
    for name in SECTIONS:
        lines += [f"#### {name}", "", answer["sections"][name], ""]
    return "\n".join(lines)


def render_answers(answers: list) -> list:
    blocks = []
    for _, label in CATEGORIES:
        group = [a for a in answers if a["category"] == label]
        blocks += [f"## {label}", ""]
        blocks += [render_answer(a) for a in group]
    return blocks


def render_contents(answers: list) -> list:
    rows = ["| No. | Category | When they say |", "| --- | --- | --- |"]
    rows += [f"| {a['number']:02d} | {a['category']} | {a['title']} |" for a in answers]
    return rows + [""]


def render_template(path: str, values: dict) -> str:
    text = fill((ROOT / path).read_text(encoding="utf-8"), values, path)
    return re.sub(r"^(#{1,4}) ", r"#\1 ", text, flags=re.MULTILINE).strip() + "\n"


def build_playbook(values: dict) -> str:
    answers = load_answers()
    intro = [
        f"# {values['agency_name']} sales playbook",
        "",
        f"Answers for selling {values['offer_name']} to {values['niche']}.",
        "",
        f"Vendor facts in this playbook were checked on {FACTS_CHECKED}. Check SOURCES.md and the vendor's own page before you say them.",
        "",
        "Only say what is true of your business. Where an answer says a tool is the better fit, tell the client so.",
        "",
        "## Find your answer fast",
        "",
    ]
    body = [fill(block, values, "answers") for block in render_contents(answers) + render_answers(answers)]
    extras = [render_template(path, values) for _, path in TEMPLATES]
    return "\n".join(intro + body + extras).rstrip() + "\n"


def parse_playbook(text: str) -> dict:
    parts = re.split(r"^### Answer (\d+): .*$", text, flags=re.MULTILINE)
    found = {}
    for i in range(1, len(parts) - 1, 2):
        block = re.split(r"^## ", parts[i + 1], maxsplit=1, flags=re.MULTILINE)[0]
        found[int(parts[i])] = split_sections(block, "####")
    return found


def promises_guarantee(line: str) -> bool:
    sentences = re.split(r"(?<=[.!?])\s+", line)
    return any(GUARANTEE.search(s) and not NEGATION.search(s) for s in sentences)


def scan_claims(text: str) -> list:
    problems = []
    for lineno, line in enumerate(text.splitlines(), 1):
        if DASHES & set(line):
            problems.append(f"line {lineno}: contains a long dash")
        if any(p.search(line) for p in AGENT_PRICE):
            problems.append(f"line {lineno}: states a price for the Salesforce agent, which no page we read gives")
        if AGENT_RELEASED.search(line):
            problems.append(f"line {lineno}: says the Salesforce agent has had its general release, which no page we read confirms")
        if STATISTIC.search(line):
            problems.append(f"line {lineno}: looks like a statistic the kit has no source for: {line.strip()[:70]}")
        if promises_guarantee(line):
            problems.append(f"line {lineno}: promises a guarantee")
    return problems


def compare_to_base(found: dict, values: dict) -> list:
    base = parse_playbook(build_playbook(values))
    allowed_everywhere = set(NUMBER.findall(" ".join(values.values())))
    problems = []
    for number, sections in sorted(found.items()):
        original = base.get(number, {})
        for name in LOCKED_SECTIONS:
            if sections.get(name, "") != original.get(name):
                problems.append(f"Answer {number:02d}: the '{name}' section was changed. Restore it word for word.")
        allowed = allowed_everywhere | set(NUMBER.findall(" ".join(original.values())))
        for name in ("Say it out loud", "Send it by email"):
            for token in sorted(set(NUMBER.findall(sections.get(name, ""))) - allowed):
                problems.append(f"Answer {number:02d}: '{name}' has the number {token}, which is not in the kit or your details.")
    return problems


def audit(text: str, values: dict = None) -> list:
    source = text.replace(values["proof_line"], "") if values else text
    problems = scan_claims(source)
    if "{{" in text:
        problems.append("A placeholder such as {{niche}} is still unfilled.")
    found = parse_playbook(text)
    if sorted(found) != list(range(1, EXPECTED_ANSWERS + 1)):
        problems.append(f"Expected {EXPECTED_ANSWERS} answers numbered 1 to {EXPECTED_ANSWERS}, found {len(found)}.")
    for number, sections in sorted(found.items()):
        for name in SECTIONS:
            if not sections.get(name):
                problems.append(f"Answer {number:02d}: the '{name}' section is missing or empty.")
    for title, _ in TEMPLATES:
        if f"\n## {title}" not in text:
            problems.append(f"The '{title}' part is missing.")
    if values:
        problems += compare_to_base(found, values)
    return problems


def run_audit(path: pathlib.Path, config_path) -> int:
    if not path.exists():
        raise KitError(f"I cannot find {path}.")
    values = validate_config(load_config(config_path)) if config_path else None
    problems = audit(path.read_text(encoding="utf-8"), values)
    if problems:
        print(f"Audit FAILED with {len(problems)} problem(s):")
        print("\n".join(f"  {p}" for p in problems))
        return 1
    print(f"Audit passed: {EXPECTED_ANSWERS} answers, all parts present, no invented claims found.")
    if not config_path:
        print("Add --config to also confirm the honest sections were left alone.")
    return 0


def run_init(path: pathlib.Path) -> int:
    if path.exists():
        raise KitError(f"{path} already exists, so I left it alone.")
    shutil.copyfile(STARTER, path)
    print(f"Wrote {path}. Replace every REPLACE value with your own detail, then run --check.")
    return 0


def run_list() -> int:
    for answer in load_answers():
        print(f"{answer['number']:02d} | {answer['category']} | {answer['title']}")
    return 0


def run_build(config_path: pathlib.Path, out: pathlib.Path) -> int:
    text = build_playbook(validate_config(load_config(config_path)))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(f"Wrote {out} with {EXPECTED_ANSWERS} answers, a comparison sheet, a one page offer and a discovery call script.")
    return 0


def parser() -> argparse.ArgumentParser:
    tool = argparse.ArgumentParser(description="Fill the 25 answers from your details. Nothing is sent anywhere.")
    tool.add_argument("--config", type=pathlib.Path, help="your details as JSON")
    tool.add_argument("--out", type=pathlib.Path, default=ROOT / "output" / "playbook.md", help="where to write the playbook")
    tool.add_argument("--init", type=pathlib.Path, metavar="PATH", help="write a starter details file")
    tool.add_argument("--check", action="store_true", help="only check your details")
    tool.add_argument("--audit", type=pathlib.Path, metavar="PATH", help="check a finished playbook for invented claims")
    tool.add_argument("--list", action="store_true", help="list the 25 answers")
    return tool


def dispatch(args: argparse.Namespace, tool: argparse.ArgumentParser) -> int:
    if args.init:
        return run_init(args.init)
    if args.list:
        return run_list()
    if args.audit:
        return run_audit(args.audit, args.config)
    if not args.config:
        tool.print_help()
        return 2
    if args.check:
        validate_config(load_config(args.config))
        print(f"{args.config} looks good.")
        return 0
    return run_build(args.config, args.out)


def main() -> int:
    tool = parser()
    try:
        return dispatch(tool.parse_args(), tool)
    except KitError as error:
        print(f"Problem: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
