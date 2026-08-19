# concur-expense

A [Claude Code](https://claude.com/claude-code) skill that turns a folder of receipts into a SAP Concur expense claim. Claude reads each receipt locally, then drives Concur in a real browser — creating the report, entering each line, attaching the receipt image, and allocating it to a cost-center fund. It stops at a draft for you to review; it submits only if you explicitly ask and confirm.

Built and tuned against **Monash University's** SAP Concur. The workflow is general, but the expense-type names and allocation fields in `reference.md` are Monash-specific — adapt them for another institution.

## What it does

- Reads receipts (PDF / PNG / JPG / JPEG / HEIC) from a folder you point it at.
- Extracts vendor, date, total, currency, and GST from each — never guessing; it asks when a field is unreadable.
- Shows you a confirmation table before opening the browser.
- Hands off to you for SSO + MFA login (it never handles credentials).
- Creates a new report (or adds to an existing one), enters each receipt as a line, attaches the image, and allocates 100% to your fund.
- Stops at a **draft** by default. Pass `submit` to have it submit after a final confirmation.

## Requirements

- **Claude Code** with the **Claude-in-Chrome** browser extension connected (the skill drives Concur in a tab of your own Chrome through `mcp__claude-in-chrome__*` tools). Because it reuses your real Chrome session, your Concur login usually persists between runs.
- A **SAP Concur** account you can log into via your browser (SSO + MFA done by you).
- Local **receipt files**.

## Installation

Quickest — the [`skills`](https://www.npmjs.com/package/skills) CLI:

```bash
npx skills@latest add rdahis/skills
```

…then select `concur-expense` and the agent to install it on.

Manual alternative — copy the folder into your Claude Code skills directory:

```bash
git clone https://github.com/rdahis/skills.git
cp -r skills/skills/productivity/concur-expense ~/.claude/skills/
```

Then configure:

1. Edit `cost-centers.yaml` and replace the placeholder with your own fund code(s). Mark exactly one `default: true` — that entry is the fund used unless a `fund:CODE` argument overrides it.

2. The Concur entry URL is preset to **Monash University's**. If you're elsewhere, the skill asks for your institution's SSO entry URL on the first run and saves it into `reference.md`.

## Usage

Put the receipts for one claim in a folder, then invoke the skill:

```
/concur-expense ~/Downloads/trip-receipts
```

Optional arguments:

| Argument            | Effect                                                            |
|---------------------|-------------------------------------------------------------------|
| `<folder-path>`     | Folder of receipts (asked for if omitted).                        |
| `report:"Name"`     | Set the report name up front (else you're asked).                 |
| `fund:CODE`         | Override the default cost-center fund for the whole report.       |
| `submit`            | After building and verifying, ask for a final confirmation, then click **Submit Report**. Omit to always stop at draft. |

Examples:

```
/concur-expense ~/Downloads/adew-receipts report:"Conference 2026"
/concur-expense ~/Downloads/adew-receipts fund:"XXXXXX NNNNNNN" submit
```

## Workflow

1. **Point it at receipts.** Claude globs the folder and reads each file.
2. **Review the table.** Claude shows file / vendor / date / amount / currency / category / fund and waits for your confirmation. Correct anything that's wrong; set per-receipt fund overrides if needed.
3. **Log in.** Claude opens Concur; you complete SSO + MFA and tell it when you're on the home page.
4. **It builds the report.** One line per receipt: expense type, fields, GST, receipt upload, and fund allocation. If a report with a similar name already exists, it asks whether to add to it or create a new one.
5. **It stops at a draft** and reports the total, line count, and fund(s) used — unless you passed `submit`, in which case it asks once more, then submits and confirms the status changed.

## Safety

- **Draft-only by default.** It will not submit unless you pass `submit` *and* confirm at the end.
- **No guessing.** Amounts, dates, and GST come from the receipt; anything unreadable is flagged, not invented.
- **No credentials handled.** You do the login in the browser window.
- **No personal identifiers committed.** Your fund codes stay in your local `cost-centers.yaml` as placeholders here. The only preset value is Monash University's public SSO entry URL (an endpoint, not a secret) — swapped on first run if you're elsewhere.

## Files

| File                 | Purpose                                                        |
|----------------------|----------------------------------------------------------------|
| `SKILL.md`           | The skill definition and step-by-step instructions.            |
| `reference.md`       | Concur entry URL, navigation, expense-type mappings, and validation gotchas. Self-updates as the UI is learned. |
| `cost-centers.yaml`  | Your cost-center fund code(s).                                 |
| `README.md`          | This file.                                                     |
