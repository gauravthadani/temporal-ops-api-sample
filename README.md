# Temporal Ops API Sample

This repository includes the Temporal API and Temporal Cloud API as git subtrees.

## Git Subtree Setup

### Temporal API

The Temporal API is included in the `api/` directory using git subtree:

```bash
git subtree add --prefix=api https://github.com/temporalio/api.git master --squash
```

To pull updates:

```bash
git subtree pull --prefix=api https://github.com/temporalio/api.git master --squash
```

### Temporal Cloud API

The Temporal Cloud API is included in the `cloud-api/` directory using git subtree:

```bash
git subtree add --prefix=cloud-api https://github.com/temporalio/cloud-api.git main --squash
```

To pull updates:

```bash
git subtree pull --prefix=cloud-api https://github.com/temporalio/cloud-api.git main --squash
```



Generate protos 

cd api && python -m grpc_tools.protoc -I./  --python_out=../ --grpc_python_out=./ ./**/*.proto

cd cloud-api && python -m grpc_tools.protoc -I./  -I../api --python_out=../ --grpc_python_out=./ ./**/*.proto