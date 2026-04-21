# Temporal Ops API Sample

This repository demonstrates how to use the Temporal Cloud API to list users using Python and gRPC.

## Setup

### 1. Create a virtual environment

```bash
python3 -m venv venv
```

### 2. Activate the virtual environment

**On macOS/Linux:**
```bash
source venv/bin/activate
```

**On Windows:**
```bash
venv\Scripts\activate
```

### 3. Install requirements

```bash
pip install -r requirements.txt
```

## Run

Execute the list_users script:

```bash
TEMPORAL_CLOUD_API_KEY=`cat api_key` python -m list_users
```

## Billing Dashboard

Generate an HTML billing dashboard from a Temporal Cloud billing CSV export.

```bash
# Output defaults to <csv_name>_dashboard.html
python3 generate_billing_dashboard.py billing_report.csv

# Or specify an output path
python3 generate_billing_dashboard.py billing_report.csv my_dashboard.html
```

The dashboard shows:
- Total billed, active namespaces, platform fees, and namespace usage cost
- Cost breakdown by namespace (horizontal bar chart)
- Cost split by SKU meter — Actions, Active Storage, Retained Storage, Enterprise Plan (donut chart)
- Daily cost trend (stacked bar chart)
- Per-namespace, per-meter detail table with quantities

Open the generated `.html` file in any browser — no server required.