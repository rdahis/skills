# skills

A collection of [Claude Code](https://claude.com/claude-code) skills.

## Quickstart

Install with the [`skills`](https://www.npmjs.com/package/skills) CLI (~30 seconds):

```bash
npx skills@latest add rdahis/skills
```

Select the skills you want and the coding agents to install them on. That's it — invoke a skill by name (e.g. `/concur-expense`) in your agent.

Prefer to do it by hand? Clone the repo and copy a skill folder into your skills directory:

```bash
git clone https://github.com/rdahis/skills.git
cp -r skills/skills/productivity/concur-expense ~/.claude/skills/
```

## Skills

### Productivity
| Skill | Description |
|-------|-------------|
| [`concur-expense`](skills/productivity/concur-expense/SKILL.md) | Turn a folder of receipts into a SAP Concur expense claim — read receipts, build the report, attach images, allocate to a fund. Draft-only unless you opt in to submit. |
| [`moodle`](skills/productivity/moodle/SKILL.md) | Administer a Moodle course from Claude Code — duplicate weekly activities, configure quizzes and Safe Exam Browser, enter gradebook marks from a spreadsheet, manage groups. Every change made in your own browser and re-read from Moodle to verify it. |
| [`overleaf`](skills/productivity/overleaf/SKILL.md) | Work on an Overleaf project from Claude Code — read the source, apply edits as tracked-change suggestions in your own browser, compile, and keep a Dropbox mirror safely in sync. Suggestions by default, direct edits only if you ask. |

Each skill folder is self-contained; see its `README.md` for requirements, installation, and usage.
