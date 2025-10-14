# Temporal Ops API Sample

This repository includes the Temporal API as a git subtree.

## Git Subtree Setup

The Temporal API is included in the `api/` directory using git subtree:

```bash
git subtree add --prefix=api https://github.com/temporalio/api.git master --squash
```

### Updating the subtree

To pull updates from the Temporal API repository:

```bash
git subtree pull --prefix=api https://github.com/temporalio/api.git master --squash
```
