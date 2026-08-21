---
name: overleaf
description: Work on an Overleaf LaTeX project — read the source, apply edits as tracked-change suggestions, compile, and keep an optional Dropbox mirror in sync. Overleaf has no API, so edits are made in the user's logged-in Chrome tab via the Claude-in-Chrome extension. Use when the user asks to edit, review, draft, or compile a paper that lives on Overleaf, mentions overleaf.com, or points at a folder under Dropbox/Apps/Overleaf.
argument-hint: "[what to change, plus the Overleaf project URL or name]"
---

# Overleaf

*Edits an Overleaf project as suggestions by default. Reads fast from a local Dropbox mirror; writes through the browser so changes land as tracked changes.*

## Hard rules

1. **Suggestion by default.** Every edit is a tracked change unless the user passed `direct` for this run. State which mode is active before the first edit and never switch modes mid-task without saying so.
2. **Never write to the Dropbox mirror without a freshness check completed in this session** for that project (Step 2). Overleaf pushes web edits to Dropbox only every 10–20 minutes, so an unverified local file is stale and writing to it silently destroys newer web edits.
3. **Never rename, move, or delete a file through the Dropbox mirror.** Overleaf reads those as delete-and-create and, in its own words, that causes "a loss of history, tracked changes, and comments." Renames, moves, and deletions go through the Overleaf file tree in the browser.
4. **Never put a compiled PDF into the mirror folder.** Overleaf's docs: "Never manually upload a compiled PDF into your Overleaf project."
5. **Never handle credentials.** The user is already signed in to Overleaf in their own Chrome. If they are not, ask them to sign in and stop until they confirm.
6. **Verify from Overleaf.** An edit is not done until it has been re-read from the Overleaf document (or from the mirror after a confirmed round trip). A green save indicator is not verification.
7. **Do not delete or accept another person's tracked changes or comments.** Resolving a co-author's suggestion is the user's call, never a side effect of your edit.

## Surfaces

| Surface | Use for | Never use for |
|---|---|---|
| **Chrome** (`mcp__claude-in-chrome__*`) — the user's real, signed-in Chrome | All writes in `suggest` mode; file tree operations; compiling; reading the review panel and history; forcing a Dropbox sync | Reading a long file in full — see the CodeMirror caveat below |
| **Dropbox mirror** (`~/Dropbox/Apps/Overleaf/<Project>/`) — optional | Fast, complete, reliable reads; `markup`-mode writes; grep across the project; running `latexdiff` | Any write in `suggest` mode; any rename, move, or delete |

The Overleaf editor is CodeMirror, which renders only the visible lines. `read_page` and `get_page_text` return **what is on screen, not the file**. Never treat a browser read as the whole document. Read the full source from the mirror; if there is no mirror, ask the user before downloading the project source and read the zip.

Load the browser tools in **one** ToolSearch call before any browser work:

```
select:mcp__claude-in-chrome__tabs_context_mcp,mcp__claude-in-chrome__navigate,mcp__claude-in-chrome__computer,mcp__claude-in-chrome__read_page,mcp__claude-in-chrome__find,mcp__claude-in-chrome__form_input,mcp__claude-in-chrome__get_page_text,mcp__claude-in-chrome__list_connected_browsers,mcp__claude-in-chrome__select_browser,mcp__claude-in-chrome__switch_browser
```

Do not substitute another browser surface. The in-app Browser pane, Playwright, computer-use clicking, and `WebFetch` either lack the signed-in session or cannot reach it. A "not connected" error is not grounds to give up — work the ladder in Step 0 first.

## Edit modes

| Mode | Where the edit is made | How it appears | Use for | Undone by |
|---|---|---|---|---|
| `suggest` **(default)** | Overleaf editor, **Reviewing** mode on | Native Overleaf tracked change | Targeted edits: sentences, paragraphs, numbers, citations, captions | Reject in the review panel |
| `markup` | Mirror file, or typed in the browser | `\added{}` / `\deleted{}` / `\replaced{}`, or sentinel-commented blocks, visible in the compiled PDF | Bulk insertions where typing into the browser is impractical: a new section, a long table, a full appendix | `scripts/resolve-markup.py --reject` |
| `direct` | Either | An ordinary, untracked edit | Only when the user explicitly asks: solo drafts, mechanical fixes they do not want to review | Overleaf History |

`direct` is opt-in per run and never inferred. When the user asks for it, say once what they lose: no per-change accept/reject, and the only record is the project history.

**Tracked changes and Dropbox sync are Overleaf premium features.** If `suggest` is unavailable — free plan, or the mode switcher only offers Editing — say so and offer `markup` instead, which needs no subscription. Never silently downgrade to `direct`.

**Never mix `suggest` and mirror writes in the same project.** Overleaf warns that pushes from an integration "can result in the loss or displacement of track changes and comments," and advises against mixing sync with track changes. In `suggest` mode the mirror is read-only.

## Instructions

### Step 0 — Connect the browser, then confirm the session is signed in

Both halves fail quietly and waste a run if skipped.

**Connect.** `tabs_context_mcp` reporting "Claude in Chrome is not connected" usually means *this session has not selected a browser yet*, not that the extension is missing. Work the ladder in order and report a problem only at the end of it:

1. `list_connected_browsers`.
2. One entry → `select_browser` with its `deviceId`. Several → list them and let the user choose, preferring `isLocal: true`.
3. Empty list → `switch_browser`, which broadcasts a pairing request; the user clicks **Connect** in the Chrome side panel.
4. Still nothing → only now is the extension genuinely absent or signed out. Point the user at the Chrome Web Store listing (`fcoeoabgfenejglbffodgkkbkcdhcgfn`) and stop.

**Never tell the user to install the extension before step 3 has failed.** Retrying `tabs_context_mcp` a second time is not the ladder; it returns the same error while a browser sits there unselected.

**Authenticate.** Navigate to `https://www.overleaf.com/project` and confirm the dashboard loads. If the URL turns into `/login`, or the page shows a Log in form, stop there:

- Never type an email, password, or SSO credential — hard rule 5.
- Ask the user to sign in **in that tab**, and wait for them to confirm before continuing.
- If they say they are already signed in, the extension is very likely driving a different Chrome profile than the one holding their Overleaf session. `list_connected_browsers` returns one entry per connected extension instance, not one per profile, so a single entry is not evidence that the right profile is in use. Say this rather than asking them to log in again.
- Leave any cookie or consent banner alone. Accepting it is the user's call, not a step in this workflow.

### Step 1 — Resolve the project

1. Read the registry — `~/.config/overleaf-skill/projects.yaml` if it exists, otherwise the `projects.yaml` template in this skill folder. Match the user's argument against `name`, `url`, or `mirror`.
2. If the argument is a path under a mirror root, take the first directory below the root as the project.
3. If nothing matches, run **Setup** (below) before continuing.
4. Restate the target: project name, URL, main file, mirror path (or "no mirror"), and the active edit mode. Do not start editing until this is stated.

### Step 2 — Freshness (before any local read that informs an edit, and before any local write)

Skip only if the project has no mirror.

1. Open the project in Chrome — reuse an existing tab whose URL matches the project id; open one only if none exists.
2. Left rail → **Integrations** → **Dropbox**. The dialog states the project's real Dropbox folder and whether Overleaf has pushed all updates; if it has not, click the **"sync this project now"** link.
3. Wait for the local folder to settle: poll the newest mtime under the mirror directory until it stops changing (typically 5–30 s; give it 90 s before reporting a problem).
4. Stamp it: `python3 hooks/overleaf-freshness.py --stamp "<mirror-dir>"`.
5. If a `(Conflicted copy ...)` file appeared, stop and follow the conflict procedure in `reference/dropbox-sync.md`. Never merge one blind.

Now the local copy matches Overleaf and can be read or written.

### Step 3 — Read and locate

1. Read the relevant file(s) from the mirror. Grep across the project for the passage, macro, label, or citation key rather than reading every file.
2. Identify the exact anchor text you will edit — enough surrounding words to be unique in the file. You will use this string to find the spot in the browser.
3. If there is no mirror: ask the user before downloading, then use `File → Download` and read the extracted zip.

### Step 4 — Draft, then confirm

Show the user the proposed edit as a before/after (or the full block for an insertion) **before touching the browser**. Cheap check, and it is the last point at which a wrong edit costs nothing.

Match the surrounding LaTeX: the project's own macros, citation style (`\citep` vs `\parencite`), label conventions, and table/figure idiom. Do not introduce a package the project does not already load unless you say so and the user agrees.

### Step 5 — Apply

**`suggest` mode:**

1. Set the editor to **Reviewing** via the mode switcher at the right end of the editor toolbar (click its chevron; when the PDF pane is open it is a pencil icon). Confirm it reads Reviewing before typing — an edit made in Editing mode is untracked and cannot be retroactively tracked.
2. Turn off **auto-close brackets** in `File → Settings` for the duration. Left on, it doubles the closing braces of every macro you type. Restore the setting afterwards.
3. Locate the anchor with the editor's own find (`Cmd/Ctrl+F`), close the find bar, then select the span to replace and type the replacement. For an insertion, place the cursor and type.
4. Apply one edit at a time. Re-read the page after each — the DOM is dynamic and refs go stale.

**`markup` mode:** follow `reference/markup-mode.md`. Inline changes use the macros; whole blocks use the sentinel comments, which survive tables, figures, and verbatim where a macro argument would not. Write to the mirror only after Step 2, then complete Step 6.

**`direct` mode:** as `suggest`, but in Editing mode; or as `markup` without the wrappers. Snapshot the file first (`cp` to a `.bak` outside the mirror) when writing locally.

### Step 6 — Round-trip and verify

For a browser edit:
1. Confirm Overleaf shows the document saved, then reload the project page and re-read the edited region.
2. Confirm the change is present, is marked as a tracked change (in `suggest` mode), and that nothing adjacent moved.

For a mirror edit:
1. Confirm Dropbox finished uploading the file.
2. Reload the project in Chrome and read the edited region **from Overleaf** — do not trust the local file as evidence that Overleaf received it. Allow up to a minute.
3. Re-stamp freshness.

### Step 7 — Compile and report

1. Click **Recompile** and wait for the run to finish.
2. If it fails, read the log panel, report the first real error with its file and line, and fix it in the same mode as the edit.
3. Report: what changed, in which files, in which mode, whether it compiled, and anything you noticed but did not touch.

## Setup (first run for a project)

1. Ask for the Overleaf project URL, or open `https://www.overleaf.com/project` and let the user name it.
2. Determine whether it is mirrored: open **Integrations → Dropbox** and read the folder path the dialog states. That path is authoritative — Overleaf appends a number when project names collide, so a matching folder name proves nothing. If the integration is not linked, there is no mirror.
3. Determine the main file (the one with `\documentclass`, unless the project sets a different main document).
4. Check whether the mode switcher offers **Reviewing**. Record `tracked_changes: yes|no`.
5. Append the project to `~/.config/overleaf-skill/projects.yaml`, seeding that file from the skill folder's `projects.yaml` if it does not exist yet. **Never write project entries into the skill folder** — it is often a checkout of a shared repository.
6. Offer the freshness hook if it is not installed (see `README.md`), and offer the `rules.dropboxignore` entries in `reference/dropbox-sync.md` if compiled output is syncing.

## Reference

| File | What it holds |
|---|---|
| `reference/editor-ui.md` | Overleaf UI mechanics: layout, mode switcher, review panel, file tree, history, compile, settings that break typed LaTeX |
| `reference/dropbox-sync.md` | Sync semantics, latency, the staleness failure mode, conflicts, `rules.dropboxignore`, rename/move hazards |
| `reference/markup-mode.md` | The suggestion macros, the sentinel-block form, preamble options, and how to resolve them |
| `projects.yaml` | Template for the registry. The live copy is `~/.config/overleaf-skill/projects.yaml` |
| `hooks/overleaf-freshness.py` | Opt-in PreToolUse guard that blocks stale writes to the mirror |
| `scripts/resolve-markup.py` | Accepts or rejects `markup`-mode suggestions in a file |

Update `reference/editor-ui.md` when the Overleaf UI moves under you. It is meant to drift and be corrected.
