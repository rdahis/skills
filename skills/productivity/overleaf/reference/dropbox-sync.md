# Overleaf ↔ Dropbox: what the mirror is and is not

## What the integration does

Linking Dropbox in **Account Settings → Dropbox → Link** creates a folder per
project under `Apps/Overleaf` in the user's Dropbox:

```
~/Dropbox/Apps/Overleaf/<Project Name>/
```

The path is fixed; Overleaf does not let you choose another location. Projects
whose names collide get a numeric suffix, so a folder name is a hint, not proof.
Confirm a mirror by comparing a distinctive line of the main file against the
browser.

Business or team Dropbox installs put this under a differently named root —
`~/Dropbox (Personal)/…`, `~/<Org> Dropbox/<User>/…`. Record the actual root in
`projects.yaml`; do not assume `~/Dropbox`.

Dropbox sync is an Overleaf premium feature, and each collaborator needs their
own subscription to mirror locally.

## Latency, and why it matters

| Direction | Typical delay |
|---|---|
| Overleaf → Dropbox | **10–20 minutes** unless a sync is forced |
| Dropbox → Overleaf | Seconds to a minute, once Dropbox has finished uploading |

The asymmetry is the whole problem. Edits made on overleaf.com are not in the
local file for up to twenty minutes. An agent that reads the local file, edits
it, and writes it back inside that window **silently overwrites every web edit
made since the last push** — deleted paragraphs return, recent work disappears,
and the loss looks like a sync glitch rather than an overwrite.

## The Sync with Dropbox dialog

Left rail → **Integrations** → **Dropbox** opens a dialog titled **Sync with
Dropbox**. It is the single most useful surface in this workflow, because it
answers three questions authoritatively:

1. **Where the mirror is.** "This project will appear in your Dropbox folder at
   `Apps/Overleaf/<Folder Name>`" — the real folder, including any numeric
   suffix Overleaf added for a name collision. **Use this instead of guessing
   from folder names.** It is proof; a matching name is not.
2. **Whether Overleaf has pushed.** A status line reads "Overleaf and Dropbox
   have processed all updates. Note that your local Dropbox might still be
   synchronizing." That is the Overleaf half done — the Dropbox client half may
   still be in flight, which is why the mtime poll below still matters.
3. **How to force a push.** A link, **"sync this project now"**, in the sentence
   beginning "Changes not appearing in Dropbox?". It is a link inside this
   dialog, not a menu item.

## The freshness protocol

Before any local read that informs an edit, and before any local write:

1. Open the project in Chrome.
2. Left rail → **Integrations** → **Dropbox**. Read the status line. If it does
   not report all updates processed, click **"sync this project now"**.
3. Poll the newest mtime under the mirror directory until it stops changing:

   ```bash
   find "<mirror-dir>" -type f -newermt '-90 seconds' -print
   ```

   Five to thirty seconds is normal. Past ninety, report a problem rather than
   proceeding.
4. Stamp it: `python3 hooks/overleaf-freshness.py --stamp "<mirror-dir>"`.

After a local write, the round trip is not complete until the change has been
read back **from Overleaf** in the browser. Dropbox finishing its upload only
proves Dropbox has the file.

## Operations that destroy history

Overleaf's own warning: renames and moves "may be interpreted as 'delete and
create,' resulting in a loss of history, tracked changes, and comments."

So, through the mirror:

- **Never rename a file.**
- **Never move a file between folders.**
- **Never delete a file or folder.** Deleting a folder empties it in Overleaf
  while leaving the project in place to preserve history.
- **Never add a compiled PDF.** Overleaf: "Never manually upload a compiled PDF
  into your Overleaf project."

All four are done in the Overleaf file tree instead, then synced down.

## Track changes and sync do not mix

Overleaf advises against combining an active sync integration with track
changes: pushes from Git — and the delete-and-create paths in Dropbox — "can
result in the loss or displacement of track changes and comments."

Consequence for this skill: **in `suggest` mode the mirror is read-only.**
Suggestions are made by typing in the browser. `markup` mode exists precisely
because bulk edits cannot be both file-written and natively tracked.

**A pending suggestion reaches Dropbox as plain text.** Tracked-change state is
Overleaf-side metadata and does not survive the push, so the mirror shows the
document *with* every unresolved insertion applied and every unresolved deletion
still present — the union of accepted and proposed text, with nothing marking
which is which. The mirror is therefore not a picture of the accepted document
while a review is open. When it matters whether text is agreed or merely
proposed, read the review panel in the browser, not the file.

## Conflicted copies

Dropbox writes `main (Conflicted copy 2026-08-21).tex` when both sides changed.
When one appears:

1. Stop. Do not merge, delete, or overwrite anything.
2. Diff it against the live file: `diff -u "main.tex" "main (Conflicted copy …).tex"`.
3. Show the user both sides and let them choose. The Overleaf History panel
   tells you what the web side actually did and when.
4. Once resolved, delete the conflicted copy **from Dropbox only** — it never
   existed in Overleaf, so no history is at risk.

## Keeping build artifacts out of the sync

Compiled output syncing back and forth produces spurious conflicts. Overleaf
recommends a `rules.dropboxignore` at the Dropbox root (or Dropbox
Preferences → Sync → Set Ignore Rules → Modify Rules):

```
/Apps/Overleaf/**/*.pdf
/Apps/Overleaf/**/*.los
/Apps/Overleaf/**/*.toc
/Apps/Overleaf/**/*.out
/Apps/Overleaf/**/*.aux
/Apps/Overleaf/**/*.log
/Apps/Overleaf/**/*.gz
/Apps/Overleaf/**/*.blg
/Apps/Overleaf/**/*.bbl
```

Adjust the leading path for a non-default Dropbox root.

## When sync appears stuck

1. Confirm the Dropbox desktop client is running and the folder is not paused
   or set to online-only.
2. Force a sync from the project's Integrations menu.
3. Check the Overleaf History panel — if the web edits are there but the mirror
   is not moving, the failure is on the Dropbox side.
4. Overleaf's own remedy is to unlink and relink Dropbox in Account Settings.
   That is the user's action, not yours; say so and stop.

While sync is broken, work browser-only and treat the mirror as absent.

## GitHub and Git alternatives

Overleaf also offers GitHub sync and a Git bridge, both premium. They carry the
same track-changes warning as Dropbox and are not used by this skill. If a
project is already on GitHub sync, say so — pushing to it from the shell has the
same overwrite hazard as the mirror, with the same fix: pull first, verify, then
write.
