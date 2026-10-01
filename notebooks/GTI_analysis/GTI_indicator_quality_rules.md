# GTI Indicator Quality Rules

These rules define which Google Threat Intelligence indicators are suitable for future analysis and testing. They evaluate indicator quality and contextual usefulness, not observation yield.

## Query scope

- Use `DateAdded` as the time field.
- Include only indicators added during the previous 90 days.
- Owner must be Google Threat Intelligence.
- Allowed types: Address, EmailAddress, Host, and URL.
- `indicatorActive` is `true`.
- `privateFlag` is `false`.
- `falsePositiveCount` is `0`.
- Rating is at least `3`.
- Confidence is at least `50`.
- `observationCount` must equal `0`. This confirms its has not already been added to HTOC Org.

## Required contextual information

### Description

The description must:

- Contain at least 100 non-whitespace characters.
- Provide analytical context rather than boilerplate, a placeholder, or a restatement of the indicator.

Qualifying evidence can include Google malware analysis, machine-learning findings, sandbox or behavioral results, Mandiant family attribution, related malicious files or infrastructure, URL-scanning results, configuration extraction, trusted-partner reporting, security-researcher reporting, or evidence of widespread malicious activity.


### Sample descriptions below the minimum length

The following examples came from the stratified 90-day GTI sample. Each description fails the requirement of at least 100 non-whitespace characters.

| Type | Indicator | Non-whitespace characters | Description |
|---|---|---:|---|
| Address | `157.254.167.12` | 97 | This indicator is suspicious (medium severity). GTI's ML scoring model identified this indicator as suspicious. |
| Address | `14.135.120.20` | 93 | This indicator is suspicious (medium severity). Its verdict recently changed from malicious to suspicious. |
| Address | `5.44.15.70` | 94 | This indicator is suspicious (low severity). GTI's ML scoring model identified this indicator as suspicious. |
| Address | `77.122.150.88` | 90 | This indicator is suspicious (low severity). Its verdict recently changed from malicious to suspicious. |
| Host | `www.nidsim.nmailserveronlinehosting.store` | 93 | This indicator did not match our detection criteria and there is currently no evidence of malicious activity. |
| Address | `185.173.35.25` | 93 | This indicator is suspicious (medium severity). Its verdict recently changed from malicious to suspicious. |
| Address | `92.118.161.13` | 93 | This indicator is suspicious (medium severity). Its verdict recently changed from malicious to suspicious. |
| Address | `185.65.105.60` | 94 | This indicator is suspicious (low severity). GTI's ML scoring model identified this indicator as suspicious. |
| Address | `84.237.229.49` | 94 | This indicator is suspicious (low severity). GTI's ML scoring model identified this indicator as suspicious. |
| Address | `173.246.104.128` | 94 | This indicator is suspicious (low severity). GTI's ML scoring model identified this indicator as suspicious. |
| Host | `activity-privacy-sources.ru` | 93 | This indicator is suspicious (medium severity). Its verdict recently changed from malicious to suspicious. |
| Host | `recycle-garden.net` | 93 | This indicator is suspicious (medium severity). Its verdict recently changed from malicious to suspicious. |
| Address | `58.208.92.132` | 93 | This indicator is suspicious (medium severity). Its verdict recently changed from malicious to suspicious. |
| Host | `backup.xoilacztm.tv` | 93 | This indicator is suspicious (medium severity). Its verdict recently changed from malicious to suspicious. |
| Host | `quantri.xoilacztm.tv` | 93 | This indicator is suspicious (medium severity). Its verdict recently changed from malicious to suspicious. |

### Source
- Source is required.
- It must be a valid HTTPS URL from an approved provider; the current approved provider is VirusTotal.
- Its path must agree with the indicator type:
  - Address: `/gui/ip-address/`
  - Host: `/gui/domain/`
  - URL: `/gui/url/`
  - EmailAddress: an approved, type-appropriate provider path.

### Threat assessment

- Threat-assessment rating is present and at least `3`.
- Threat-assessment confidence is present and at least `50`.
- Values are complete and consistent with the indicator-level thresholds.

### Analytic context

Analytic context is evaluated as a promotion gate for the ThreatConnect playbook. An indicator passes when at least one of these conditions is met:

1. **Qualified associated group:** A group has a non-empty ID, a non-empty name, and a type of Malware, Campaign, Intrusion Set, or Report.
2. **Strong threat tag:** When no qualified group is available, at least one tag clearly identifies a threat concept, malware family, campaign, or malicious behavior.
3. **Multiple behavioral tags:** When no qualified group or strong threat tag is available, at least two distinct, meaningful behavioral tags provide useful context.

A closed allowlist of every accepted tag must not be used. New malware-family or campaign tags, such as `emotet`, must not fail merely because they are new. Normalize tag names, classify known tags by signal strength, accept previously unseen non-administrative tags for review, and retain an audit report of unknown tags.

Weak or generic tags do not satisfy the rule by themselves. Examples include a type label such as `ip`, a single infrastructure label such as `ns-port`, a single generic web label such as `external-resources`, and neutral content categories. Empty, duplicated, or purely administrative tags also do not count.

Recommended decision logic:

```python
passes_context = (
    has_qualified_group
    or has_strong_threat_tag
    or has_at_least_two_behavioral_tags
)
```

The latest full-population tag review covered 443,065 indicators that already met the 90-day, owner, type, zero-observation, rating, confidence, and source requirements:

- 439,558 had a qualified associated group.
- 142,240 group-qualified indicators also had tags.
- 707 unique normalized tags appeared among group-qualified indicators.
- Qualified groups should therefore be the primary context signal; tag evaluation is principally a fallback for indicators without a qualified group.
- Exact totals may change slightly between runs because the GTI source is live.

## Required provenance

Retain enough provenance to trace and reproduce every accepted indicator:

- Indicator ID
- Indicator type
- Canonical indicator value or summary
- Date added
- Owner
- Source URL
- Rating and confidence
- Threat-assessment rating and confidence
- Verdict
- Threat Level
- External Score
- Description
- Tags
- Associated groups

## Optional attributes

- Category is optional.
- When Category is present, it must contain a meaningful provider/category value rather than an empty value or placeholder.

## Excluded as a quality criterion

- Observe yield is not part of the indicator-quality decision.
- Observation count is used only as the requested query constraint (`observationCount = 0`), not as evidence that an indicator is analytically useful.

## First-failure evaluation order

For mutually exclusive failure reporting, evaluate records in this order and assign each rejected record to the first rule it fails:

1. Threat-assessment completeness and thresholds
2. Type-specific indicator syntax and canonical-value consistency
3. Description quality and evidence requirements
4. Semantic threat tag or qualified associated group
5. Source validity and type consistency
6. Remaining base-quality and provenance requirements

## Latest reviewed population

The latest completed review evaluated 3,000 indicators from July 3 through October 1, 2026:

- 2,268 passed every finalized rule (75.6%).
- 732 failed at least one rule.
- First-failure totals:
  - 425 failed threat-assessment requirements.
  - 291 failed type-specific syntax validation.
  - 13 lacked both semantic tags and qualified associated groups.
  - 3 failed description-quality requirements.
