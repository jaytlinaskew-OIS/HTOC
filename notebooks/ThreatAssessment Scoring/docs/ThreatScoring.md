## Threat Assessment Scoring Framework

A clear, actionable guide for scoring threat indicators using ThreatConnect data and external enrichment.

---

### 1. Continuity Score (by Indicator Type)

Assign a continuity score based on ThreatConnect’s indicator classification:

| Indicator Type         | Continuity Score |
|------------------------|-----------------|
| IP Address / IPv6      | 1               |
| Domain / URL / Email   | 2               |
| File Hash (SHA1/256/MD5)| 3              |

<details>
<summary>Python Example</summary>

```python
continuity_score = {
    "IP Address": 1,
    "IPv6 Address": 1,
    "Domain": 2,
    "URL": 2,
    "Email Address": 2,
    "File Hash - SHA1": 3,
    "File Hash - SHA256": 3,
    "File Hash - MD5": 3
}
```
</details>

---

### 2. Actions Reported / Behavioral Context

**Sources in ThreatConnect:**
- ThreatAssess scores or sightings
- Tags/attributes (e.g., “Scanning,” “Phishing”)
- Links to incidents/adversaries

**How to Use:**
- Categorize indicators by behavioral tags or sightings
- Leverage MITRE ATT&CK TTPs and action tags
- Associate with relevant incidents

---

### 3. Infrastructure Context

**ThreatConnect Support:**
- WHOIS, reverse DNS, ASN data (as attributes)
- Integrate with passive DNS/domain tools for enrichment

**Tips:**
- Export IPs for external enrichment (e.g., Farsight DNSDB)
- Tag known CDN ASNs/domains and discount in scoring

---

### 4. Scoring Model

#### Base Scores

| Indicator Type        | Base Score |
|-----------------------|------------|
| SHA256 / MD5 Hash     | 600        |
| Email Address         | 500        |
| Domain / URL          | 400        |
| IP Address (IPv4)     | 300        |

#### Positive Score Triggers

| Trigger                             | Score Impact  | Notes                      |
|--------------------------------------|---------------|----------------------------|
| Reported in ThreatFeed as malicious  | +150          | External confirmation      |
| Linked to phishing/malware behavior  | +100          | Tags or sightings          |
| Multiple sightings across sources    | +50–100       | Based on count             |
| Tied to known adversary/campaign     | +200          | ThreatConnect associations |
| Hash with verified malware           | +250          | Strong indicator           |
| Repeated bad behavior over time      | +50/event     | Threat persistence         |

#### Negative Score Triggers

| Trigger                                         | Score Impact   | Notes                    |
|-------------------------------------------------|----------------|--------------------------|
| Shared infrastructure (CDN, DNS, cloud hosting) | -100 to -200   | De-risks false positives |
| Inactive (no bad activity in X days)            | -X/week        | Use time decay           |
| Known benign usage (domain/IP)                  | -150           | Based on whitelists      |
| Score aging (natural decay)                     | -Y/30 days     | Tune to intel needs      |
| Resolved issue (incident closed/false positive) | -200           | Manual/automated         |

---

### 5. Time-Based Decay

Apply score decay if no new sightings/behaviors occur, or for lower continuity types.

**Example Decay (per 30 days of inactivity):**
- Hashes: –10 points
- Domains: –25 points
- IPs: –40 points

Customize decay curves as needed.

---

### 6. Score Range & Risk Levels

| Score Range | Risk Level      | Action                            |
|-------------|----------------|-----------------------------------|
| 800–1000    | Critical Threat| Block, alert, auto-escalate       |
| 600–799     | High Suspicion | Investigate, watchlist            |
| 400–599     | Low Risk       | Log only/contextual enrichment    |
| 0–399       | Benign / Clean | Suppress or ignore                |

---

> **Note:** Adjust scoring logic and thresholds to fit your organization’s risk appetite and operational needs.
