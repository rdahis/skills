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

Overleaf publishes no figure for how long its push to Dropbox takes, and the
reported spread is wide:

| Source | Overleaf → Dropbox |
|---|---|
| Overleaf's own documentation | unstated |
| `overleaf-sync-now`, a third-party tool built to work around the lag | 10–20 minutes |
| Measured 2026-08-21, one Premium account, two events | text edit in ~60 s; a 496 KB upload in under a minute |

**Treat the interval as unknown.** A fast push one day is no guarantee the
next, and the tool above exists because people do hit the long tail. Writing a
protocol around any specific number — short or long — is the mistake.

Latency is also not the only source of divergence, and fixing on it misses the
larger one: **a co-author editing right now.** Their work reaches the mirror
whenever it reaches it, and no push interval bounds how far behind your local
copy is. Hence a protocol that *verifies* rather than *waits*: the check costs
seconds and holds regardless of which cause is in play.

The failure it prevents is the same either way. An agent reads the local file,
edits it, and writes it back, **silently overwriting every web edit made since
the last push** — deleted paragraphs return, recent work disappears, and the
loss reads as a sync glitch rather than an overwrite.

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
   find "<mirror-dir>" -type f -mmin -2 -print
   ```

   Use `-mmin`, not `-newermt '-90 seconds'`. Relative timestamps are a GNU
   extension: BSD `find` and `bfs` (a drop-in replacement some users install)
   both reject them, and `bfs` fails with a parse error rather than falling
   back.

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

Consequence for this skill: **never write to the mirror copy of a file that has
suggestions pending.** That specific collision — incoming sync content meeting
unresolved tracked ranges in the same file — is what Overleaf's warning
describes, and it has not been tested here, so treat it as live. Resolve the
pending suggestions first, or make the edit in the browser.

Writing to a file with *no* pending suggestions is a different case, and the
observation above shows it can land as tracked changes rather than plain edits.

**A mirror write can arrive as a tracked change.** Observed 2026-08-21: with
the editor in **Reviewing** mode, content written into the mirror and synced up
appeared in Overleaf as native tracked insertions, listed in the review panel
with accept/reject and attributed to the linked account. Overleaf appears to
apply incoming sync edits under the linked user's track-changes setting.

This is one observation on one project, so verify it for a given project before
relying on it — but it matters, because it means bulk edits do not have to
choose between being file-written and being tracked.

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
