# Mail Mind — User Guide

Mail Mind helps you analyze your email patterns (senders, categories, trends). This guide is for **people using the product** after someone has deployed it for them. Server setup, OAuth clients, and environment variables belong in **Developer setup** — not here.

## Quick start

1. Open Mail Mind in your browser (use the URL from whoever runs the app for you).
2. Enter a **username** (this is your local workspace name)
3. Add an account in **Settings**
4. Go to **Analyze**, pick a date range, and start an analysis
5. View results in **Insights**

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

- **Top senders**: most frequent senders and domains
- **Top domains**: most frequent sender domains
- **Categories**: category breakdown
- **Yearly trend**: year-over-year totals (simple view for now)

If Insights are empty, run an analysis first.

### Settings

Account management:

- Add an email account: choose **provider** (how Mail Mind connects to that mailbox) and your **email address**.
- **Gmail**: choose **Gmail**, add the account, then click **Connect Gmail**. Your browser opens Google’s sign-in and permission screen for **that** account. Approve the request; when you return to Mail Mind, the account should show as connected. If connect fails or the button does nothing, the deployment may not be finished on the server side — ask whoever runs Mail Mind for you.
- **Yahoo**: choose **Yahoo**, add the account. You do **not** use your normal Yahoo login password in Mail Mind. In Yahoo’s **Account security** on the web, create an **app password** (Yahoo shows a long code). Paste that code into Mail Mind and click **Connect Yahoo**.

Once an account is connected, analysis reads **metadata** from your provider (enough for patterns and insights). Mail Mind does not use this screen to download full email bodies for browsing.

