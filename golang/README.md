# Temporal Ops API Sample (Golang)

A sample application demonstrating Temporal workflows for managing privilege requests (breakglass scenarios) using Temporal Cloud Service APIs.

## Overview

This project implements a breakglass workflow that:
1. Elevates user privileges to `DEVELOPER` role
2. Waits for a specified duration (3 minutes by default)
3. Automatically reverts privileges back to `READ` role

## Prerequisites

- Go 1.19 or later
- Access to a Temporal Cloud account
- Temporal Cloud API key
- Running Temporal server (local or cloud)

## Project Structure

```
golang/
├── shared/
│   ├── activity.go       # Cloud operations activities
│   ├── workflow.go       # Breakglass workflow definition
│   ├── types.go          # Request/Response types
│   └── options.go        # Client configuration
├── worker/
│   └── main.go           # Worker that executes workflows
├── client/
│   └── main.go           # Client that starts workflows
└── api_key               # Temporal Cloud API key (not committed)
```

## Setup

### 1. Install Dependencies

```bash
go mod tidy
```

### 2. Configure API Key

Create an `api_key` file in the `golang/` directory with your Temporal Cloud API key:

```bash
echo "your-temporal-cloud-api-key" > api_key
```

**Important:** Make sure there are no trailing newlines or spaces in the API key file.

### 3. Configure Connection (Optional)

By default, the worker connects to `localhost:7233`. To customize:

```bash
# Set environment variable
export TEMPORAL_CLIENT_API_KEY="your-api-key"

# Or pass as command-line arguments
go run worker/main.go -target-host "your-host:7233" -namespace "your-namespace"
```

## Running the Application

### Start the Worker

The worker listens for workflow tasks and executes activities:

```bash
go run worker/main.go --api-key=`cat api_key` --namespace <your-namespace> --target-host <your-temporal-host>:7233
```

**Command-line options:**
- `--target-host`: Temporal server address (default: `localhost:7233`)
- `--namespace`: Temporal namespace (default: `default`)
- `--api-key`: Temporal Cloud API key (optional, can use file or env var)

### Start the Client

The client starts a new breakglass workflow:

```bash
go run client/main.go --api-key=`cat api_key` --namespace <your-namespace> --target-host <your-temporal-host>:7233
```

**Command-line options:** Same as worker

The client will:
1. Connect to Temporal
2. Start a `BreakglassRequestWorkflow`
3. Wait for the workflow to complete
4. Print the result

## Workflow Details

### BreakglassRequestWorkflow

**Input:** `BreakglassRequest`
```go
type BreakglassRequest struct {
    UserID        string
    RequestedBy   string
    Justification string
    Duration      string
    EmailID       string
}
```

**Behavior:**
1. Elevates user to `DEVELOPER` role via Temporal Cloud API
2. Sleeps for 3 minutes
3. Reverts user to `READ` role via Temporal Cloud API

**Output:** `PrivilegeResponse`

## Configuration Files

### api_key

Store your Temporal Cloud API key in this file. The worker and client will read it automatically.

**Security Note:** Add `api_key` to your `.gitignore` to prevent committing secrets.

## Development

### Adding New Workflows

1. Define workflow in `shared/workflow.go`
2. Define activities in `shared/activity.go`
3. Register workflow and activities in `worker/main.go`

## License

MIT
