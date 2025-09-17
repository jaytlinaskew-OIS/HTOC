# alyn-threatconnect

Lightweight ThreatConnect client (GET-only) with a convenience `get_tc_data(days)` function.

Quickstart (PowerShell):

```
py -m pip install --upgrade pip build
py -m build --wheel
```

Usage:

```python
from AlynThreatConnect import get_tc_data

df = get_tc_data(7)
print(df.head())
```
