# Concur Field Map & Quirks
*Learned notes for the concur-expense skill. Update after each run. Never store credentials, session tokens, or personal fund/grant identifiers here.*

> Tuned against **Monash University's** SAP Concur (`us2.concursolutions.com`). Expense-type names and the allocation field layout are Monash-specific; adapt for other institutions.

## URL
- Concur entry URL (Monash University): `https://www-us.api.concursolutions.com/sso/saml2/V2/authnrequest/30aaba59-2df8-4d54-870d-3974b06782b5/1582495419386`
- **First run:** if the user is **not** at Monash University, ask for their institution's SAP Concur / SSO entry URL and replace the line above.

## Login
- Manual SSO + MFA in the user's Chrome tab. Claude-in-Chrome reuses the user's real Chrome session, so the Concur login normally persists between runs — check first; you are often already logged in.
- **Auto-detect login — do not ask the user when they are done.** After navigating to the entry URL, poll: `read_page`, and if the page is still Okta/SSO, wait and re-`read_page`. Proceed automatically once `Page URL` is `https://us2.concursolutions.com/home` (or any `us2.concursolutions.com/*` app page). Tell the user once ("Log in — I'll detect when you land on the Concur home page and continue") then poll silently rather than waiting for a "I'm there" message.

## Navigation
- **Create report:** Home → "Create Expense Claim" (the home tile is "Create Expense Claim"; the report list button is also "Create Expense Claim") → dialog (Report Name*, Report Date auto, Comment) → Create Claim. No header-level business-purpose field. Concur calls reports "Claims" throughout this UI.
- **Open existing report:** Home list, or navigate to `/nui/expense/reports/<id>` (note the plural `reports`). New lines append to its total. A freshly created claim's id appears in the URL after Create Claim.
- **Add a line:** report page → "Add Expense" → "Manually Create Expense" → pick expense type → Details form.
- **Attach receipt:** right-side Receipt panel → "Upload New Receipt" (opens a file chooser → `file_upload` with the receipt's absolute path).
- **Allocate:** open the entry → "Allocate" (this auto-saves the entry) → "Add" → New Allocation tab.
- **Import card transactions:** report page → "Add Expense" → "Select from Available Expenses (N)" → tick rows → "Add to Claim"/"Move to". If N is 0, the Manage Expenses page (`/nui/expense`) has an **Available Expenses** section with a "Card Transactions" button to pull the latest card feed. Imported lines arrive with vendor/date/amount filled and expense type often "Undefined" — set the type, fill required fields, allocate, attach a matched receipt, then Save Expense (same per-line order as below).

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
- DOM is dynamic; re-`read_page` rather than reuse element refs (`ref_N`) across actions.
- After the first Save Expense on a fresh line, Concur may pop "saved but missing required info" — click Yes, then resolve the listed alerts (typically allocation + GST). "View Alerts" lists them.
- GST is sometimes not broken out on a receipt (e.g. some rideshare receipts). Do not guess — ask the user how to handle it.
- Totals include booking fees / card surcharges; enter the full amount paid as Total Amount (Inc Tax).
