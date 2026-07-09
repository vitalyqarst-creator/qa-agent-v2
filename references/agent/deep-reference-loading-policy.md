# Deep Reference Loading Policy

Default runtime scenarios must load compact operational rules only.

Deep references are allowed only for:

- explicit debug or audit scenarios;
- targeted remediation scenarios where the finding id requires detailed guidance;
- validator-failure follow-up after compact rule cards and remediation map are insufficient;
- human documentation that is not included in default prompt context.

Default writer, reviewer and remediation scenarios must not load long examples, historical canary reports, full reviewer-only rubrics or all optional table templates merely as safety padding. The default path should load compact rule cards/maps, then route to an explicit deep scenario when the work actually needs detailed examples or diagnostics.

Do not increase scenario limits to hide instruction growth. Split context into compact default and deep/debug groups, preserve validator gates, and keep all active scenarios above their configured minimum headroom.
