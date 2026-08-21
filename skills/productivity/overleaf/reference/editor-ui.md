# Overleaf editor: driving it from Chrome

Mechanics of the Overleaf web editor as operated through the Claude-in-Chrome
extension. Correct this file when the UI moves.

## URLs

| Target | URL |
|---|---|
| Project dashboard | `https://www.overleaf.com/project` |
| A project | `https://www.overleaf.com/project/<project-id>` |
| Account settings (Dropbox / GitHub linking) | `https://www.overleaf.com/user/settings` |

The 24-character hex `<project-id>` in the editor URL is the stable identifier.
Project *names* are not unique and change; store the id in `projects.yaml`.

Self-hosted and enterprise instances (Overleaf Server Pro) use the same paths on
a different host. Take the host from the URL the user gives you.

## Layout

- **Left rail** — file tree at the top; below it the **Integrations** section
  (Dropbox, GitHub, Git), **History**, and the chat/review toggles. On narrow
  windows the rail collapses to icons; widen the window rather than guessing.
- **Centre** — the source editor (CodeMirror 6).
- **Right** — the PDF preview and, above it, **Recompile**.
- **Top right** — the editor **mode switcher** and **Share**.
- **Top left** — **Menu**, holding Settings, Download, and project actions.

## The mode switcher

Options, depending on the user's access level:

- **Editing** — ordinary edits, untracked.
- **Reviewing** — every edit is recorded as a tracked change. This is
  `suggest` mode.
- **Viewing** — read-only.

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

Menu → Settings:

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
comes from the Dropbox mirror, or from Menu → **Download** → **Source** (ask the
user before downloading).

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

## Compiling

**Recompile** runs the compile; the log panel below the preview holds the
errors. Read the first genuine error — later ones are usually cascade. The
compiler (pdfLaTeX / XeLaTeX / LuaLaTeX) is set in Menu → Settings and in
`latexmkrc` when the project has one.

## History

Menu → History (or the History entry in the left rail) shows versions, labels,
and who made each change. Use it to confirm what a Dropbox sync actually landed,
and to find the state before an accident. Restoring a version is destructive to
anything after it — surface the option, let the user do it.

## Boundaries

- Interact through the visible UI. Do not issue mutating HTTP requests, replay
  network calls, or drive Overleaf with copied session credentials.
- Read-only inspection of network traffic is acceptable for diagnosis only.
- Never inspect cookies, local storage, saved passwords, or profile data.
- Reuse the user's existing tab for the project; do not open duplicate editor
  tabs on the same project, which can produce competing sessions.
