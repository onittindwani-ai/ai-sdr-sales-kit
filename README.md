# AI SDR Sales Kit

25 ready answers to "why not just use Salesforce", for people running or starting an AI SDR agency, with the guide, offer and call script to go with them.

An AI SDR agency uses AI to find sales prospects and book calls for its clients. Now that big companies are shipping their own AI sales agents, every client is going to ask why they should not just use one of those. This kit gives you an honest answer for each version of that question, including the times when the honest answer is that the tool is the better fit.

## Start here

Open this folder in Claude Code, fill in what you can, and paste this:

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

You get one playbook in `output/`: all 25 answers written for your niche, plus your comparison sheet, one page offer and discovery call script.

Do not have the folder yet? Give Claude Code this link and ask it to set the kit up for you: https://github.com/onittindwani-ai/ai-sdr-sales-kit

## What is inside

| Part | Count | Where |
| --- | --- | --- |
| Ready answers | 25 | [answers](answers/README.md) |
| Answer categories | 5 | cost and setup, who runs it, results and trust, data, switching |
| Parts in every answer | 5 | what they really mean, spoken answer, email version, follow up question, when the tool is the better fit |
| Who to sell to guide (the founder with no sales team) | 1 | [guides/who-to-sell-to.md](guides/who-to-sell-to.md) |
| One page offer template | 1 | [templates/one-page-offer.md](templates/one-page-offer.md) |
| Comparison sheet (Hunter, HubSpot, done for you agency) | 1 | [templates/comparison-sheet.md](templates/comparison-sheet.md) |
| Discovery call script | 1 | [templates/discovery-call-script.md](templates/discovery-call-script.md) |
| Claude Code quick start prompt | 1 | [QUICK-START-PROMPT.md](QUICK-START-PROMPT.md) |
| Claude Code skill | 1 | [.claude/skills/personalize-sdr-answers](.claude/skills/personalize-sdr-answers/SKILL.md) |
| Claude Code commands | 2 | `/personalize-answers` and `/practice-objections` |
| Python tool, standard library only | 1 | [tools/personalize.py](tools/personalize.py) |
| Practice lines (synthetic) | 50 | [examples/synthetic-objections.json](examples/synthetic-objections.json) |
| Worked example configs and playbooks (synthetic) | 3 | [examples/configs](examples/configs) and [examples/playbooks](examples/playbooks) |
| Sample discovery call (synthetic) | 1 | [examples/sample-discovery-call.md](examples/sample-discovery-call.md) |

## The 25 questions

Each of these is one answer. The [full list](answers/README.md) links to every file.

- **Cost and setup:** Salesforce, HubSpot at $1 a lead, Clay and a few tools, doing it yourself this weekend, and whether a tool has to be cheaper.
- **Who runs it:** the agent doing the whole job, the office manager, hiring a junior rep, ChatGPT or Claude, and what you are paying for.
- **Results and trust:** being small, promising meetings, spam, AI mistakes, and having no results in their industry.
- **Data:** 240 million contacts, who owns the list, not having a CRM, whether this is allowed, and customer data going into AI.
- **Switching:** already paying for HubSpot, moving to Salesforce later, tools replacing you, waiting for Hunter, and having been burned before.

See what a finished one looks like in [this example playbook](examples/playbooks/commercial-cleaning.md). The agency in it is made up.

## Run it without AI

You need Python 3.9 or newer, and nothing else.

```text
python3 tools/personalize.py --init my-config.json
python3 tools/personalize.py --check --config my-config.json
python3 tools/personalize.py --config my-config.json --out output/my-playbook.md
python3 tools/personalize.py --audit output/my-playbook.md --config my-config.json
python3 tests/check_kit.py
```

The first line writes a details file, and you replace each REPLACE value in it. The audit catches missing answers, new numbers and risky claims, and confirms the honest sections are intact. The last line checks the whole kit.

## Honest limits

- This is an independent kit, not made or endorsed by Salesforce, HubSpot, Clay, Apollo or LinkedIn.
- Nobody has measured how often these answers win deals, so the kit makes no claim about results.
- Vendor facts were checked on 2026-11-09 and they change quickly. Recheck them first, especially Hunter's status. No price for Hunter is stated, because none was published on the pages we read. See [SOURCES.md](SOURCES.md).
- Every promise in an answer has to be true of your business. If it is not, change it or do not use it.
- All examples are made up and labelled as synthetic.
- This is not legal advice.

Read the full [HONEST-LIMITS.md](HONEST-LIMITS.md) before you use this with a client.

## Licence

MIT. See [LICENSE](LICENSE).
