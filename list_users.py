#!/usr/bin/env python3
"""
Simple script to list users from Temporal Cloud using the Cloud API.
"""

import asyncio
import os
import sys
from temporalio.client import CloudOperationsClient
from temporalio.api.cloud.cloudservice.v1 import request_response_pb2


async def list_users(api_key: str, namespace: str = None, page_size: int = 10):
    client = await CloudOperationsClient.connect(
        api_key=api_key,
        rpc_metadata={"temporal-cloud-api-version": "v0.12.0"},
    )

    request = request_response_pb2.GetUsersRequest(
        page_size=page_size,
        page_token="",
    )

    if namespace:
        request.namespace = namespace

    print(f"Fetching users from Temporal Cloud...")
    if namespace:
        print(f"Filtering by namespace: {namespace}")
    print()

    response = await get_users(client, request)
    print_users(response)

    while response.next_page_token:
        print(f"More users available. Next page token: {response.next_page_token}")
        request.page_token = response.next_page_token
        response = await get_users(client, request)
        print_users(response)


async def get_users(client, request):
    return await client.cloud_service.get_users(request)


def print_users(response):
    if not response.users:
        print("No users found.")
    else:
        print(f"Found {len(response.users)} user(s):\n")
        for user in response.users:
            print(f"User ID: {user.id}")
            print(f"  Email: {user.spec.email}")
            print(f"  State: {user.state}")
            print(f"  Resource Version: {user.resource_version}")

            if user.spec.access and user.spec.access.account_access:
                print(f"  Account Role: {user.spec.access.account_access.role}")

            if user.spec.access and user.spec.access.namespace_accesses:
                print(f"  Namespace Access:")
                for ns, access in user.spec.access.namespace_accesses.items():
                    print(f"    - {ns}: {access.permission}")

            print()


def main():
    api_key = os.getenv("TEMPORAL_CLOUD_API_KEY")

    if not api_key:
        print("Error: TEMPORAL_CLOUD_API_KEY environment variable not set.")
        print("\nUsage:")
        print("  export TEMPORAL_CLOUD_API_KEY='your-api-key'")
        print("  python list_users.py [namespace]")
        sys.exit(1)

    namespace = sys.argv[1] if len(sys.argv) > 1 else None

    asyncio.run(list_users(api_key, namespace))


if __name__ == "__main__":
    main()
