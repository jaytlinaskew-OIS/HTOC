# GTI Indicator Quality Rules

These rules define which Google Threat Intelligence indicators are suitable for future analysis and testing. They evaluate indicator quality and contextual usefulness.

## Query scope

- Use `DateAdded` as the time field.
- Include only indicators added during the previous 90 days initially. Playbook will look at the last 24 hours.
- Owner must be Google Threat Intelligence.
- Allowed types: Address, EmailAddress, Host, and URL.
- `falsePositiveCount` is `0`. Prevents using an indicator that someone has already disputed as incorrectly classified as malicious.
- Rating is at least `3`. Baseline.
- Confidence is at least `50`. Baseline.
- `observationCount` must equal `0`. This confirms its has not already been added to HTOC Org.



## Required contextual information



### Description

The indicator must contain a non-empty Description attribute. 

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



### Tags

- Require at least two distinct, non-empty source tags.



### Associated groups

Associated groups provide attribution and relationship context. They are retained as provenance rather than treated as tags or used as a separate promotion gate.

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

The live comparison completed on October 5, 2026 covered indicators added since July 7, 2026.

Sample results by indicator type:


| Type         | Initial population |
| ------------ | ------------------ |
| Address      | 5,334              |
| EmailAddress | 0                  |
| Host         | 81,961             |
| URL          | 359,105            |


