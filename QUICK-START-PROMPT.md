# Quick start prompt

Open this folder in Claude Code, fill in what you can below, and paste the whole thing in. Leave a line blank if you are not sure, and Claude will ask you.

```text
Read CLAUDE.md, then read .claude/skills/personalize-sdr-answers/SKILL.md and follow it step by step.
I run or am starting an AI SDR agency. Personalise all 25 answers in this kit to my niche and my offer.
Here is what I know so far. Ask me only for what is missing, and never guess a number or a result.
My agency name:
Who I sell to:
Who my clients want to reach:
What I offer and what it costs:
What proof I can honestly show:
When you finish, give me the path to my playbook and list anything you could not confirm.
```

Claude writes your playbook to `output/`. Nothing is sent anywhere, and your details stay on your computer.

Using Codex instead? The same prompt works. Codex reads `AGENTS.md` and the same skill file.

Prefer no AI at all? You can run the tool by hand:

```text
python3 tools/personalize.py --init my-config.json
python3 tools/personalize.py --check --config my-config.json
python3 tools/personalize.py --config my-config.json --out output/my-playbook.md
```
