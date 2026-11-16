package shared

import (
	"context"
	"time"

	"go.temporal.io/cloud-sdk/api/cloudservice/v1"
	"go.temporal.io/cloud-sdk/api/identity/v1"
	"google.golang.org/protobuf/types/known/timestamppb"
)

type CloudOps struct {
	cloudServiceClient cloudservice.CloudServiceClient
	secretStore        *SecretStore
}

func NewCloudOps(client cloudservice.CloudServiceClient, store *SecretStore) *CloudOps {
	return &CloudOps{
		cloudServiceClient: client,
		secretStore:        store,
	}
}

func (ops *CloudOps) CreateApiKey(ctx context.Context, request CreateApiKeyRequest) (*CreateApiKeyResponse, error) {
	expiresAt := time.Now().Add(request.KeyTTL)
	resp, err := ops.cloudServiceClient.CreateApiKey(ctx, mapApiKey(request, expiresAt))
	if err != nil {
		return nil, err
	}

	err = ops.secretStore.Put(Secret{
		KeyID:     resp.GetKeyId(),
		Token:     resp.GetToken(),
		CreatedAt: time.Now(),
		ExpiresAt: expiresAt,
	})
	if err != nil {
		return nil, err
	}
	return &CreateApiKeyResponse{KeyID: resp.GetKeyId(), ExpiresAt: expiresAt}, nil
}

func mapApiKey(request CreateApiKeyRequest, expiresAt time.Time) *cloudservice.CreateApiKeyRequest {
	return &cloudservice.CreateApiKeyRequest{
		Spec: &identity.ApiKeySpec{
			OwnerId:     request.OwnerID,
			OwnerType:   identity.OwnerType_OWNER_TYPE_SERVICE_ACCOUNT,
			DisplayName: "rotated-" + expiresAt.UTC().Format("20060102-150405"),
			ExpiryTime:  timestamppb.New(expiresAt),
		},
	}
}
