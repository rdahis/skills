---
name: moodle
description: Administer a Moodle course through the user's logged-in Chrome tab via the Claude-in-Chrome extension. Moodle's web services are usually disabled for staff, so every change is made in the browser and re-read from Moodle to verify it. Use for course editing, activity duplication, quiz and assignment configuration, dates and availability, Safe Exam Browser settings, maximum grades, manual gradebook entry from a spreadsheet, groups, section placement, visibility, and inline learning resources.
argument-hint: "[what to change, plus the Moodle URL or course name]"
---

# Moodle

*Operates Moodle through the user's signed-in Chrome tab, makes the smallest requested change, and verifies every saved value from Moodle itself.*

Adapted from a Moodle administration skill by **Klaus Ackerman** (Monash
University), which is the original source for the workflow and the safety
constraints below.

## Hard rules

1. **Smallest possible mutation.** Change only the fields the user asked for. Every other setting is preserved from the reference activity, exactly as it was found.
2. **Verify from Moodle.** A change is not done until it has been re-read from a reloaded Moodle page. A success banner is not verification; a missing banner is not failure. The re-read value decides.
3. **Never delete or reset.** No deleting activities, submissions, attempts, grades, users, groups, or enrolments; no resetting attempts. Only on an explicit request naming that exact deletion.
4. **Never act outward without confirmation in chat.** Releasing grades, submitting final grades, and sending student notifications are irreversible and visible to students. Ask, then wait for a clear yes.
5. **Never handle credentials.** The user is already signed in to Moodle in their own Chrome. If they are not, ask them to sign in and stop until they confirm. Never read cookies, storage, profiles, or saved passwords.
6. **Never bypass the forms.** Moodle validates, recalculates, and logs on save. Drive the visible tab; `read_network_requests` is for inspection only, never for issuing a mutating call.
7. **Stop on ambiguity.** If the course, week, activity, student identity, grade scale, or target field is uncertain, stop before saving and ask.
8. **Match students by stable ID.** Student ID or Moodle user ID, never by display name or email spelling.

## Surfaces

| Surface | Use for | Never use for |
|---|---|---|
| **Chrome** (`mcp__claude-in-chrome__*`) — the user's real, signed-in Chrome | Everything: reading course state, editing forms, gradebook entry, uploads, verification | — |
| **`anthropic-skills:xlsx`** | Reading `.xlsx` / `.xls` workbooks that supply grades, IDs, groups, or dates | Writing back to Moodle |
| Local file reads | `.csv` / `.tsv` inputs | Anything requiring the authenticated session |

Load the browser tools in **one** ToolSearch call before any browser work:

```
select:mcp__claude-in-chrome__tabs_context_mcp,mcp__claude-in-chrome__navigate,mcp__claude-in-chrome__computer,mcp__claude-in-chrome__read_page,mcp__claude-in-chrome__find,mcp__claude-in-chrome__form_input,mcp__claude-in-chrome__get_page_text,mcp__claude-in-chrome__read_network_requests
```

Add `file_upload` to the same call when the task uploads a file. If a needed tool was missed, issue one more ToolSearch — never load tools one at a time.

Do not substitute another browser surface. The in-app Browser pane (`mcp__Claude_Browser__*`), Playwright, computer-use clicking, and `WebFetch` either lack the signed-in session or cannot reach it. If the Chrome extension is not connected, ask the user to connect it and stop until they confirm.

## Config

- **Courses:** `courses.yaml` in this skill folder is a template. The live registry is `~/.config/moodle-skill/courses.yaml`; copy it there on first use and append an entry each time a new course is met. It holds the Moodle site URL and the course id behind each shorthand the user says ("PPS", "the honours seminar").
- **Site URL:** the template defaults to Monash's `https://learning.monash.edu`. On first run at a different institution, ask for the site URL and write it into the live registry.
- **UI mechanics:** `reference/moodle-ui.md` — navigation paths, form quirks, and validation gotchas. Update it after each run as the UI is learned.
- **Task recipes:** `reference/workflows.md` — duplicating activities, quizzes and Safe Exam Browser, manual gradebook entry, maximum grades, groups, and inline resources.

## Chrome session rules

- List tabs with `tabs_context_mcp` and reuse an existing tab on the Moodle site whose URL or title matches the intended target. Open a new tab with `tabs_create_mcp` + `navigate` only if none exists.
- Prefer semantic locators: `find` and `read_page` refs, labels, element IDs, names, and Moodle data attributes. Avoid coordinate clicking wherever a stable DOM target exists.
- For large gradebook or participant tables, use targeted DOM inspection (`find`, scoped `read_page`) rather than a full-page snapshot — a full snapshot is slow and exposes thousands of unrelated student fields.
- Reacquire page state with `read_page` after every navigation or save. Never trust an element ref or a value captured before a reload.

## Instructions

### Step 1 — Define the exact mutation

Resolve, and state back to the user:

- Course and section, from the URL, `courses.yaml`, or the user's words. A user-supplied URL is authoritative; if the URL and the visible page disagree, stop and resolve the mismatch before editing.
- The activity, grade item, quiz, group, or resource being changed.
- The requested names, dates, times, grades, permissions, and visibility.
- The reference activity whose settings must otherwise be copied.
- The timezone Moodle itself displays — confirm it before setting any date, rather than assuming the user's local zone.
- For batch work: the source file and the stable matching key.

### Step 2 — Inspect before changing

Read current Moodle state and record enough to detect an unintended change:

- Course and activity ids, and the visible names.
- Current values of every setting the task touches.
- Grade-item id and maximum grade.
- Any existing nonblank student grade, before it is replaced.
- Source and destination sections, for a duplication.
- Current group membership and counts.
- Open, due, cutoff, close, and availability dates.
- For quizzes: the reference restrictions, attempts, review options, and Safe Exam Browser configuration.

For a repeated weekly activity, inventory every relevant week first, so missing or inconsistent items surface before any edit begins.

### Step 3 — Validate batch data

For spreadsheet-driven work, before opening Moodle:

1. Inspect the workbook and render the relevant sheet.
2. Preserve student IDs as text and grades as numbers.
3. Confirm row count, duplicates, missing IDs, blank grades, the grade range, and the Moodle maximum.
4. Match students by stable student ID or Moodle user ID.
5. Report and stop on unmatched or duplicate IDs, unless the user supplies the resolution.
6. Note harmless display-name differences while keeping the stable ID as the source of truth.

Produce an exact `identifier → target value` mapping and show it to the user before touching Moodle.

### Step 4 — Apply bounded changes

- Prefer one grouped save over several partial saves when Moodle presents a single form.
- For a large batch, work in bounded groups that can be verified and retried independently without duplicating work.
- Do not change course-wide grade calculations, aggregation, weights, visibility, or completion rules merely to make an individual task easier.
- Keep a draft hidden only when the user asks for that or the copied reference is hidden; otherwise preserve visibility.

### Step 5 — Save and verify

After each save:

1. Wait for navigation or async completion.
2. Reopen, refresh, and re-read the saved page.
3. Compare every requested value against the prepared mapping or the reference activity.
4. Confirm item names and ids, so an adjacent column or week was not changed instead.
5. Check Moodle's validation and field-level errors.

Do not report completion until every requested value re-reads correctly from Moodle.

### Step 6 — Report

State what changed, how many items or students were affected, what was verified, and any exceptions — including overwritten nonblank grades and any display-name differences between the source file and Moodle. Do not include student data beyond what the task and its verification require.

## Common workflows

See `reference/workflows.md` for the step-by-step recipes:

| Workflow | What it covers |
|---|---|
| Duplicate a weekly activity | Duplicate, rename, move to section, update only week-specific fields, compare against the reference |
| Create or repair a quiz | The full setting checklist, including Safe Exam Browser and review options |
| Enter manual quiz grades | When manual override is appropriate, and the single-save entry and verification loop |
| Change maximum grades | Activity setting versus grade item, and the rescaling risk on a populated item |
| Manage groups | Create missing groups, match by student ID, verify counts and membership |
| Embed a PDF or presentation inline | Why `<iframe>` does not guarantee inline PDF rendering, and what to use instead |
