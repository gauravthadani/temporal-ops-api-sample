package shared

import (
	"context"
	"go.temporal.io/cloud-sdk/api/cloudservice/v1"
	"go.temporal.io/cloud-sdk/api/identity/v1"
)

type CloudOps struct {
	cloudServiceClient cloudservice.CloudServiceClient
}

func NewCloudOps(client cloudservice.CloudServiceClient) *CloudOps {
	return &CloudOps{
		cloudServiceClient: client,
	}
}

func (ops *CloudOps) ProcessPrivilegeRequest(ctx context.Context, request PrivilegeRequest) (*PrivilegeResponse, error) {
	user, err := ops.cloudServiceClient.GetUser(ctx, &cloudservice.GetUserRequest{
		UserId: request.UserID,
	})
	if err != nil {
		return nil, err
	}
	if user == nil {
		return nil, UserNotFoundError
	}

	_, err = ops.cloudServiceClient.UpdateUser(ctx, mapUser(request, user))
	if err != nil {
		return &PrivilegeResponse{}, err
	}
	return &PrivilegeResponse{}, nil
}

func mapUser(request PrivilegeRequest, user *cloudservice.GetUserResponse) *cloudservice.UpdateUserRequest {
	return &cloudservice.UpdateUserRequest{
		UserId: request.UserID,
		Spec: &identity.UserSpec{
			Email: request.EmailID,
			Access: &identity.Access{
				NamespaceAccesses: user.GetUser().Spec.Access.NamespaceAccesses,
				AccountAccess: &identity.AccountAccess{
					Role: request.AccountAccessRole,
				},
			},
		},
		ResourceVersion: user.GetUser().GetResourceVersion(),
	}
}
