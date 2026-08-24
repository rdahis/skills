# Moodle task recipes

Step-by-step recipes for the tasks this skill is asked for most. All of them
assume Steps 1–2 of `SKILL.md` are done: the target is resolved and the current
state is recorded.

---

## Duplicate a weekly activity

1. Inspect the reference activity and every one of its settings.
2. Use Moodle's own duplicate action rather than recreating the activity by hand.
3. Rename the copy for the destination week.
4. Move it into the correct section — duplication often leaves the copy directly
   below the original, in the source section.
5. Update only the week-specific dates and text.
6. Preserve grade type, maximum, completion, groups, availability, submission,
   feedback, and notification settings unless instructed otherwise.
7. Reopen both the reference and the copy, and compare the preserved settings
   field by field.

When dates follow teaching weeks, distinguish teaching weeks from breaks, and
confirm the local timezone and the weekday Moodle displays before saving.

---

## Create or repair a quiz

Compare against the named reference quiz and verify each of:

- Name and section.
- Open and close times.
- Time limit, and any grace period.
- Attempts allowed and grading method.
- Maximum grade, and the question total.
- Navigation method and question behaviour.
- Password and network restrictions, where present.
- The Safe Exam Browser requirement and every dependent option it reveals.
- Review options, for attempt, correctness, marks, feedback, and answers.
- Visibility and completion conditions.

Do not infer Safe Exam Browser settings from the label alone. Selecting the
requirement exposes further options — quit password, config key, permitted
browser exam keys — and their values are part of the reference configuration.
Inspect and reproduce all of them.

---

## Enter manual quiz grades

Direct gradebook entry is for a deliberate manual override: a paper submission,
or an approved exceptional attempt. For a question-by-question regrade of an
online attempt, use the quiz grading workflow instead — editing the gradebook
cell there is overwritten by the next regrade.

1. Identify the exact quiz column by its visible label **and** its grade-item id.
2. Confirm the column's maximum grade before entering anything.
3. Locate each student row by student ID.
4. Record any existing nonblank grade in the target cell before replacing it.
5. Fill numeric grades with appropriate precision.
6. Re-read all unsaved values before pressing the single save control.
7. Save once, reload the grader report, and compare every saved value against
   the source mapping.
8. Report overwritten nonblank grades, and any display-name differences between
   the source file and Moodle.

Enter points where Moodle expects points, not percentages. Convert only when the
scale relationship is explicit, and verify the result stays within the maximum.

---

## Change maximum grades

- Confirm first whether the maximum belongs to the activity, to its grade item,
  or to both. They are separate settings and can disagree.
- Inspect existing grades before changing the maximum on a populated item —
  Moodle may offer to rescale, which alters results already recorded.
- Update the authoritative activity setting where one exists, then verify the
  gradebook column shows the intended maximum.
- Do not edit category or course totals unless the user asked for that.

---

## Manage groups

1. Inspect the existing groups and their memberships.
2. Create only the groups that are missing.
3. Match participants by student ID.
4. Add or remove memberships exactly as supplied — no inferred tidying.
5. Verify each group's count and member IDs, and check for unintended
   duplicates or omissions.
6. Preserve grouping assignments and activity group modes unless asked to
   change them.

---

## Embed a PDF or presentation inline

First establish whether the user accepts browser-native PDF rendering, because
that decides the whole approach.

Do not claim that `<iframe>`, `<embed>`, or `<object>` makes a PDF display
browser-independently. Firefox's viewer settings and Moodle's own response
headers can still force a download, and the embed then renders as an empty box.

For reliable cross-browser presentation, prefer one of: a Moodle-supported
HTML or slide-image presentation, H5P, Panopto, an approved web-presentation
embed, or a PDF.js viewer the institution permits.

If browser-native inline PDF is acceptable, use a Moodle file or resource set to
display embedded, or an accessible `iframe`/`object` with a clear download-and-open
fallback. Preserve accessible title text, keyboard access, a sensible height, and
a direct-file fallback link.

After saving, test the **learner** view. The editor preview is not evidence.
