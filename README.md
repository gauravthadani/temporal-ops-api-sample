# Temporal Ops API Sample

This repository includes the Temporal API and Temporal Cloud API as git subtrees.

## Setup



Add the Temporal API and Cloud API as git subtrees:

```bash
# Add Temporal API
git subtree add --prefix=api https://github.com/temporalio/api.git master --squash

# Add Temporal Cloud API
git subtree add --prefix=cloud-api https://github.com/temporalio/cloud-api.git main --squash
```

To pull updates:

```bash
# Update Temporal API
git subtree pull --prefix=api https://github.com/temporalio/api.git master --squash

# Update Temporal Cloud API
git subtree pull --prefix=cloud-api https://github.com/temporalio/cloud-api.git main --squash
```

## Compile

Generate Python code from protos:

```bash
cd api && python -m grpc_tools.protoc -I./  --python_out=../ --grpc_python_out=../ ./**/*.proto && cd ..
cd cloud-api && python -m grpc_tools.protoc -I./  -I../api --python_out=../ --grpc_python_out=../ ./**/*.proto && cd ..
```

## Run

Execute the list_users script:

```bash
TEMPORAL_CLOUD_API_KEY=`cat api_key` python -m list_users
```