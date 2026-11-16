package shared

import (
	"encoding/json"
	"errors"
	"os"
)

// SecretStore is a mock external secret store (e.g. Vault, AWS Secrets Manager).
// It keeps the latest API key in a local JSON file.
type SecretStore struct {
	path string
}

func NewSecretStore() *SecretStore {
	return &SecretStore{
		path: "secret_store.json",
	}
}

func (s *SecretStore) Put(secret Secret) error {
	data, err := json.MarshalIndent(secret, "", "  ")
	if err != nil {
		return err
	}
	// Write to a temp file then rename, so readers never see a half-written file.
	err = os.WriteFile(s.path+".tmp", data, 0o600)
	if err != nil {
		return err
	}
	return os.Rename(s.path+".tmp", s.path)
}

func (s *SecretStore) GetLatest() (*Secret, error) {
	data, err := os.ReadFile(s.path)
	if errors.Is(err, os.ErrNotExist) {
		return nil, SecretNotFoundError
	}
	if err != nil {
		return nil, err
	}
	var secret Secret
	err = json.Unmarshal(data, &secret)
	if err != nil {
		return nil, err
	}
	return &secret, nil
}
