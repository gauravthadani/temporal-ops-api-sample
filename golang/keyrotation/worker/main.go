package main

import (
	"context"
	"crypto/tls"
	"errors"
	"flag"
	"log"
	"os"
	"strings"
	"sync/atomic"
	"time"

	"key-rotation/shared"

	"go.temporal.io/cloud-sdk/cloudclient"
	"go.temporal.io/sdk/client"
	"go.temporal.io/sdk/worker"
)

// How often to pick up the latest API key from the secret store.
const refreshInterval = 5 * time.Minute

// New API keys can take up to about a minute before Temporal Cloud accepts them.
const propagationDelay = time.Minute

func main() {
	targetHost := flag.String("target-host", "localhost:7233", "Host:port for the server")
	namespace := flag.String("namespace", "default", "Namespace for the server")
	flag.Parse()

	store := shared.NewSecretStore()

	// First run only: seed the secret store with the bootstrap key from the api_key file.
	// After that the worker only uses keys created by the KeyRotationWorkflow.
	_, err := store.GetLatest()
	if errors.Is(err, shared.SecretNotFoundError) {
		apiKeyBytes, err := os.ReadFile("api_key")
		if err != nil {
			log.Fatalln("Unable to read API key file:", err)
		}
		err = store.Put(shared.Secret{KeyID: "seed", Token: strings.TrimSpace(string(apiKeyBytes))})
		if err != nil {
			log.Fatalln("Unable to seed secret store:", err)
		}
	}

	var currentKey atomic.Value // API key token (string)

	refreshKey := func() {
		secret, err := store.GetLatest()
		if err != nil {
			log.Println("Unable to refresh API key, keeping current one:", err)
			return
		}
		// Give a brand-new key time to propagate before switching to it.
		if wait := propagationDelay - time.Since(secret.CreatedAt); wait > 0 {
			time.Sleep(wait)
		}
		currentKey.Store(secret.Token)
		log.Println("Using API key", "KeyID", secret.KeyID, "ExpiresAt", secret.ExpiresAt)
	}

	refreshKey()
	go func() {
		for range time.Tick(refreshInterval) {
			refreshKey()
		}
	}()

	// Both clients look up the key on every request, so they just return the key held in memory.
	getApiKey := func(context.Context) (string, error) {
		return currentKey.Load().(string), nil
	}

	c, err := client.Dial(client.Options{
		HostPort:          *targetHost,
		Namespace:         *namespace,
		ConnectionOptions: client.ConnectionOptions{TLS: &tls.Config{}},
		Credentials:       client.NewAPIKeyDynamicCredentials(getApiKey),
	})
	if err != nil {
		log.Fatalln("Unable to create client", err)
	}
	defer c.Close()

	cloudClient, err := cloudclient.New(cloudclient.Options{
		APIKeyReader: apiKeyReader(getApiKey),
	})
	if err != nil {
		log.Fatalln("Unable to create cloud client", err)
	}
	defer func(cloudClient *cloudclient.Client) {
		err = cloudClient.Close()
		if err != nil {
			panic(err)
		}
	}(cloudClient)

	// Create worker listening on the task queue
	w := worker.New(c, "key-rotation-queue", worker.Options{})

	w.RegisterWorkflow(shared.KeyRotationWorkflow)
	w.RegisterWorkflow(shared.HelloWorkflow)
	w.RegisterActivity(shared.NewCloudOps(cloudClient.CloudService(), store))

	err = w.Run(worker.InterruptCh())
	if err != nil {
		log.Fatalln("Unable to start Worker", err)
	}
}

// apiKeyReader adapts a function to the cloudclient.APIKeyReader interface.
type apiKeyReader func(context.Context) (string, error)

func (f apiKeyReader) GetAPIKey(ctx context.Context) (string, error) { return f(ctx) }
