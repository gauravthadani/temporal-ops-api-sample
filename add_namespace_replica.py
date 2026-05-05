#!/usr/bin/env python3
"""
Adds a replica region to a Temporal Cloud namespace.

Flow:
  1. GetNamespace — fetch current spec and resource_version
  2. AddNamespaceRegion — submit the change
  3. Poll GetNamespace until the new region appears in spec.regions
"""

import asyncio
import os
import sys

from temporalio.api.cloud.cloudservice.v1 import (
    AddNamespaceRegionRequest,
    GetNamespaceRequest,
)
from temporalio.client import CloudOperationsClient

CLOUD_API_VERSION = "v0.14.0"


async def add_namespace_replica(api_key: str, namespace_name: str, region: str) -> None:
    client = await CloudOperationsClient.connect(
        api_key=api_key,
        rpc_metadata={"temporal-cloud-api-version": CLOUD_API_VERSION},
    )
    cloud_service = client.cloud_service

    # Step 1: Fetch the current namespace to get its resource_version and current regions.
    print(f"Fetching namespace '{namespace_name}' ...")
    get_resp = await cloud_service.get_namespace(
        GetNamespaceRequest(namespace=namespace_name)
    )
    ns = get_resp.namespace
    resource_version = ns.resource_version
    current_regions = list(ns.spec.regions)
    print(f"  Current regions : {current_regions}")
    print(f"  Resource version: {resource_version}")

    if region in current_regions:
        print(f"Region '{region}' is already present — nothing to do.")
        return

    # Step 2: Submit AddNamespaceRegion.
    print(f"\nSubmitting AddNamespaceRegion for region '{region}' ...")
    await cloud_service.add_namespace_region(
        AddNamespaceRegionRequest(
            namespace=namespace_name,
            region=region,
            resource_version=resource_version,
        )
    )
    print("AddNamespaceRegion accepted.")

    # Step 3: Poll GetNamespace until the new region appears.
    poll_interval = 5
    max_poll_interval = 60
    print("\nWaiting for region to appear in namespace spec ...")

    while True:
        await asyncio.sleep(poll_interval)
        get_resp = await cloud_service.get_namespace(
            GetNamespaceRequest(namespace=namespace_name)
        )
        regions = list(get_resp.namespace.spec.regions)
        print(f"  Current regions: {regions}")

        if region in regions:
            print(f"\nRegion '{region}' has been added to namespace '{namespace_name}'.")
            return

        poll_interval = min(poll_interval * 2, max_poll_interval)


if __name__ == "__main__":
    api_key = os.environ.get("TEMPORAL_CLOUD_API_KEY")
    if not api_key:
        print("ERROR: Set the TEMPORAL_CLOUD_API_KEY environment variable.")
        sys.exit(1)

    namespace = os.environ.get("TEMPORAL_NAMESPACE", "gaurav-mrn-ops-sample.a2dd6")
    region = os.environ.get("TEMPORAL_REPLICA_REGION", "gcp-us-central1")

    asyncio.run(add_namespace_replica(api_key=api_key, namespace_name=namespace, region=region))
