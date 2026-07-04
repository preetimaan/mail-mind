# Mail Mind — User Guide

Mail Mind helps you analyze your email patterns (senders, categories, trends). This guide is for **people using the product** after someone has deployed it for them. Server setup, OAuth clients, and environment variables belong in **Developer setup** — not here.

## Quick start

1. Open Mail Mind in your browser (use the URL from whoever runs the app for you).
2. Enter a **username** (this is your local workspace name)
3. Add an account in **Settings**
4. Go to **Analyze**, pick a date range, and start an analysis
5. View results in **Insights**
6. Use **Labels & Filters** to review labels/folders and copy filter queries

## Username (local workspace)

- Your username groups your accounts and data locally.
- Your username is remembered in your browser (refresh won’t log you out).
- Use **Log out** to clear the saved username.

## Dashboard tabs

### Analyze

Use this tab to run analyses and manage coverage.

- **Start/End dates**: choose the analysis window as a half-open range \([start, endExclusive)\).
  - **Start (on and after)**: first calendar day included.
  - **End (before, exclusive)**: first calendar day **not** included.
- **Start analysis**: begins a new analysis run.
- **Stop**: requests stopping the currently running analysis.

You’ll also see:

- **Recent runs**: the latest run statuses and progress.
- **Processed ranges**: which ranges have already been processed.
- **Unprocessed gaps**: missing coverage (click a gap to auto-fill Start/End).

### Insights

Shows summaries computed from stored email metadata:

- **Top senders**: most frequent senders with copyable sender/list-id queries
- **Top domains**: most frequent sender domains
- **Categories**: category breakdown
- **Yearly trend**: year-over-year totals (simple view for now)

If Insights are empty, run an analysis first.

### Sender Classification

This is the main tab for organizing your senders into categories and deciding what to do with them. Mail Mind never modifies your emails — everything here is read-only analysis and suggestions that you act on yourself in Gmail.

**Step 1 — Run Classification**

Click **Run Classification** to assign labels to your senders using built-in rules (known domains and keyword patterns). This is instant and safe to re-run.

After running you'll see:
- Coverage percentage (how many emails belong to a classified sender)
- Per-label counts (how many senders and emails in each category)
- Unclassified count (senders with no label yet)

**Step 2 — Review labels (optional)**

Click any label (e.g. Shopping) to see the senders under it. You can change a sender's labels by clicking **Edit** next to a row. Changes you make manually are never overwritten by future classification runs.

If you remove a label that was auto-assigned, it won't come back — the system remembers your removal.

**Step 3 — AI Enhancement (optional)**

If AI is configured, click **Enhance with AI** to classify remaining unclassified senders using Gemini. Each run processes 50 senders. Run it multiple times until the remaining count reaches zero. AI-assigned labels can be overridden the same way as rule-assigned ones.

**Step 4 — Copy filter queries**

Each label has a **Copy filter** button that copies a Gmail-compatible `from:` search query to your clipboard (e.g. `from:(@amazon.com OR @ebay.com)`). Paste this into Gmail's filter builder to create a filter for that label.

**Dispositions (coming soon)**

Once senders are classified, you'll be able to assign a disposition to each:
- **Archive** — keep for records or future reference
- **Delete** — safe to delete after reading (e.g. OTPs, delivery notifications)
- **Unsubscribe** — recurring emails you want to stop receiving
- **Undecided** — not sure yet

Dispositions are suggestions only. You act on them in Gmail yourself.

### Settings

Account management:

- Add an email account: choose **provider** (how Mail Mind connects to that mailbox) and your **email address**.
- **Gmail**: choose **Gmail**, add the account, then click **Connect Gmail**. Your browser opens Google’s sign-in and permission screen for **that** account. Approve the request; when you return to Mail Mind, the account should show as connected. If connect fails or the button does nothing, the deployment may not be finished on the server side — ask whoever runs Mail Mind for you.
- **Yahoo**: choose **Yahoo**, add the account. You do **not** use your normal Yahoo login password in Mail Mind. In Yahoo’s **Account security** on the web, create an **app password** (Yahoo shows a long code). Paste that code into Mail Mind and click **Connect Yahoo**.

Once an account is connected, analysis reads **metadata** from your provider (enough for patterns and insights). Mail Mind does not use this screen to download full email bodies for browsing.

