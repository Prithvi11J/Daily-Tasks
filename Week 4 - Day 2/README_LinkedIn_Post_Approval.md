# LinkedIn Post Approval — Human-in-the-Loop AI Workflow

An n8n automation that turns a topic into a reviewed LinkedIn post, requests human approval by email, and stores only approved drafts in Google Sheets.

## Overview

The workflow separates content creation, editorial review, and approval into distinct stages. Two AI agents collaborate on the draft, but the final decision remains with the user. Rejected content never reaches the content tracker. This is an **approval and draft-management system**, not an automatic LinkedIn publisher.

## Features

- **Topic intake:** A simple n8n web form with a required `Topic` field.
- **Dedicated Writer Agent:** Produces a 120–150-word LinkedIn draft with a hook, a single call to action, and up to three hashtags.
- **Dedicated Reviewer Agent:** Evaluates the hook, clarity, and call to action, then refines the weakest part of the draft.
- **Human approval gate:** Gmail sends the reviewed draft with **Approve** and **Reject** options and pauses execution while awaiting a response (up to one day).
- **Conditional storage:** The IF node adds the post to Google Sheets only when approval is true.
- **Reusable content tracker:** Every approved draft is stored with its date, original topic, final content, and approval status.

## Architecture

```text
n8n Form Trigger (Topic)
         |
         v
   Writer AI Agent <--- OpenAI Chat Model (gpt-4.1-mini)
         |
         v
  Reviewer AI Agent <-- OpenAI Chat Model (gpt-4.1-mini)
         |
         v
Gmail: Send and Wait for Response (Approve / Reject)
         |
         v
    IF: data.approved is true
      /                    \
  TRUE                    FALSE
    |                       |
Google Sheets          End workflow
  Append Row             (no save)
```

## Technology Stack

| Technology | Purpose |
| --- | --- |
| n8n | Workflow orchestration, form trigger, approval handling, and branching |
| OpenAI `gpt-4.1-mini` | Drafting and reviewing LinkedIn content |
| Gmail API via n8n OAuth2 | Sending approval requests and collecting responses |
| Google Sheets API via n8n OAuth2 | Persisting approved drafts |
| JavaScript expressions | Mapping original topic, reviewed post, and date into the sheet |

## Workflow Nodes

1. **On form submission** — Accepts a required `Topic` field.
2. **Writer Agent** — Produces the initial post from the submitted topic.
3. **OpenAI Chat Model** — Supplies the Writer Agent's model.
4. **Reviewer Agent** — Improves the Writer Agent's `output` and returns only the polished draft.
5. **OpenAI Chat Model1** — Supplies the Reviewer Agent's model.
6. **Send message and wait for response** — Emails the final draft and captures an approval decision.
7. **If** — Checks `{{ $json.data.approved }}` for `true`.
8. **LinkedIn Post Approval Tracker** — Appends a row only from the IF node's true branch.

## Setup

### Prerequisites

- A working n8n instance.
- An OpenAI API credential in n8n.
- Gmail OAuth2 and Google Sheets OAuth2 credentials authorized for the accounts you intend to use.
- A Google spreadsheet with a `Sheet1` tab containing the exact column headers below.

| Date | Topic | Final Post | Status |
| --- | --- | --- | --- |

### Import and configure

1. Download or clone this repository and import `LinkedIn_Post_Approval_GitHub_Safe.json` into n8n via **Import from File**.
2. Reconnect the **OpenAI Chat Model** nodes to your OpenAI credentials.
3. Reconnect the **Gmail** node to your Gmail OAuth2 credential and replace `YOUR_EMAIL@example.com` with your approval recipient.
4. In **LinkedIn Post Approval Tracker**, select your spreadsheet document and `Sheet1` tab using your own Google Sheets credentials.
5. Check the four column mappings:

   | Sheet column | Value / expression |
   | --- | --- |
   | Date | `{{ $now.setZone('Asia/Kolkata').toFormat('yyyy-MM-dd HH:mm:ss') }}` |
   | Topic | `{{ $('On form submission').first().json.Topic }}` |
   | Final Post | `{{ $('Reviewer Agent').first().json.output }}` |
   | Status | `Approved` |

6. Confirm **Response Type = Approval**, both **Approve** and **Reject** options are available, and the wait limit is **1 day**.
7. Save the workflow. Use the Form Trigger's **Test URL** while testing; use its production form URL once the workflow is published and active.

> The public-safe JSON intentionally omits account-specific credential references, account IDs, webhook IDs and spreadsheet links. Reconnect these in your own n8n instance before running.

## How to Use

1. Open the form and submit a LinkedIn topic (for example, *How AI agents improve team collaboration*).
2. The Writer Agent drafts the post and the Reviewer Agent polishes it.
3. Review the emailed draft and select **Approve** or **Reject**.
4. **Approve:** One row is appended to Google Sheets with status `Approved`.
5. **Reject:** The false branch ends; nothing is appended.

The workflow does **not** post to LinkedIn directly.

## Validation

The workflow was manually tested for both outcomes:

- **Approved:** The post was added to Google Sheets with the submitted topic, reviewed content, timestamp, and status.
- **Rejected:** `data.approved` returned `false`, the IF node followed the false branch, and the Sheets append path was not invoked.

## Design Considerations

- **Human-in-the-loop controls:** An explicit approval prevents automated persistence of unreviewed content.
- **No hallucinated approval:** A post is saved only when the approval response is explicitly `true`.
- **Editorial separation:** Drafting and review use separate agent nodes to make each step easier to improve independently.
- **Data minimization:** Store credentials in n8n, not in exported JSON or repository files.
- **Scope:** This system manages approved drafts; publishing to LinkedIn would require a separate integration and authorization.
- **Limitations:** AI-generated content may need factual review; an expired or unanswered approval should not be treated as approval.

## Security

- Keep OAuth tokens, API keys, real recipient addresses, and private spreadsheet URLs out of version control.
- Review n8n execution data and screenshots for personal information before sharing.
- Restrict access to the approval form if deploying outside a trusted environment.
- Reconnect imported credentials using the destination n8n instance's credential store.

## Potential Enhancements

- Revision requests that return to the Writer or Reviewer Agent.
- Approval reminders and a separate expired-approval state.
- Duplicate-topic detection and scheduled drafting.
- Post categorization and an editorial dashboard in Google Sheets.
- A separate LinkedIn publishing integration after explicit approval.
