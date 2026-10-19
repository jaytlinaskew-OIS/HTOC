# GTI Indicator Quality Rules

These rules define which Google Threat Intelligence indicators are suitable for future analysis and testing. They evaluate indicator quality and contextual usefulness.

## Query scope

- Use `DateAdded` as the time field.
- Include only indicators added during the previous 90 days. The current Playbook retrieves at most 1,000 candidates per execution.
- Owner must be Google Threat Intelligence.
- Allowed types: Address, EmailAddress, Host, and URL.
- `falsePositiveCount` is `0`. Prevents using an indicator that someone has already disputed as incorrectly classified as malicious.
- Rating is at least `3`. Baseline.
- Confidence is at least `50`. Baseline.
- `observationCount` must equal `0`. This confirms its has not already been added to HTOC Org.

Current 90-day TQL:

```text
rating in (3,4,5) and (confidence > 49) and (observationCount = 0) and (falsePositiveCount = 0) and (dateAdded >= "NOW() - 90 DAYS") and (ownerName in ("Google Threat Intelligence")) and typeName in ("Address","EmailAddress","Host","URL")
```



## Required contextual information



### Description

The indicator must contain a non-empty Description attribute. 

### Source

- Retain Source as provenance when present.
- Source presence and type-specific VirusTotal paths are not promotion gates because they did not reduce the initial population.



### Tags

- Retrieve every accessible owner copy having the same indicator type and exact value as the GTI candidate.
- Combine distinct, non-empty tags across those owner copies for evaluation. Trim surrounding whitespace and compare tag names case-insensitively.
- Cross-owner tags are used only for qualification. When an indicator is promoted, copy only the tags already attached to the original GTI-owned indicator; do not copy another owner's tags or generate a tag-provenance attribute.
- Require at least two distinct tags in the combined set.
- Require at least one combined tag other than `hex` or `dga`.
- If no other owner copy is accessible, evaluate only the GTI-owned copy.
- A GTI candidate tagged only `dga` may pass when another accessible owner supplies a useful tag such as `malware`, `C2`, or a malware-family name. It still fails when the complete combined tag set contains only `hex`, only `dga`, or both.



### Associated groups

Associated groups provide attribution and relationship context. They are not used as a separate promotion gate. For a qualified indicator, the Playbook reads the original GTI indicator's existing group associations and recreates those same associations on the HTOC Org indicator when ThreatConnect permits it. It does not create groups or generate a provenance attribute.

Covered **446,399 indicators** returned by the current 90-day TQL:

- **442,898 (99.2%)** had at least one associated Malware, Campaign, Intrusion Set, or Report.
- **3,501 (0.8%)** had none of those associated group types.
- **432,475** were associated with Malware.
- **9,997** were associated with an Intrusion Set.
- **4,148** were associated with a Campaign.
- **1,386** were associated with a Report.

Counts by group type overlap because one indicator can be associated with multiple groups or group types. 

In the 1,000-record type-stratified sample, 912 indicators had exactly one associated group, 68 had two, 13 had three or more, and seven had none. The sample contained 72 distinct Malware groups, 15 Campaigns, 12 Intrusion Sets, and six Reports. Common groups included ASYNCRAT, MIRAI, FORMBOOK, QUASARRAT, BEACON, CURLYFENCE, XWORM, UNC6676, UNC4403, APT42, and APT21.

Tags are attached to indicators, not inherited from their associated groups. In the same sample, 460 indicators had both tags and groups. Of 54 unique tags observed on grouped indicators, 33 appeared with multiple groups. Broad tags such as `malware`, `Phishing`, `pwn`, `Phishing and Other Frauds`, `dga`, and `spyware and malware` were shared across many groups. 

## 90-day Playbook volume estimate

The live comparison completed on October 8, 2026 used the current initial TQL and a type-stratified systematic sample of 1,000 indicators.

- Initial TQL population: **446,224**.
- Estimated passes using only tags on the GTI-owned copy: **64,577 (14.5%)**.
- Estimated passes using tags across all accessible owner copies: **74,525 (16.7%)**.
- Approximate 95% interval for the cross-owner estimate: **64,594–84,457**.
- **76 of 1,000 sampled indicators** were rescued by useful tags from another owner.

Initial population by indicator type:


| Type         | Initial population |
| ------------ | ------------------ |
| Address      | 5,321              |
| EmailAddress | 0                  |
| Host         | 81,909             |
| URL          | 358,994            |


Within the sample, 892 indicators existed in one accessible owner, 79 in two owners, 20 in three owners, and nine in four owners. Examples of owners supplying useful additional tags included abuse.ch ThreatFox, CISA Federal Feed, and Intel 471 Intelligence.

The initial population count is exact at query time. The passing counts are sample-based estimates because the normalized cross-owner tag rule cannot be expressed directly in the initial TQL.

## ThreatConnect Playbook design plan

The Playbook will use **ThreatConnect Get Indicators** for every indicator TQL lookup. The generic ThreatConnect API request App will not be used to execute the initial TQL.

### Triggers

- Keep a WebHook Trigger for controlled testing.
- Add a daily Timer Trigger only after the WebHook path passes validation.
- The current validation build uses the rolling 90-day query and a maximum of 1,000 candidates per execution.



### 1. Pull GTI candidates

Use **ThreatConnect Get Indicators v1.0.9** with:

- Action: `TQL`
- TQL:

```text
rating in (3,4,5) and (confidence > 49) and (observationCount = 0) and (falsePositiveCount = 0) and (dateAdded >= "NOW() - 90 DAYS") and (ownerName in ("Google Threat Intelligence")) and typeName in ("Address","EmailAddress","Host","URL")
```

- `fail_on_no_results`: `false`
- `max_results`: `1000` in the current validation build.
- Required outputs: `tc.indicators.entity`, `tc.indicators.summary`, `tc.indicators.type`, `tc.indicators.owner_name`, `tc.indicators.rating`, `tc.indicators.confidence`, `tc.indicators.count`, and `tc.response.json.raw` where available.

If the returned count reaches `max_results`, stop promotion and raise an overflow notification rather than silently processing a truncated result. If daily bursts exceed the supported limit, partition the initial pull by indicator type or run the timer more frequently with an idempotent destination check.

### 2. Iterate through candidates

Use an **Iterator** over the synchronized entity, summary, type, owner, rating, and confidence arrays from ThreatConnect Get Indicators. Each iteration evaluates one GTI candidate. Failed candidates end their branch; the Playbook does not create separate REVIEW or REJECT records.

### 3. Confirm Description

Read the candidate's Description from the native Get Indicators raw output and extract it with **JMESPath**. Require a non-empty value. During implementation, validate that the installed Get Indicators version includes Description or attributes in `tc.response.json.raw`. If it does not, use an entity-scoped enrichment step for Description; do not replace the initial native Get Indicators TQL call with a generic API request.

### 4. Retrieve cross-owner tags for qualification

Use **ThreatConnect Tags** with Action `Get` and Get By `TQL`. Query Tags associated with any accessible Indicator having the current candidate's exact type and summary:

```text
hasIndicator(typeName in ("<TYPE>") and summary = "<SUMMARY>")
```

This cross-owner result is evaluation-only. It is not copied directly to the destination indicator.

### 5. Normalize tags for comparison

Extract the original tag names with **JMESPath**. Use **String Operations** to strip surrounding whitespace and lowercase the names. Use **Array Operations — Difference** against an empty set to deduplicate the normalized values, then require more than one result.

Use **Array Operations — Difference** again against `["hex", "dga"]` and require at least one remaining value. Keep the original GTI tag spelling separate from this normalized evaluation path.

### 6. Retain only original GTI metadata

After the candidate passes and is created in HTOC Org:

1. Read Tags directly from the original GTI `TCEntity` and copy only those GTI-owned tag names.
2. Read group associations directly from the original GTI `TCEntity` and recreate those associations on the HTOC indicator when permitted.
3. Do not create groups, copy another owner's tags, or synthesize tag/group provenance attributes.



### 7. Apply the promotion decision

The candidate passes only when:

- Description is non-empty.
- The combined cross-owner set contains at least two distinct normalized tags.
- The combined set contains at least one tag other than `hex` or `dga`.

If an across-owner lookup fails and the GTI copy does not already pass, fail closed for that execution and allow the candidate to be reconsidered on the next scheduled run.

### 8. Check the destination owner

Before creation, use **ThreatConnect Get Indicators — TQL** again with the exact type, summary, and destination owner. This makes the Playbook idempotent and prevents duplicate work if a candidate reappears in the rolling time window.

### 9. Create or update the qualified indicator

On the passing branch only:

1. Use **ThreatConnect Create Indicators** with the destination owner, original type and summary, and the indicator-level rating and confidence already validated by the initial TQL.
2. Use **ThreatConnect Attributes** to retain the GTI Description and Source when present.
3. Use **ThreatConnect Tags** to copy only the tags already attached to the original GTI indicator. Cross-owner tags remain qualification-only.
4. Copy the original GTI indicator's existing group associations to the new HTOC Org indicator when permitted. Do not create new groups or synthesize a group-provenance attribute.
5. Add the static tag `GTI Indicator PB` to identify records created by this process.



### 10. Validation and operational controls

- Validate first with the WebHook Trigger and a small `max_results`.
- Confirm the Get Indicators raw output contains the Description needed by JMESPath.
- Confirm nested Iterator outputs flatten correctly into a StringArray.
- Confirm Array Operations deduplicates case-normalized tags before counting.
- Confirm dynamic TQL escaping with Address, Host, EmailAddress, and complex URL values.
- Confirm destination creation is idempotent.
- Record execution counts for candidates, GTI-tag passes, cross-owner rescues, final passes, creations, existing destination records, lookup errors, and max-result overflows.
- Keep the Timer Trigger disabled until all validation checks pass.

