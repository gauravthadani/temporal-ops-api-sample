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