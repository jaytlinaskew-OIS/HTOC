# 🔐 MITRE NLP Auto-Tagging System (Technical Overview)

This project creates a semantic tagging system using MITRE ATT&CK data to help label descriptions with relevant ATT&CK techniques.

---

## 📌 Purpose
Traditional rule-based tagging or keyword searches often fall short in accurately labeling unstructured threat intel or security logs. This system leverages transformer-based NLP to semantically compare input text with MITRE ATT&CK technique descriptions, providing smarter matches even if exact keywords differ.

---

## ⚙️ Main Functional Components

### `preprocess_description`
Cleans the technique descriptions before vectorizing them:
- Removes HTML tags
- Decodes HTML entities
- Removes citation references
- Strips whitespace

> Helps improve vector quality and remove noise.

### `get_vector(doc)`
Extracts a dense vector from spaCy transformer pipeline (`en_core_web_trf`):
- Uses the last hidden layer of the transformer
- Averages all token vectors into a single sentence vector

> Converts text into semantic embedding space.

### `infer_tactic_hints(text)`
Extracts high-level hints from input text:
- If text includes words like "network" or "initially access", suggests corresponding MITRE tactics like `command-and-control`, `initial-access`

> Boosts relevant technique scores based on implied tactics.

### `semantic_tagging(text, dictionary, threshold, keyword_boost=0.1)`
The main function for tagging:
1. Vectorizes input text
2. Compares it to each technique’s vector via cosine similarity
3. Applies additional scoring:
   - **Keyword match boost**: adds to score if key terms (like "exploit", "CVE") from technique are found
   - **Tactic hint boost**: if implied tactics from input match technique tactics
4. Sorts results by final score and returns top match

Output structure:
```python
{
  "external_id": "T1055.011",
  "technique_name": "Extra Window Memory Injection",
  "tactics": ["defense-evasion"],
  "similarity": 0.89,
  "final_score": 1.24
}
```

> Balances NLP similarity with contextual and keyword cues.

---

## How Matching Works
When a user submits free-form input text:
- It's embedded into a semantic vector
- Compared against all techniques' descriptions
- Boosted by matching keywords (e.g., CVE, malware)
- Further refined using inferred tactics (e.g., "initial access")
- Output sorted by relevance

---

## Example Usage
```python
text = """
CISA discovered traffic between 198.98.54[.]209 and NLM that resembles patterns from CVE-2025-282 and CVE-2025-283.
"""
results = semantic_tagging(text, mitre_nlp_dict, threshold=0.9)

for match in results:
    print(f"✅ {match['external_id']} - {match['technique_name']}")
    print(f"  - Tactics: {', '.join(match['tactics'])}")
    print(f"  - Semantic Similarity: {match['similarity']}")
    print(f"  - Final Score: {match['final_score']}")
```

Sample Output:
```
✅ T1562.006 - Indicator Blocking
  - Tactics: defense-evasion
  - Semantic Similarity: 0.97
  - Final Score: 1.27
```

---

## Dependencies
- `spacy`
- `en_core_web_trf`
- `numpy`
- `stix2`
- `mitreattack` (for parsing downloaded STIX data)

Install:
```bash
pip install spacy numpy stix2 mitreattack
python -m spacy download en_core_web_trf
```

---

