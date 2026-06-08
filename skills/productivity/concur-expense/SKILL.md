---
name: concur-expense
description: Build a SAP Concur expense claim via Playwright — from local receipts (PDF/PNG/JPG) and/or corporate-card transactions already waiting in Concur. Each line entered or imported, allocated to a cost-center fund, receipts attached. Draft-only by default; submits only when explicitly asked and confirmed.
---

# Concur Expense Drafter
*Builds a Concur expense report from local receipts and/or corporate-card transactions, and stops before submit unless you opt in.*

## Hard rules
1. **Draft-only by default. NEVER click Submit unless the `submit` argument was passed AND the user confirms at the end (Step 6).** When in doubt, leave the draft for the user.
2. **NEVER guess receipt amounts, dates, or GST.** Extract them from the receipt. If a field is unreadable or absent, ask.
3. **Confirm extracted data with the user before touching the browser.** Cheap check, avoids garbage in Concur.
4. Login is **manual** — the user signs in (SSO + MFA) in the Playwright browser; only then proceed. Never type credentials.
5. When a report with a similar name already exists, **ask** whether to add to it or create a new one — never silently create a duplicate.

## Config
- **Cost centers:** `cost-centers.yaml` (in this skill folder). Set your own fund code(s); mark one `default: true`.
- **Concur field map / quirks:** `reference.md` (in this skill folder). Holds the entry URL, navigation, expense-type mappings, and validation gotchas. Update it after each run as the UI is learned.
- **Receipt folder:** passed as an argument, else ask.

## Arguments
- `<folder-path>` — folder of receipts (PDF/PNG/JPG/etc.). Optional in card mode; if omitted and `cards` is not passed, ask for it.
- `cards` — import corporate-card transactions already waiting in Concur ("Available Expenses" from the card feed) into the report. See **Modes** below.
- `fund:CODE` — override the default cost-center fund for the whole report.
- `report:"Name"` — set the report name up front (else ask).
- `submit` — after the draft is built and verified, ask the user for an explicit final confirmation, then click **Submit Report**. Without this argument the skill always stops at draft.

Per-line fund overrides are taken interactively at the confirm step.

## Modes
- **Receipt mode** (default): read local receipt files, create one line per receipt (Step 5).
- **Card mode** (`cards`): import card transactions Concur already holds; vendor/date/amount come from the card feed, not from reading a file (Step 5C). No local folder is required.
- **Combined** (`cards` + a folder): import the card lines, then match each local receipt to a card line by vendor + amount + date and attach it. Receipts with no matching card line are flagged for the user (entered manually only if the user confirms) — never silently create a duplicate of a card transaction.

---

## Instructions

### Step 1 — Gather and read receipts
0. **Ask the report name up front** (one report holds all the receipts in the folder, e.g. "Conference 2026"), unless given via `report:`. Also confirm the business purpose if not obvious — common ones: conference/seminar, airport trips, hotel, food (lunch/dinner/incidentals).
- **Card mode with no folder:** skip the rest of Step 1 and Step 2. Go to Step 3 (login), then Step 5C — the transaction list is read from Concur, not from local files, and confirmed there.
1. Resolve the folder (argument or ask).
2. `Glob` for `*.pdf`, `*.png`, `*.jpg`, `*.jpeg`, `*.heic` in it.
3. `Read` each receipt. For each, extract:
   - **vendor / merchant**
   - **date** (the transaction date printed on the receipt — trust the receipt over the filename if they disagree)
   - **total amount** + **currency** (the full amount paid, including booking fees / card surcharges)
   - **GST / tax** if shown
   - **expense category guess** (e.g. airfare, meals, accommodation, taxi, conference fee, software)
   - **brief description** (what it was for)
4. Flag any receipt where a field is unreadable — do not invent.

### Step 2 — Confirm with user
Present a compact table: file | vendor | date | amount | currency | category guess | fund.
- Fund column defaults from `cost-centers.yaml` (or the `fund:` argument).
- Report name already set in Step 0. Ask the user to confirm, correct any field, and override per-receipt funds if needed.
- **Do not proceed to the browser until the user confirms.**

### Step 3 — Open Concur, hand off for login
1. `browser_navigate` to the Concur entry URL in `reference.md` (defaults to Monash University's). On the **first run only**, confirm the user is at Monash; if not, ask for their institution's SAP Concur / SSO entry URL and save it to `reference.md`.
2. `browser_snapshot`. If a login / SSO page is shown, tell the user:
   *"Log in to Concur in the browser window (SSO + MFA). Tell me when you're on the Concur home page."*
3. Wait for the user. The persistent profile usually keeps the session between runs.

### Step 4 — Create or open the report
1. New report: Concur home → "Create Expense Report" → fill the header (report name, date, any required policy fields).
2. Existing report: open it from the home list, or navigate to `/nui/expense/report/<id>`, then add lines to it.
3. `browser_snapshot` after each navigation; act on what the snapshot shows. The Concur DOM is dynamic — re-snapshot rather than reuse stale element refs.

### Step 5 — Add each expense (one line per receipt)
A per-line order that avoids Concur's "saved but missing required info" popup:
1. Add Expense → Manually Create Expense → pick the expense type matching the category (see `reference.md`; if a mapping is unknown, ask once, then record it).
2. Fill all required Details fields: transaction date, business purpose, vendor, city/location, GST, total amount, plus any type-specific required fields (`reference.md` lists them per type). Leave read-only/auto-derived amount fields alone.
3. Set Receipt Status to match the GST you entered (see `reference.md` — a "GST present" status requires a non-zero GST value).
4. Attach the receipt: trigger the upload control, then `browser_file_upload` with the receipt's absolute path.
5. Click **Allocate** (this saves the entry and opens allocations) → Add → pick the cost-center fund (default from `cost-centers.yaml`, or the per-receipt override) → 100% → Save the allocation → Save the Allocate dialog.
6. **Save Expense.** A clean line shows "Show Allocation Summary" in its row; a line still needing attention shows "Show Errors" — open it and resolve.
7. Repeat for each receipt.

### Step 5C — Import corporate-card transactions (card mode)
Use this instead of Step 5 when `cards` was passed. Card lines already carry vendor, date, and amount from the card feed — never overwrite those with guesses.
1. Open the report (Step 4). Click **Add Expense**, then **Select from Available Expenses** (the menu shows a count, e.g. "Select from Available Expenses (7)"). If the count is 0, the feed has no pending charges: click **Card Transactions** on the Manage Expenses page to pull the latest, then re-check. If still 0, tell the user and stop — do not invent lines.
2. `browser_snapshot` the Available Expenses list. Each row shows expense type (often "Undefined"), vendor, date, and amount.
3. **Confirm with the user before importing:** present a compact table — vendor | date | amount | card | suggested expense type | fund. Ask which rows to import (default: all that match the report's purpose) and confirm the fund per row. Do not import until the user confirms.
4. Tick the chosen rows → **Move to** / **Add to Claim** (the selected report). They become expense lines on the report.
5. For **each** imported line, open it and finish what the feed does not provide:
   - Set the **expense type** if it is "Undefined" (map from vendor/purpose via `reference.md`).
   - Fill type-specific required fields (business purpose, city, GST, head-count fields — see `reference.md`). The amount is from the card; leave it.
   - **Allocate** → fund (default or per-row override) → 100% → Save the allocation → Save the Allocate dialog.
   - **Combined mode:** attach the matched local receipt (vendor + amount + date) via the upload control + `browser_file_upload`, and set Receipt Status to match the GST. If no receipt matches, leave it unattached and flag the line for the user.
   - **Save Expense.** Resolve any "Show Errors" before moving on.
6. Report any local receipts that matched no card line, and any card lines left without a receipt.

### Step 6 — Verify, then stop or submit
1. `browser_take_screenshot` of the finished draft.
2. Report to the user: report name & number, line count, total, fund(s) used, and any receipts skipped or flagged.
3. **If `submit` was NOT passed:** hand off — *"Draft is ready in Concur. Review and Submit yourself."* Done.
4. **If `submit` WAS passed:** show the summary and ask for an explicit yes/no confirmation to submit (submission is outward-facing and hard to reverse). Only on an explicit "yes":
   - Click **Submit Report**.
   - Handle any policy/agreement confirmation dialog that appears (read it; proceed only if it is the expected submit confirmation).
   - `browser_snapshot` to confirm the report status changed to Submitted; screenshot and report the result.
   - If a blocking validation error prevents submission, do not force it — report the error and leave the draft.

### Step 7 — Learn
If anything in the UI differed from `reference.md` (button labels, field names, type mappings, the URL, popups), update `reference.md` so the next run is smoother. Never record credentials, session tokens, or personal fund/grant identifiers beyond what `cost-centers.yaml` already holds.

---

## Failure handling
- Selector/ref not found → re-`browser_snapshot`, find the current element, retry once. If still failing, screenshot and ask the user.
- Session expired mid-run → pause, ask the user to re-auth, resume from the last saved line.
- Receipt file rejected by Concur (size/format) → flag to user, continue with the rest.
- A "Submit" confirmation appears unexpectedly (and `submit` was not requested) → **cancel/close it** — never confirm.
