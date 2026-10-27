# Unread Email Summariser — n8n AI Workflow

An on-demand **Gmail + OpenAI email summariser** built in n8n. The workflow fetches up to five unread emails from the Gmail **Primary inbox**, creates concise AI summaries and suggested action items, and sends **one formatted HTML digest** to a configured email address.

## What it does

- Retrieves up to **5 unread messages** from Gmail's Primary inbox.
- Uses an **AI Agent** with the **OpenAI `gpt-4.1-mini` chat model** to produce a factual summary (maximum 25 words), a Yes/No action-required assessment, and an action item if explicitly requested.
- Aggregates individual AI responses into one set and combines them with the **original Gmail metadata**.
- Converts Gmail timestamps to **India Standard Time (Asia/Kolkata)** and builds an HTML table.
- Sends **one digest email**, rather than one message per source email.
- Runs only when manually triggered; it does **not** mark source messages as read or modify them.

## Workflow architecture

```text
Manual Trigger
    |
Gmail — Get Many Messages (5 unread, Primary)
    |
AI Agent <--- OpenAI Chat Model (gpt-4.1-mini)
    |
Aggregate (collect output fields)
    |
Code in JavaScript (HTML table + Gmail metadata)
    |
Gmail — Send a Message (one digest)
```

No conversation memory or AI tool connections are necessary: Gmail retrieval and sending are performed by dedicated workflow nodes.

## Nodes and configuration

| Node | Purpose | Important settings |
|---|---|---|
| **When clicking ‘Execute workflow’** | Run on demand | Manual Trigger |
| **Gmail** | Retrieve messages | Message → Get Many; limit **5**; read status **Unread**; Gmail query `in:inbox category:primary is:unread` |
| **AI Agent** | Summarise each message | Prompt includes `From`, `Subject`, and `snippet`; returns JSON with `summary`, `action_required`, `action_item` |
| **Model** | Generate AI responses | OpenAI Chat Model: **gpt-4.1-mini** |
| **Aggregate** | Combine five responses | Aggregate individual field **`output`** (case-sensitive) |
| **Code in JavaScript** | Assemble HTML digest | Reads aggregated `output` and original `$('Gmail').all()` items; HTML-escapes values and formats Gmail `internalDate` in IST |
| **Send a message** | Deliver the digest | Gmail → Send; subject **Unread Email Summary - Action Tracker**; body expression `{{ $json.html }}` |

**Gmail output fields:** The current Gmail node supplies `From` and `Subject` with capital letters, and `snippet` and `internalDate` in lowercase. The Code node uses these original Gmail fields rather than asking the model to guess metadata.

## Digest format

The emailed HTML report includes:

| Received (IST) | From | Subject | Summary | Action Required |
|---|---|---|---|---|
| Message date and time | Original sender | Original subject | AI-generated summary | Yes/No and suggested action |

Rows alternate background shading to improve readability. If no explicit action is requested, the report displays **No / None**. Always check the original email before acting on an AI assessment.

## Requirements

- A working **n8n** instance (cloud or self-hosted).
- A connected **Gmail OAuth2 credential** with appropriate Gmail access.
- An **OpenAI API credential** configured in n8n.
- Access to a Gmail account with unread messages.

API keys, OAuth tokens, and passwords must remain in **n8n Credentials**, not in the exported workflow or README.

## Import and run

1. In n8n, create or open a workflow and **import** the exported `Unread Email Summariser.json` file.
2. Reconnect the Gmail credentials in the **Gmail** and **Send a message** nodes and the OpenAI credential in **Model**.
3. Change the **Send a message** recipient to your own email address.
4. Verify that Gmail's filter is `in:inbox category:primary is:unread`, **Read Status = Unread**, and **Limit = 5**.
5. Verify the AI Agent returns valid JSON with `summary`, `action_required`, and `action_item` for each email.
6. Run the workflow with **Execute workflow**; confirm the Aggregate node returns **one item** and the Code node generates a non-empty `html` field.
7. Check the receiving inbox for the HTML digest. **Avoid rerunning the Send node unnecessarily**, because each execution sends another email.

The workflow uses the existing Gmail account and OpenAI model; there is no need for a separate Python program, local virtual environment, or Docker deployment.

## Troubleshooting

| Problem | Check |
|---|---|
| Wrong emails retrieved | Confirm the Gmail Primary search query and unread filter; Gmail categories are labels rather than folders. |
| No sender or subject | Use `From` and `Subject`, not `from` or `subject`. |
| Empty Aggregate output | Field name must be exactly `output`, lowercase. |
| JSON parsing fails in Code | Check that AI Agent returns only valid JSON for each of the five items. |
| Incorrect email date | Gmail `internalDate` is milliseconds since Unix epoch; convert and display in `Asia/Kolkata`. |
| Email arrives as plain text | Ensure the Gmail Send node uses an HTML-capable message body with `{{ $json.html }}`. |
| Multiple digest emails | Do not repeatedly execute the Send node; this workflow is manual and sends once per run. |

## Limitations and privacy

- The summariser uses the sender, subject, and **email preview**, not necessarily the complete body. Its summary or action assessment may miss details further down in an email.
- AI classifications are suggestions, not authoritative decisions. Financial, security, and deadline-sensitive messages should be reviewed in Gmail.
- Sending message previews to an AI model involves processing email content with an external service. Use only with appropriate authorization.
- Before publishing the exported workflow to GitHub, **remove or replace any personal recipient address and review credential references, node metadata, pinned data, and sample outputs**. The export is not an encrypted secrets vault; never publish OAuth tokens or API keys.
- The source messages remain unread unless changed independently in Gmail.

## Assignment deliverables

- Screenshot of the complete n8n workflow.
- Screenshot of the final digest in Gmail.
- Exported and **sanitised** workflow JSON committed to GitHub.
- Short screen recording showing a successful run.

## Status

**Completed and tested:** five message summaries were aggregated into a single, styled HTML email containing received time (IST), sender, subject, summary, and action-required fields.
