# Instructions for Codex and other coding agents

Read `CLAUDE.md` and follow the same rules. To personalise the kit, follow the steps in `.claude/skills/personalize-sdr-answers/SKILL.md`.

The short version: never invent a number or a result, never state a price for Salesforce Hunter or say it is released, keep every "When the tool is the better fit" section, use no long dashes, and never send anything to anyone.

Check your work with `python3 tests/check_kit.py` and `python3 tools/personalize.py --audit <playbook> --config my-config.json`.
