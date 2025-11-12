#!/usr/bin/env python3
"""
Simple script to list users from Temporal Cloud using the Cloud API.
"""

import os
import sys
import grpc
# from temporal.api.cloud.cloudservice.v1 import service_pb2_grpc, request_response_pb2
from temporalio.api.cloud.cloudservice.v1 import service_pb2_grpc, request_response_pb2


def list_user_group_members(api_key: str, namespace: str = None, page_size: int = 10):
    """
    List user group members from Temporal Cloud.

    Args:
        api_key: Temporal Cloud API key
        namespace: Optional namespace to filter users
        page_size: Number of users per page (default: 10)
    """
    # Temporal Cloud gRPC endpoint
    cloud_endpoint = "saas-api.tmprl.cloud:443"

    # Create credentials with API key
    call_credentials = grpc.access_token_call_credentials(api_key)
    # Disable TLS verification
    channel_credentials = grpc.ssl_channel_credentials(
        root_certificates=None,
        private_key=None,
        certificate_chain=None
    )
    channel_options = [
        ('grpc.ssl_target_name_override', 'saas-api.tmprl.cloud'),
        ('grpc.default_authority', 'saas-api.tmprl.cloud'),
    ]
    composite_credentials = grpc.composite_channel_credentials(
        channel_credentials, call_credentials
    )

    # Create gRPC channel with TLS verification disabled
    channel = grpc.secure_channel(cloud_endpoint, composite_credentials, options=channel_options)

    # Create service stub
    client = service_pb2_grpc.CloudServiceStub(channel)
    try:

        result = get_user_group_members(client, request_response_pb2.GetUserGroupMembersRequest(
            page_size=page_size,
            group_id="<GROUPID>",
        ))

        print(result)

    except grpc.RpcError as e:
        print(f"Error calling Temporal Cloud API: {e.code()}")
        print(f"Details: {e.details()}")
        sys.exit(1)

    finally:
        channel.close()


def get_user_group_members(client, request):
    metadata = [("temporal-cloud-api-version", "2024-05-13-00")]
    return client.GetUserGroupMembers(request, metadata=metadata)

def get_user_groups(client, request):
    metadata = [("temporal-cloud-api-version", "2024-05-13-00")]
    return client.GetUserGroups(request, metadata=metadata)

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
    list_user_group_members(api_key, namespace)


if __name__ == "__main__":
    main()
