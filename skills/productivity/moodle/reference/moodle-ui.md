# Moodle UI mechanics

Navigation paths, form quirks, and validation gotchas. This file is meant to
grow: append what each run teaches, so the next run does not rediscover it.

Paths below are written against a standard Moodle 4.x Boost theme. Institutional
themes rename and relocate things — verify before relying on a path.

## URLs worth knowing

| Target | URL |
|---|---|
| Course main page | `/course/view.php?id=<courseid>` |
| Course settings | `/course/edit.php?id=<courseid>` |
| Activity settings | `/course/modedit.php?update=<cmid>` |
| Gradebook setup | `/grade/edit/tree/index.php?id=<courseid>` |
| Grader report | `/grade/report/grader/index.php?id=<courseid>` |
| Single-view (one grade item) | `/grade/report/singleview/index.php?id=<courseid>` |
| Grade item settings | `/grade/edit/tree/item.php?courseid=<courseid>&id=<itemid>` |
| Groups | `/group/index.php?id=<courseid>` |
| Participants | `/user/index.php?id=<courseid>` |
| Quiz settings | `/mod/quiz/view.php?id=<cmid>` then **Settings** |
| Quiz manual grading | `/mod/quiz/report.php?id=<cmid>&mode=grading` |

`courseid` identifies the course; `cmid` identifies a course module (an activity
instance in a course); `itemid` identifies a gradebook item. They are distinct
namespaces and are not interchangeable.

## Form quirks

- **Editing mode.** Most course-page mutations need the **Edit mode** toggle on,
  top right. The duplicate, move, and hide actions only appear with it enabled.
- **Collapsed sections.** Activity settings forms open with most sections
  collapsed. `read_page` will not show a field inside a collapsed section —
  expand it (or use **Expand all**) before concluding a setting is absent.
- **Date fields are enabled by a checkbox.** Each date group has an **Enable**
  checkbox; setting the day/month/year selects without ticking it leaves the
  date off. Verify the checkbox state, not just the values.
- **Timezone.** Dates are stored and shown in the user's Moodle profile timezone,
  which need not match the browser's. Read the timezone Moodle displays before
  setting anything time-sensitive.
- **Safe Exam Browser.** The requirement selector reveals dependent fields only
  after it is set. Set it first, re-read the page, then fill what appeared.
- **Grader report editing.** Turn on editing in the grader report to get input
  cells. It has one save control for the whole page — a navigation away before
  saving loses every entered value silently.
- **Single view** is usually the safer surface for entering one grade item across
  many students: one column, one save, far fewer adjacent fields to hit by mistake.

## Verification notes

- After a save, Moodle often redirects to the activity or course page rather than
  back to the form. Navigate back to the settings form to verify.
- A grade entered in the grader report can be overwritten later by the activity
  itself (a quiz regrade, an assignment grade change). Note in the report when a
  manual entry is of that kind.
- Duplicated activities take the name `<original> (copy)` and land in the source
  section. Both need fixing; neither is reported as an error.

## Institution notes

Record here what is specific to your Moodle: theme differences, custom fields,
local plugins, enrolment conventions, and the shorthand your courses go by.
