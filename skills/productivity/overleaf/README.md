# overleaf

A [Claude Code](https://claude.com/claude-code) skill for working on an Overleaf
LaTeX project. Claude reads the source, drafts the edit, applies it **as a
tracked-change suggestion** in your own browser, compiles, and verifies the
result from Overleaf itself.

Overleaf has no public API, so edits go through a tab in your real, signed-in
Chrome via the Claude-in-Chrome extension. If you sync the project to Dropbox,
the local mirror is used as a fast, complete read surface — with a guard against
the one failure mode that makes that dangerous.

## Why it is built this way

Two facts from Overleaf's own documentation shape the whole design:

1. **Overleaf pushes web edits to Dropbox only every 10–20 minutes.** An agent
   that reads your local `main.tex`, edits it, and writes it back inside that
   window silently overwrites everything you typed on overleaf.com since the
   last push. Deleted paragraphs come back; recent work disappears.
2. **Sync integrations and track changes do not mix.** Overleaf warns that
   pushes from Git — and the delete-and-create paths Dropbox takes on renames —
   "can result in the loss or displacement of track changes and comments."

So: **the browser is the write surface, the mirror is the read surface**, and a
forced sync plus a freshness stamp sits between them.

## What it does

- Resolves "the paper" to an Overleaf project, its main file, and its local
  mirror, from a registry you build up as you go.
- Forces **Integrations → Dropbox → Sync this project now** before reading or
  writing locally, then waits for the folder to settle.
- Applies edits as **native tracked changes** by default, so every change is a
  suggestion your co-authors accept or reject in the review panel.
- Falls back to **markup mode** for bulk edits — `\added{}`, `\deleted{}`,
  `\replaced{}`, and sentinel-commented blocks that compile, are visible in the
  PDF, and resolve with one command.
- Verifies every edit by re-reading it from Overleaf, then recompiles and
  reports the log.
- Refuses to rename, move, or delete through the mirror, because Overleaf reads
  those as delete-and-create and loses history, tracked changes, and comments.

## Requirements

- **Claude Code** with the **Claude-in-Chrome** extension connected. The skill
  drives a tab in your own Chrome, reusing your existing Overleaf session; it
  never handles credentials. Connect the extension from the Chrome **profile**
  that holds your Overleaf login — the extension reports one connection per
  instance, not per profile, so a connected browser can still be driving the
  wrong profile and land on the login page.
- An **Overleaf** account. Tracked changes and Dropbox sync are premium
  features — without them the skill still works, using markup mode and the
  browser only.
- **Python 3** for the hook and the markup resolver. No third-party packages.
- Optional: the **Dropbox desktop client** with your Overleaf projects synced to
  `Apps/Overleaf`.

## Installation

Quickest — the [`skills`](https://www.npmjs.com/package/skills) CLI:

```bash
npx skills@latest add rdahis/skills
```

…then select `overleaf`.

Manual alternative:

```bash
git clone https://github.com/rdahis/skills.git
cp -r skills/skills/productivity/overleaf ~/.claude/skills/
```

## Configuration

1. **The registry.** Copy the template out of the skill folder, then list
   every Dropbox root you use:

   ```bash
   mkdir -p ~/.config/overleaf-skill
   cp ~/.claude/skills/overleaf/projects.yaml ~/.config/overleaf-skill/projects.yaml
   ```

   The default root assumes `~/Dropbox/Apps/Overleaf`; business and team
   installs differ (`~/Acme Dropbox/Jane Doe/Apps/Overleaf`). Leave
   `projects: []` — the skill appends entries as it meets projects. Keeping the
   live registry in `~/.config` means reinstalling the skill never clobbers it,
   and your project list never lands in a repository.

2. **Keep build artifacts out of the sync.** Add the `rules.dropboxignore`
   entries listed in `reference/dropbox-sync.md`, or compiled PDFs and `.aux`
   files will generate conflicts.

3. **The freshness guard (recommended).** The protocol in `SKILL.md` protects
   you while the skill is running. The hook protects you always — including in
   sessions where you never invoked the skill. Add to `~/.claude/settings.json`:

   ```json
   {
     "hooks": {
       "PreToolUse": [
         {
           "matcher": "Write|Edit|MultiEdit|NotebookEdit|Bash",
           "hooks": [
             {
               "type": "command",
               "command": "python3 \"$HOME/.claude/skills/overleaf/hooks/overleaf-freshness.py\""
             }
           ]
         }
       ]
     }
   }
   ```

   It denies any write to a mirrored project that has not been verified fresh in
   the last 15 minutes, and explains how to clear the block. It fails open on
   any internal error, so a broken hook never stops your work.

   ```bash
   python3 hooks/overleaf-freshness.py --roots   # what it is watching
   python3 hooks/overleaf-freshness.py --list    # current stamps
   ```

   Environment overrides: `OVERLEAF_MIRROR_ROOTS` (colon-separated),
   `OVERLEAF_FRESHNESS_TTL_MINUTES`, `OVERLEAF_GUARD_READS=1` to also prompt on
   stale reads.

## Usage

```
/overleaf tighten the identification paragraph in section 3 — https://www.overleaf.com/project/<id>
/overleaf add the new robustness table to the appendix    markup
/overleaf fix the broken \ref in the conclusion           direct
```

Arguments are free text: what you want changed, plus the project URL or a name
already in `projects.yaml`. The trailing keyword picks the edit mode.

| Mode | Where the edit lands | How it appears | Best for |
|---|---|---|---|
| `suggest` *(default)* | Overleaf editor, Reviewing mode | Native tracked change | Sentences, numbers, citations, captions |
| `markup` | Mirror file or browser | Visible `\added` / `\deleted` markup in the PDF | New sections, long tables, appendices |
| `direct` | Either | An ordinary untracked edit | Solo drafts, mechanical fixes |

Resolving markup afterwards:

```bash
python3 scripts/resolve-markup.py paper/main.tex --list
python3 scripts/resolve-markup.py paper/main.tex --accept
python3 scripts/resolve-markup.py paper/main.tex --reject --label referee-2
```

## Safety

- **Suggestions by default.** `direct` is opt-in per run and never inferred.
- **No stale writes.** A forced sync and a freshness stamp precede every local
  write; the optional hook enforces this outside the skill too.
- **No destructive sync operations.** Renames, moves, and deletions go through
  the Overleaf file tree, never the mirror.
- **No credentials handled.** You are already signed in; the skill drives your
  tab and never touches cookies, storage, or saved passwords.
- **No blind conflict resolution.** A Dropbox conflicted copy stops the run and
  is shown to you as a diff.
- **Nothing personal committed.** The shipped `projects.yaml` is an empty
  template; the live registry lives in `~/.config/overleaf-skill/`, outside any
  checkout.

## Files

| File | Purpose |
|---|---|
| `SKILL.md` | The skill definition: hard rules, modes, and the step-by-step workflow. |
| `reference/editor-ui.md` | Overleaf UI mechanics — mode switcher, review panel, file tree, history, and the settings that mangle typed LaTeX. |
| `reference/dropbox-sync.md` | Sync semantics, latency, the staleness failure mode, conflicts, and `rules.dropboxignore`. |
| `reference/markup-mode.md` | The suggestion macros, the sentinel-block form, and how to resolve them. |
| `projects.yaml` | Template for the registry; the live copy is `~/.config/overleaf-skill/projects.yaml`. |
| `hooks/overleaf-freshness.py` | Opt-in PreToolUse guard against stale mirror writes; also `--stamp` / `--check` / `--list`. |
| `scripts/resolve-markup.py` | Accepts or rejects markup-mode suggestions in a file. |
