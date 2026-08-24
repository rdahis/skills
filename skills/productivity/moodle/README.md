# moodle

A [Claude Code](https://claude.com/claude-code) skill for administering a Moodle
course. Claude reads the current course state, makes the smallest change you
asked for, saves it through Moodle's own forms, and then re-reads the page to
verify every value landed.

Moodle's web services are disabled for staff accounts at most institutions, so
the work happens in a tab of your real, signed-in Chrome through the
Claude-in-Chrome extension. Claude never handles your credentials.

## Credits

Adapted from a Moodle administration skill written by **Klaus Ackerman** (Monash
University), which is the original source for the workflow and the safety
constraints. This port restructures it for this repository, moves the
course-specific settings out into a registry, and adds the reference files.

## Why it is built this way

Moodle is a system where a small mistake is expensive and quiet. Three
properties drive the design:

1. **Adjacent fields look identical.** Week 7's quiz column and week 8's differ
   by one character in a label. So every target is resolved by id — course id,
   course module id, grade item id — and re-read after saving, never trusted from
   the click that preceded it.
2. **Some actions reach students immediately.** Releasing grades, submitting
   final grades, and sending notifications are irreversible and visible. They
   require your explicit confirmation in chat; nothing else does them as a side
   effect.
3. **Duplication drifts.** Copying week 3's quiz to week 4 means changing two
   dates and nothing else. The skill copies the reference activity's settings
   wholesale, changes only what you named, and then diffs the copy against the
   original.

## What it does

- Duplicates weekly activities, renames them, moves them into the right section,
  and updates only the week-specific dates — preserving grade type, maximum,
  completion, groups, availability, submission, and feedback settings.
- Creates or repairs quizzes against a reference quiz, including the full **Safe
  Exam Browser** configuration and its dependent options, which the label alone
  does not describe.
- Enters manual gradebook grades from a spreadsheet — validating row counts,
  duplicates, blanks, and the grade range first, matching students by stable
  student ID, and reporting every nonblank grade it overwrote.
- Changes maximum grades, distinguishing the activity setting from the grade
  item and flagging the rescaling risk on a populated item.
- Creates groups and sets membership, verifying counts and member IDs afterwards.
- Embeds learning resources, and tests the **learner** view rather than the
  editor preview.

## Requirements

- **Claude Code** with the **Claude-in-Chrome** extension connected. The skill
  drives a tab in your own Chrome, reusing your existing Moodle session.
  Connect the extension from the Chrome **profile** that holds your Moodle
  login — the extension reports one connection per instance, not per profile, so
  a connected browser can still be driving the wrong profile.
- A **Moodle** account with editing rights on the course.
- For spreadsheet-driven work: the `anthropic-skills:xlsx` skill for `.xlsx` and
  `.xls` workbooks. `.csv` and `.tsv` are read directly, no dependency.

## Installation

Quickest — the [`skills`](https://www.npmjs.com/package/skills) CLI:

```bash
npx skills@latest add rdahis/skills
```

…then select `moodle`.

Manual alternative:

```bash
git clone https://github.com/rdahis/skills.git
cp -r skills/skills/productivity/moodle ~/.claude/skills/
```

## Configuration

Copy the registry template out of the skill folder, then add your courses:

```bash
mkdir -p ~/.config/moodle-skill
cp ~/.claude/skills/moodle/courses.yaml ~/.config/moodle-skill/courses.yaml
```

The site URL is preset to **Monash University's** `learning.monash.edu` — a
public endpoint, not a secret. If you are elsewhere, the skill asks for your
Moodle URL on the first run and writes it into the live registry. Leave
`courses: []`; the skill appends an entry as it meets each course, so
`/moodle update the week 8 quiz on PPS` resolves without a URL from then on.

Keeping the live registry in `~/.config` means reinstalling the skill never
clobbers it, and your teaching load never lands in a repository.

## Usage

```
/moodle duplicate the week 3 quiz for week 4 — https://learning.example.edu/course/view.php?id=12345
/moodle enter the grades in ~/Downloads/week6-marks.xlsx into the Week 6 Quiz column on PPS
/moodle create tutorial groups from ~/Downloads/tutorials.csv on PPS
/moodle set the maximum grade on the Week 9 assignment to 20
```

Arguments are free text: what you want changed, plus the Moodle URL or a course
name already in `courses.yaml`. A URL you supply is authoritative — if it
disagrees with the page Claude finds, it stops and asks rather than editing the
wrong thing.

Before anything is saved you get: the resolved target, the current values, and —
for batch work — the full `student ID → grade` mapping. Afterwards you get what
changed, what was verified, and every exception.

## Safety

- **Smallest possible mutation.** Only the fields you named change; everything
  else is preserved from the reference activity as found.
- **Verified from Moodle.** Every saved value is re-read from a reloaded page. A
  success banner is not accepted as evidence.
- **No deletions or resets.** Activities, submissions, attempts, grades, users,
  groups, and enrolments are never deleted, and attempts are never reset, except
  on an explicit request naming that exact deletion.
- **Outward actions confirmed in chat.** Releasing grades, submitting final
  grades, and notifying students each need your explicit yes.
- **No credentials handled.** You are already signed in; the skill drives your
  tab and never touches cookies, storage, or saved passwords.
- **Student data minimised.** Grades, IDs, and emails are surfaced only as far as
  the task and its verification require.
- **Nothing personal committed.** The shipped `courses.yaml` is an empty
  template; the live registry lives in `~/.config/moodle-skill/`, outside any
  checkout.

## Files

| File | Purpose |
|---|---|
| `SKILL.md` | The skill definition: hard rules, surfaces, and the step-by-step workflow. |
| `reference/workflows.md` | Task recipes — duplication, quizzes and Safe Exam Browser, manual grades, maximum grades, groups, inline resources. |
| `reference/moodle-ui.md` | Moodle UI mechanics — URLs, form quirks, verification notes. Self-updates as the UI is learned. |
| `courses.yaml` | Template for the course registry; the live copy is `~/.config/moodle-skill/courses.yaml`. |
| `README.md` | This file. |
