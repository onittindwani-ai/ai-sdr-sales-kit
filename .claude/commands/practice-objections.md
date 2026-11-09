---
description: Role play a prospect and practise your answers to why not just use Salesforce
argument-hint: "[number of rounds, default 5]"
---

Run a short practice session. Number of rounds: $ARGUMENTS (use 5 if blank).

Read `examples/synthetic-objections.json`. These lines are made up. Each round:

1. Pick a line at random, favouring the ones marked "hidden". Say it in character as a prospect, and do not reveal the answer number.
2. Wait for the user to reply as if on a call.
3. Open the answer it points to in `answers/` (or in `output/my-playbook-final.md` if that exists) and give short feedback on 3 things: did they find what the prospect really meant, did they stay honest, and did they ask a follow up question?
4. If "When the tool is the better fit" applies to the prospect, say so.

Rules: never invent statistics or results, never state a price for Salesforce Hunter or say it has been released, and never speak badly of a company. At the end, name the 2 answers the user should practise most.
