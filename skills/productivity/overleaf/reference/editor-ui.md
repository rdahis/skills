# Overleaf editor: driving it from Chrome

Mechanics of the Overleaf web editor as operated through the Claude-in-Chrome
extension. Correct this file when the UI moves.

## URLs

| Target | URL |
|---|---|
| Project dashboard | `https://www.overleaf.com/project` |
| A project | `https://www.overleaf.com/project/<project-id>` |
| Account settings (Dropbox / GitHub linking) | `https://www.overleaf.com/user/settings` |
| Login (a redirect here means the session is signed out) | `https://www.overleaf.com/login` |

The 24-character hex `<project-id>` in the editor URL is the stable identifier.
Project *names* are not unique and change; store the id in `projects.yaml`.

Self-hosted and enterprise instances (Overleaf Server Pro) use the same paths on
a different host. Take the host from the URL the user gives you.

## Connection and session

Two preconditions, both of which fail in ways that look like something else.

**The extension must be selected, not merely installed.** A "Claude in Chrome is
not connected" error from `tabs_context_mcp` most often means this session has
not picked a browser yet. The ladder:

| Step | Call | Meaning |
|---|---|---|
| 1 | `list_connected_browsers` | Each entry is one connected extension instance: `deviceId`, `name`, `osPlatform`, `isLocal` |
| 2 | `select_browser` | Attach to a known `deviceId`. Prefer `isLocal: true` |
| 3 | `switch_browser` | Broadcasts a pairing request; the user clicks **Connect** in the Chrome side panel. Waits up to two minutes |
| 4 | — | An empty list after step 3 is the only evidence the extension is absent |

Retrying `tabs_context_mcp` is not a diagnostic — it returns the same error while
an unselected browser sits waiting. Check the list before saying anything about
installation.

**Profiles.** The list reports one entry per connected extension instance, not
one per Chrome profile. A single entry therefore proves nothing about *which*
profile is being driven. When a user insists they are signed in but the tab shows
the login page, a profile mismatch is the most likely explanation: the extension
is connected from a profile without the Overleaf session. The fix is theirs —
connect the extension from the profile that holds the session.

**Signed-in state.** Navigating to `/project` while signed out silently redirects
to `/login`. Confirm the dashboard actually loaded before searching for a project;
a `find` that reports "no such project" on a login page is a misleading result.
Never type credentials, and leave the cookie banner to the user.

## Layout

- **Top left** — a menu bar: **File, Edit, Insert, View, Format, Help**. Not a
  single "Menu" button; older documentation says otherwise.
- **Left rail** — five icon tabs, top to bottom: **File tree**, **Project
  search**, **Integrations**, **Review panel**, **Chat**. History is *not* here
   — it lives under File. Below the file tree sits a **File outline** pane.
- **Centre** — the source editor (CodeMirror 6), with a **Code / Visual** toggle
  and the mode switcher at the right end of its toolbar.
- **Right** — the PDF preview and, above it, **Recompile** with a warnings count.
- **Top right** — **Share**, history, and account controls.

The File menu holds: New file, New folder, Upload file, Make a copy, **Show
version history**, Word count, Submit, **Download**, **Settings**. So the paths
this skill needs are `File → Settings`, `File → Download`, and
`File → Show version history`.

## The mode switcher

It sits at the **right end of the editor toolbar**, beside the Code/Visual
toggle — not in the window's top-right corner. When the PDF pane is open it
collapses to a pencil icon with a chevron; click the **chevron** to open it.
Clicking the label itself may only collapse or expand the control.

Options, depending on the user's access level:

- **Editing** — "Edit content directly". Ordinary edits, untracked.
- **Reviewing** — "Edits become suggestions". Every edit is recorded as a
  tracked change. This is `suggest` mode.
- **Viewing** — read-only. Absent from the menu for users with edit access, so
  a two-item menu is normal and not a sign of a missing plan.

Users with review-only or view-only access cannot switch. If **Reviewing** is
absent for a user with edit access, the project is not on a plan that includes
track changes; report that rather than falling through to an untracked edit.

The project owner can force tracking for named collaborators through the
sharing permissions dialog, so a collaborator may be tracked without touching
the switcher.

**Check the switcher reads Reviewing immediately before typing.** Mode is per
user per project and survives reloads, but a second tab, a fresh session, or a
permissions change can reset it. An edit typed in Editing mode is a plain edit
and cannot be converted into a suggestion afterwards.

## Settings that break typed LaTeX

File → Settings:

- **Auto-close brackets** — on by default. It inserts a matching `}` as you
  type `{`, so typing `\added{text}` yields `\added{text}}`. Turn it off before
  typing LaTeX and restore it afterwards.
- **Auto-complete** — offers macro completions that can swallow keystrokes in a
  long insertion. Turn it off for bulk typing.
- **Code check** — only draws warnings; harmless, leave it.

After each typed edit, read back the exact line you touched and count the
braces. Doubled or missing braces are the most common failure here.

## Finding a spot in the file

The editor renders only the visible lines, so scrolling and screen reading are
unreliable for locating text in a long document. Use the editor's own search:

1. Click into the editor pane.
2. `Cmd+F` (macOS) / `Ctrl+F` — Overleaf's find bar, not the browser's.
3. Type a distinctive anchor string taken from the mirror copy of the file.
4. `Enter` to jump, `Esc` to close the find bar, which leaves the cursor at the
   match.
5. Select the span with `Shift`+arrows or a click-then-shift-click, then type.

Overleaf's find bar also offers replace. Prefer it over hand-selection for a
short, unambiguous string — but confirm the match count first, and never use
replace-all on a string that appears more than once.

**Never read a file's contents out of the editor DOM and treat it as the file.**
`read_page` and `get_page_text` return rendered lines only. The complete source
comes from the Dropbox mirror, or from `File → Download` (ask the user
before downloading).

## The review panel

Tracked changes and comments appear in the right-hand review panel, each with
the author and a timestamp.

- **Accept / reject:** select the text containing the changes — `Cmd+A` /
  `Ctrl+A` for the whole file — then use **Accept selected changes** or
  **Reject selected changes**. A confirmation dialog follows.
- Only act on a suggestion when the user asked for that specific resolution.
  Never accept or reject a co-author's change as a side effect of your own edit.
- To leave a comment rather than an edit: select the text and add a comment from
  the review panel. A comment is the right output when the point is a question
  for a co-author, not a change.

Copying a project applies all tracked changes in the copy and drops the
suggestion state. Warn the user before duplicating a project mid-review.

## File tree operations

Renames, moves, new files, and deletions are done here — never through the
Dropbox mirror. Right-click a file for the menu. After any of these, force a
Dropbox sync so the mirror follows, and re-stamp freshness.

The panel's toolbar holds three creation controls, left to right: **new file**,
**new folder**, **upload**. All three, and `File → Upload file`, open the same
**Add files** dialog (tabs: New file, Upload, From another project, From
external URL, From ReadCube, From Zotero, From Mendeley).

The dialog gives no indication of where the file will land: the destination is
whatever the file tree has selected when it opens. Its drop zone is an Uppy
Dashboard with two hidden file inputs — the first accepts files, the second a
folder. Drive the first with `file_upload`; the visible "Select files" link opens
a native picker that cannot be operated. Full procedure in `SKILL.md`.

Sorting puts folders before files at every level, so a root-level file renders
below the entire expanded subtree of the last root folder. Judge placement by
indentation, not position.

A same-name upload is caught: the drop zone turns red and offers **Cancel** or
**Overwrite** rather than replacing the file or appending a suffix. Cancel is
non-destructive and leaves no duplicate behind.

## Compiling

**Recompile** runs the compile; the log panel below the preview holds the
errors. Read the first genuine error — later ones are usually cascade. The
compiler (pdfLaTeX / XeLaTeX / LuaLaTeX) is set in Menu → Settings and in
`latexmkrc` when the project has one.

## History

`File → Show version history` shows versions, labels,
and who made each change. Use it to confirm what a Dropbox sync actually landed,
and to find the state before an accident. Restoring a version is destructive to
anything after it — surface the option, let the user do it.

## Promotional overlays are invisible to the tools

Overleaf shows feature-promo modals ("Did you know Overleaf supports PDF
tagging?", Library tooltips) that render **outside the accessibility tree**.
The consequences are specific and confusing:

- `find` reports the dialog does not exist, and `read_page` does not list its
  close button.
- A coordinate click on its X does nothing.
- A `ref` click on an element *behind* it reports success and has no effect —
  the page does not navigate, and nothing indicates why.

Symptom to recognise: a click that "succeeded" while the URL and the screenshot
stay unchanged. Press **Escape**, take a screenshot to confirm the overlay is
gone, then repeat the click. Screenshot before concluding a click failed for
some other reason — this overlay class is the usual cause.

## Boundaries

- Interact through the visible UI. Do not issue mutating HTTP requests, replay
  network calls, or drive Overleaf with copied session credentials.
- Read-only inspection of network traffic is acceptable for diagnosis only.
- Never inspect cookies, local storage, saved passwords, or profile data.
- Reuse the user's existing tab for the project; do not open duplicate editor
  tabs on the same project, which can produce competing sessions.
