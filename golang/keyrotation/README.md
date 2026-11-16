# Temporal Ops API Sample: API Key Rotation (Golang)

A sample application that rotates Temporal Cloud API keys automatically, using a Temporal workflow and the Temporal Cloud Ops API.

## Overview

A single namespace-scoped service account rotates its own API keys:
1. Create an API key for the service account by hand. The worker uses it to seed a mock external secret store (`secret_store.json`) on first run.
2. The `KeyRotationWorkflow` creates a new API key for the same service account every 5 minutes, and writes it to the secret store. Each key expires after 25 hours (Temporal Cloud requires an expiry more than 24 hours away).
3. The worker connects to Temporal with `client.NewAPIKeyDynamicCredentials`, and to the Cloud Ops API with a `cloudclient.APIKeyReader`. Every 5 minutes it switches to the latest key in the secret store.

This works because a service account can always create new API keys for itself.

The worker's key is never more than about 10 minutes old, so it always has close to a full day of validity left. It also waits until a new key is a minute old before using it, because new keys can take up to a minute to propagate.

## Prerequisites

- Go 1.19 or later
- Access to a Temporal Cloud account
- One API key for that service account (the seed key)

## Project Structure

```
keyrotation/
├── go.mod
├── shared/
│   ├── activity.go       # Cloud operations activities (create API key)
│   ├── workflow.go       # Key rotation workflow definition
│   ├── secret_store.go   # Mock external secret store
│   └── types.go          # Request/Response types
├── worker/
│   └── main.go           # Worker that runs the rotation workflow, using the rotated keys
└── client/
    └── main.go           # Client that starts the key rotation workflow
```

## Setup

### 1. Install Dependencies

```bash
go mod tidy
```

### 2. Create the Service Account and Seed Key
1. Create a namespace API key
Save the seed key in an `api_key` file in the `keyrotation/` directory:

```bash
echo "your-seed-api-key" > api_key
```

The seed key only needs to last until the worker has created its first rotated key.

### 3. Configure Service Account

Set `OwnerID` in `client/main.go` to the ID of the service account.

## Running the Application

Run all commands from the `keyrotation/` directory, so every process shares the same `secret_store.json`.

### Start the Worker

```bash
go run ./worker --namespace <your-namespace> --target-host <your-temporal-host>:7233
```

On first run, the worker copies the seed key from `api_key` into the secret store. After that, it only uses keys from the secret store.

### Start the Key Rotation Workflow

```bash
go run ./client --namespace <your-namespace> --target-host <your-temporal-host>:7233
```

The workflow creates the first key straight away. If the workflow is already running, the client reuses it.

To check that the worker keeps working across rotations, run:

```bash
temporal workflow execute \
  --type HelloWorkflow --task-queue key-rotation-queue --input '"world"' \
  --namespace <your-namespace> --address <your-namespace>.tmprl.cloud:7233 \
  --api-key "$(jq -r .token secret_store.json)"
```

This uses the current rotated key from the secret store, so it also checks that the latest key works.

## Workflow Details

### KeyRotationWorkflow

**Input:** `KeyRotationRequest`
```go
type KeyRotationRequest struct {
    OwnerID  string
    Interval time.Duration
    KeyTTL   time.Duration
}
```

**Behavior:**
1. Creates a new API key via the Temporal Cloud API and stores it in the secret store.
2. Sleeps for `Interval`.
3. Repeats. After 100 rotations, it continues as new to keep the history small.

The activity returns only the key ID and expiry. The key's token is never stored in workflow history.

To stop rotating, terminate the workflow `key-rotation-workflow`. Keys that were already created expire on their own.

**If the worker is down longer than the key lifetime (25 hours)**, every key will have expired. Create a new seed key, then delete `secret_store.json` so the worker re-seeds from `api_key`.

## Configuration Files

### secret_store.json

The mock secret store, created by the worker. In a real setup, replace `shared/secret_store.go` with Vault, AWS Secrets Manager or a similar store.

**Security Note:** `secret_store.json` contains a live API key and is listed in `.gitignore`.
