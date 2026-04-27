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

- **Start/End dates**: choose the date range you want analyzed.
  - The UI uses an inclusive end date.
  - Internally, the system uses a half-open range: \([start, endExclusive)\).
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

- Add an email account (provider + email)

## Current limitation (temporary)

Provider integrations (Gmail OAuth / Yahoo app-password) are not implemented yet. Until then, analysis runs generate deterministic “stub” email metadata so you can use the product flows and insights UI during development.

