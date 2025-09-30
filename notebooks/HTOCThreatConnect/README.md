# alyn-threatconnect

Lightweight ThreatConnect client (GET-only) with a convenience `get_v3_threatconnect_data(lastObserved_date=None)` function.

Quickstart (PowerShell):

```
py -m pip install --upgrade pip build
py -m build --wheel
```

Usage:

```python
from AlynThreatConnect import get_v3_threatconnect_data

df = get_v3_threatconnect_data(lastObserved_date=None) #none can be set to a specific date like '2025-01-01' by default it is '2023-01-01' with none as its input
print(df.head())
```
