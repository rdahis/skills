# Concur Field Map & Quirks
*Learned notes for the concur-expense skill. Update after each run. Never store credentials, session tokens, or personal fund/grant identifiers here.*

> Tuned against **Monash University's** SAP Concur (`us2.concursolutions.com`). Expense-type names and the allocation field layout are Monash-specific; adapt for other institutions.

## URL
- Concur entry URL (Monash University): `https://www-us.api.concursolutions.com/sso/saml2/V2/authnrequest/30aaba59-2df8-4d54-870d-3974b06782b5/1582495419386`
- **First run:** if the user is **not** at Monash University, ask for their institution's SAP Concur / SSO entry URL and replace the line above.

## Login
- Manual SSO + MFA in the Playwright browser. The persistent profile usually retains the session between runs.

## Navigation
- **Create report:** Home → "Create Expense Report" → dialog (Report Name*, Report Date auto, Comment) → Create Report. No header-level business-purpose field.
- **Open existing report:** Home list, or navigate to `/nui/expense/report/<id>`. New lines append to its total.
- **Add a line:** report page → "Add Expense" → "Manually Create Expense" → pick expense type → Details form.
- **Attach receipt:** right-side Receipt panel → "Upload New Receipt" (opens a file chooser → `browser_file_upload`).
- **Allocate:** open the entry → "Allocate" (this auto-saves the entry) → "Add" → New Allocation tab.

## Per-line order that avoids the post-save error popup
Fill all Details fields → Upload receipt → **Allocate** (auto-saves) → Add fund → 100% → Save allocation → Save the Allocate dialog → **Save Expense**.
A clean row shows "Show Allocation Summary"; an incomplete one shows "Show Errors".

## Allocation: Cost Centre + Fund
- The Allocate panel splits the fund into TWO fields: **Cost Centre** and **Fund**.
- The combined picker option reads "<Fund name> (<CostCentre>-<Fund>)" and usually sits at the top of the Cost Centre **Most Recently Used** list.
- Selecting the Cost Centre option **auto-fills** the matching Fund. Then set Percent 100, Save the allocation, and Save the Allocate dialog.

## Expense-type mappings (receipt category → Concur expense type)
| Receipt category   | Concur expense type (Monash)                |
|--------------------|---------------------------------------------|
| taxi / rideshare   | Short Distance Commuter Travel - Australia  |
| meals (travel)     | Food & Drink Travel - Australia             |
| airfare            | Airfare Expense - Australia / - Overseas    |
| accommodation      | Accommodation Travel - Australia / - Overseas |
| conference fee     | Conference/Seminar Expenses (External) - Australia / - Overseas |
| _other_            | _add as learned_                            |

## Required fields by expense type
**Short Distance Commuter Travel - Australia**
- Commuter Travel Type* — for AU taxi/rideshare pick "Domestic Travel (inc taxis, hire cars and parking)".
- City*, Transaction Date*, Business Purpose*, Vendor Name*, Total Amount (Inc Tax)*.
- Business use %* — 100 for fully work-related.
- "Amount" is READONLY (auto-derives from Total on save).

**Food & Drink Travel - Australia**
- Transaction Date*, Business Purpose*, Vendor Name*, City*.
- "Was entertainment provided…"* — defaults to "No"; leave as-is for ordinary meals.
- Total Amount (Inc Tax)*, Australian GST Amount*.
- "Amount Approved" is READONLY (auto-derives on save).
- "Number of Monash University staff traveling"* — set to 1 for a solo trip (blank triggers a save error).
- The other head-count fields (partners/family, clients/non-staff, staff-not-travelling) default to 0 — leave unless others were paid for.

## Receipt Status ↔ GST consistency
- Options: "None Selected", "No receipt or invoice", "Invoice no GST", "Invoice GST".
- "Invoice GST" requires a **non-zero** GST value or it errors.
- If the receipt shows a GST line, enter it and pick "Invoice GST". If GST is genuinely 0.00 (or absent and you choose not to claim it), pick "Invoice no GST".

## Known quirks
- DOM is dynamic; re-`browser_snapshot` rather than reuse element refs across actions.
- After the first Save Expense on a fresh line, Concur may pop "saved but missing required info" — click Yes, then resolve the listed alerts (typically allocation + GST). "View Alerts" lists them.
- GST is sometimes not broken out on a receipt (e.g. some rideshare receipts). Do not guess — ask the user how to handle it.
- Totals include booking fees / card surcharges; enter the full amount paid as Total Amount (Inc Tax).
