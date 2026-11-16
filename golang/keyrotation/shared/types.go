package shared

import (
	"errors"
	"time"
)

type KeyRotationRequest struct {
	OwnerID  string        `json:"owner_id"`
	Interval time.Duration `json:"interval"`
	KeyTTL   time.Duration `json:"key_ttl"`
}

type CreateApiKeyRequest struct {
	OwnerID string        `json:"owner_id"`
	KeyTTL  time.Duration `json:"key_ttl"`
}

// CreateApiKeyResponse intentionally omits the token so it never lands in workflow history.
type CreateApiKeyResponse struct {
	KeyID     string    `json:"key_id"`
	ExpiresAt time.Time `json:"expires_at"`
}

type Secret struct {
	KeyID     string    `json:"key_id"`
	Token     string    `json:"token"`
	CreatedAt time.Time `json:"created_at"`
	ExpiresAt time.Time `json:"expires_at"`
}

var SecretNotFoundError = errors.New("secret not found")
