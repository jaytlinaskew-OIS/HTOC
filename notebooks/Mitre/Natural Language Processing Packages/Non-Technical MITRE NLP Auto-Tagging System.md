# 🔐 MITRE NLP Auto-Tagging System (Non-Technical Overview)

This project helps **automatically label cybersecurity text** using the **MITRE ATT&CK** framework. It uses NLP text analysis to figure out which techniques are being described, even if specific keywords aren't used.

---

## 📌 Purpose
Traditional rule-based tagging or keyword searches often fall short in accurately labeling unstructured threat intel or security logs. This system leverages transformer-based NLP to semantically compare input text with MITRE ATT&CK technique descriptions, providing smarter matches even if exact keywords differ.

---

## How It Works (Conceptual)

### Step 1: Clean the MITRE Data
We clean up MITRE’s descriptions (remove clutter like HTML or citations) so the system focuses on what matters.

### Step 2: Teach the System the MITRE Techniques
We use spaCy (a powerful language tool) to turn each MITRE technique description into a vector that represents its meaning.

### Step 3: Process Your Text
When you enter a report, the system does the same thing: it turns it into a vector for comparison.

### Step 4: Smart Matching
It then:
- Compares your text’s meaning with all MITRE techniques
- Boosts matches that mention important keywords like "exploit", "malware", "CVE"
- Looks for clues about the kind of activity (e.g., network access = command-and-control)

Finally, it ranks the best matches and shows the top match.

---

## Example

### Input:
```
CISA conducted a hunt on IoC's obtained from ongoing investigations regarding recently disclosed CVE-2025-282 and CVE-2025-283.
CISA Analysts discovered traffic on 6JAN2025 between 198.98.54[.]209 and NLM device 130.14.13.10 that has similar traffic patterns to previously confirmed compromises at separate agencies.
CISA recommends NLM verifies their Ivanti versions and investigate this activity to determine if any malicious events have occurred.
```

### Output:
```
✅ T1562.006 - Indicator Blocking
  - Tactics: defense-evasion
  - Semantic Similarity: 0.97
  - Final Score: 1.27
```

This tells us the text is most related to the MITRE technique “Indicator Blocking,” and it explains what tactic it fits into.

---

## Technical Aspects

This system uses:
- **spaCy** to understand and compare text
- **MITRE STIX JSON** as the knowledge base
- Python functions that:
  - Clean up and analyze descriptions
  - Extract keywords and potential clues
  - Calculate smart scores for best match

---