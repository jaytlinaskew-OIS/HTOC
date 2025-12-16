# HTOC-threatconnect

Lightweight ThreatConnect client (GET-only) with a convenience `get_v3_threatconnect_data(lastObserved_date=None)` function.

## Installation

### From Wheel File

If you have a pre-built `.whl` file:

```powershell
py -m pip install Z:\wheels\HTOC_threatconnect-0.1.10-py3-none-any.whl
```

### Upgrade Existing Installation

```powershell
py -m pip install --upgrade Z:\wheels\HTOC_threatconnect-0.1.10-py3-none-any.whl
```

## Usage

```python
from HTOCThreatConnect import get_v3_threatconnect_data

# Get all data from default date (2023-01-01)
df = get_v3_threatconnect_data()

# Get data from a specific date
df = get_v3_threatconnect_data(lastObserved_date='2025-01-01')

print(df.head())
```

## Requirements

- Python 3.7+
- Access to Z drive
- Required packages will be installed automatically during installation
