#!/usr/bin/env python3
"""
Simple script to list users from Temporal Cloud using the Cloud API.
"""

import os
import sys
import grpc
# from temporal.api.cloud.cloudservice.v1 import service_pb2_grpc, request_response_pb2
from temporalio.api.cloud.cloudservice.v1 import service_pb2_grpc, request_response_pb2


def list_users(api_key: str, namespace: str = None, page_size: int = 10):
    """
    List users from Temporal Cloud.

    Args:
        api_key: Temporal Cloud API key
        namespace: Optional namespace to filter users
        page_size: Number of users per page (default: 10)
    """
    # Temporal Cloud gRPC endpoint
    cloud_endpoint = "saas-api.tmprl.cloud:443"

    # Create credentials with API key
    call_credentials = grpc.access_token_call_credentials(api_key)
    channel_credentials = grpc.ssl_channel_credentials()
    composite_credentials = grpc.composite_channel_credentials(
        channel_credentials, call_credentials
    )

    # Create gRPC channel
    channel = grpc.secure_channel(cloud_endpoint, composite_credentials)

    # Create service stub
    client = service_pb2_grpc.CloudServiceStub(channel)

    try:
        # Create GetUsers request
        request = request_response_pb2.GetUsersRequest(
            page_size=page_size
        )

        # Add namespace filter if provided
        if namespace:
            request.namespace = namespace

        # Make the API call
        print(f"Fetching users from Temporal Cloud...")
        if namespace:
            print(f"Filtering by namespace: {namespace}")
        print()

        # Add API version metadata
        metadata = [("temporal-cloud-api-version", "2024-05-13-00")]
        response = client.GetUsers(request, metadata=metadata)

        # Display results
        if not response.users:
            print("No users found.")
        else:
            print(f"Found {len(response.users)} user(s):\n")
            for user in response.users:
                print(f"User ID: {user.id}")
                print(f"  Email: {user.spec.email}")
                print(f"  State: {user.state}")
                print(f"  Resource Version: {user.resource_version}")

                # Display account access if available
                if user.spec.access and user.spec.access.account_access:
                    print(f"  Account Role: {user.spec.access.account_access.role}")

                # Display namespace accesses if available
                if user.spec.access and user.spec.access.namespace_accesses:
                    print(f"  Namespace Access:")
                    for ns, access in user.spec.access.namespace_accesses.items():
                        print(f"    - {ns}: {access.permission}")

                print()

            # Display pagination info
            if response.next_page_token:
                print(f"More users available. Next page token: {response.next_page_token}")

    except grpc.RpcError as e:
        print(f"Error calling Temporal Cloud API: {e.code()}")
        print(f"Details: {e.details()}")
        sys.exit(1)

    finally:
        channel.close()


def main():
    """Main entry point."""
    # Get API key from environment variable
    api_key = os.getenv("TEMPORAL_CLOUD_API_KEY")

    if not api_key:
        print("Error: TEMPORAL_CLOUD_API_KEY environment variable not set.")
        print("\nUsage:")
        print("  export TEMPORAL_CLOUD_API_KEY='your-api-key'")
        print("  python list_users.py [namespace]")
        sys.exit(1)

    # Get optional namespace from command line
    namespace = sys.argv[1] if len(sys.argv) > 1 else None

    # List users
    list_users(api_key, namespace)


if __name__ == "__main__":
    main()
