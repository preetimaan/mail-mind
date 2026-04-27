# Mail Mind — User Guide

Mail Mind helps you analyze your email patterns (senders, categories, trends). It is local-first and runs on your machine.

## Quick start

1. Open the app at `http://localhost:3000`
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
  - **End (before, exclusive)**: first calendar day **not** included (same value the API calls `end_date_exclusive`).
- **Start analysis**: begins a new analysis run.
- **Stop**: requests stopping the currently running analysis.

You’ll also see:

- **Recent runs**: the latest run statuses and progress.
- **Processed ranges**: which ranges have already been processed.
- **Unprocessed gaps**: missing coverage (click a gap to auto-fill Start/End).

### Insights

Shows summaries computed from stored email metadata:

- **Top senders**: most frequent senders and domains
- **Categories**: category breakdown
- **Yearly trend**: year-over-year totals (simple view for now)

If Insights are empty, run an analysis first.

### Settings

Account management:

- Add an email account: choose **provider** (how Mail Mind connects) and your **email address**.
- **Gmail**: click **Connect Gmail** and finish Google’s OAuth consent. You need Gmail API OAuth client id/secret configured on the server (see developer setup).
- **Yahoo**: you do **not** type your normal Yahoo login password here. In Yahoo **Account security**, generate an **app password** (a long one-time code Yahoo shows you). Paste that code into Mail Mind and click **Connect Yahoo**. Mail Mind validates it with IMAP and stores it encrypted.

Analysis uses real provider metadata once the account is connected; Mail Mind keeps **metadata only** locally (see developer docs for detail).

