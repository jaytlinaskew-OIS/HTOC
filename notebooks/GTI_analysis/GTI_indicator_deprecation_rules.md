# GTI Indicator Deprecation Rules

## Purpose

Limit the number of active indicators placed in HTOC Org by the GTI Indicator Quality Promotion Playbook while retaining partner-observation history and supporting recovery.

## Scope

The deprecation Playbook manages only indicators that meet all of these conditions:

- Owner is `HTOC Org`.
- Tag `GTI Indicator PB` is present.
- Indicator is active.
- Manual exemption tag `GTI Retain` is not present.

It does not manage indicators created by other processes or existing HTOC indicators that the promotion Playbook skipped.

## Retention policy

- Never observed: deactivate 30 days after the indicator was added to HTOC Org.
- Observed at least once: retain until 90 days after `lastObserved`, then deactivate.
- Manual retention: applying `GTI Retain` prevents automatic deactivation.
- Deprecation action: set `active` to `false`; do not delete the indicator.

Deactivation preserves the indicator, its tags, attributes, associations, and observation history. It can be reversed by setting `active` to `true`.

At an intake rate near 1,000 indicators per day, the 30-day unobserved window targets an active baseline near 30,000 unobserved indicators rather than approximately 90,000 after 90 days. Observed indicators may remain active longer because their 90-day clock restarts with the latest observation.

## Candidate TQL

```text
ownerName in ("HTOC Org") and hasTag(summary in ("GTI Indicator PB")) and NOT hasTag(summary in ("GTI Retain")) and indicatorActive = true and (((observationCount = 0) and (dateAdded <= "NOW() - 30 DAYS")) or ((observationCount > 0) and (lastObserved <= "NOW() - 90 DAYS")))
```

This TQL was validated successfully against the target ThreatConnect instance on October 21, 2026. It currently returns zero because no active HTOC Org indicators are yet tagged `GTI Indicator PB`.

## Playbook design

1. WebHook Trigger supports controlled testing.
2. Disabled daily Timer is scheduled for 6:45 a.m. after validation.
3. ThreatConnect Get Indicators runs the candidate TQL with `max_results` set to `1000`.
4. Iterator processes the returned indicator IDs one at a time.
5. HTTP Client sends `PUT /api/v3/indicators/{id}` with `{"active":false}`.

The initial query uses the native ThreatConnect Get Indicators app. The HTTP Client is used only for the update because the installed ThreatConnect Update Indicators app does not expose the indicator `active` field.

## Operational controls

- Keep the Timer disabled until the WebHook path has been tested successfully.
- Confirm the ThreatConnect token variable referenced as `@tc_token` is available to the HTTP Client app after import.
- Review the candidate count before the first deactivation run.
- If a run reaches 1,000 candidates, run it again after completion or increase its frequency so the backlog does not grow.
- Review HTTP Client failures for locked indicators or permission problems.
- Do not replace deactivation with deletion without a separately approved retention and recovery policy.
