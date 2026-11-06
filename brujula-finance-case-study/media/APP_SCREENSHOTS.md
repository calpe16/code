# Application screenshots with invented data

These three images are real widget renders of the private Flutter financial screen,
executed in an isolated local copy on 6 November 2026. They are not screen captures
of a personal account. No file export, real account or cloud connection was loaded.

The in-memory fixture was newly created for the portfolio: a fictional bank, income
of 2,000 EUR, food expense of 180 EUR, travel of 45 EUR and a pending item of 12.50 EUR.
The month is fixed to January 2026. The summary excludes the pending classification.
The movement view uses a text filter; it is not a complete statement.

- `app-summary.png`: financial overview, with unconfirmed balances explicitly shown.
- `app-movements.png`: filtered fictional transactions.
- `app-review.png`: pending classification and an empty import history.

The screenshot fixture passed a local Flutter widget test. It does not validate
the full app, its bank integrations or its security. The complete application
source is not part of this repository.

The numbered import-review images and `walkthrough.gif` are separate explanatory
illustrations of the extracted CLI logic, not additional full-application screenshots.
