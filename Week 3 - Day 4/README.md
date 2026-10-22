# AI Slack Recipe Bot using n8n and OpenAI

**CAIE Course Program — Assignment 8**

An n8n automation that listens for recipe requests in a Slack channel, uses OpenAI to produce a shopping list with approximate ingredient quantities, and replies in the **same Slack channel**.

## Demo

**In Slack `#recipe-bot`:**

**User:** `chicken fry for 10 people`

**AI Recipe Bot:** Responds with a shopping list for chicken fry, adjusted for **10 servings**.

The bot also asks users to clarify genuinely unrecognizable recipe requests.

> Screenshots and a demonstration video can be added here after recording.

## How it works

```text
Slack Trigger
     |
     v
IF (ignore bot-generated and empty messages)
     | True
     v
Edit Fields (extract recipe name)
     |
     v
Basic LLM Chain <--- OpenAI Chat Model (gpt-4o-mini)
     |
     v
Slack — Send a message (same channel)
```

The **False** output of the IF node is intentionally left unconnected to prevent the bot from replying to its own messages.

## Workflow nodes

| Node | Purpose |
| --- | --- |
| Slack Trigger | Receives new messages from a selected Slack channel |
| IF | Allows user messages with non-empty text through; filters common bot messages |
| Edit Fields (Set) | Stores the incoming message in the `recipe` field |
| Basic LLM Chain | Prompts the AI to create an ingredient shopping list |
| OpenAI Chat Model | Provides the language model (`gpt-4o-mini`) |
| Slack — Send a message | Posts the generated ingredients to the original channel |

## Features

- Recipe requests and replies stay inside Slack.
- Recognizes common dishes, including informal names such as `chicken fry`.
- Adjusts approximate ingredient quantities when a serving count is included.
- Defaults to **2 servings** if no number of people is specified.
- Responds politely to genuinely unclear recipe requests.
- Filters typical bot-generated messages to help avoid reply loops.
- Omits the automatic n8n workflow footer from Slack replies.

## Requirements

- An n8n instance with a publicly reachable HTTPS webhook endpoint
- A Slack workspace and a public testing channel
- A Slack app/bot installed in the workspace and invited to that channel
- Slack bot token and Slack app signing secret, configured securely in n8n
- An OpenAI API credential with access to the selected model (API charges may apply)

### Slack app setup

Configure the Slack app with:

**Bot token scopes:**
- `channels:history`
- `channels:read`
- `chat:write`

**Bot event subscription:**
- `message.channels`

Disable **Socket Mode** for this webhook-based setup. In Slack **Event Subscriptions**, set the **Request URL** to the n8n Slack Trigger's **Production URL**. Publish/activate the workflow before verifying that URL, and reinstall the Slack app after changing scopes.

## Import and configure

1. Download [`CAIE_Assignment_8_Slack_Recipe_Bot_GitHub_Safe.json`](./CAIE_Assignment_8_Slack_Recipe_Bot_GitHub_Safe.json) from this repository.
2. In n8n, import the workflow JSON using the workflow import option.
3. In **Slack Trigger**, set **Channel to Watch → By ID** and replace `REPLACE_WITH_YOUR_CHANNEL_ID` with your own Slack channel ID.
4. Select your **Slack API** credential in both **Slack Trigger** and **Send a message**. Enter the bot token (`xoxb-...`) and signing secret in the credential settings, **not** in the workflow JSON.
5. Select your **OpenAI API** credential in **OpenAI Chat Model** and confirm the model is available.
6. Review the **Basic LLM Chain** prompt and node connections.
7. Save and publish/activate the workflow.
8. In Slack **Event Subscriptions**, configure and verify the Production webhook URL.
9. Send a recipe name in the watched channel and inspect n8n **Executions** if the bot doesn't respond.

> **Note:** This repository contains a **sanitized workflow export** for sharing. Credential references, instance identifiers, webhook identifiers, and the original channel ID have been removed. Importers must configure their own credentials and channel. Do not expect the imported workflow to work without setup.

## Example tests

| Slack message | Expected behavior |
| --- | --- |
| `Paneer Butter Masala` | Ingredient list with approximate quantities for 2 |
| `chicken fry for 10 people` | Ingredient list with quantities for 10 |
| `Masala Dosa` | Ingredient list for the dish |
| `xyzabc123` | Polite request to clarify the recipe name |

Empty messages and common bot events are filtered by the IF node rather than being sent to the AI.

## Security

- Never commit Slack bot tokens, signing secrets, or OpenAI API keys.
- Keep secrets in **n8n Credentials**.
- Review every exported workflow before publishing it.
- This workflow sends recipe requests to OpenAI for processing.

## Assignment submission

- [x] Build the Slack Recipe Bot workflow in n8n
- [x] Test ingredient generation and responses in Slack
- [x] Export a GitHub-safe workflow JSON
- [ ] Upload workflow JSON and README to GitHub
- [ ] Record the working demonstration
- [ ] Post the video to WhatsApp
- [ ] Post the video to the Skool community

---

Built as part of **CAIE Course Program — Assignment 8: n8n Automation — Slack Recipe Bot**.
