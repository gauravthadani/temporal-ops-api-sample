package main

import (
	"context"
	"crypto/tls"
	"flag"
	"log"
	"time"

	"go.temporal.io/api/enums/v1"
	"go.temporal.io/sdk/client"

	"key-rotation/shared"
)

func main() {
	targetHost := flag.String("target-host", "localhost:7233", "Host:port for the server")
	namespace := flag.String("namespace", "default", "Namespace for the server")
	flag.Parse()

	// Use the latest key from the secret store (seeded by the worker on first run).
	secret, err := shared.NewSecretStore().GetLatest()
	if err != nil {
		log.Fatalln("Unable to read API key from secret store. Start the worker first.", err)
	}

	c, err := client.Dial(client.Options{
		HostPort:          *targetHost,
		Namespace:         *namespace,
		ConnectionOptions: client.ConnectionOptions{TLS: &tls.Config{}},
		Credentials:       client.NewAPIKeyStaticCredentials(secret.Token),
	})
	if err != nil {
		log.Fatalln("Unable to create client", err)
	}
	defer c.Close()

	workflowOptions := client.StartWorkflowOptions{
		ID:                       "key-rotation-workflow",
		TaskQueue:                "key-rotation-queue",
		WorkflowIDConflictPolicy: enums.WORKFLOW_ID_CONFLICT_POLICY_USE_EXISTING,
	}

	request := shared.KeyRotationRequest{
		OwnerID:  "test-ns-key-rotator", // ID of the worker's own namespace-scoped service account
		Interval: 5 * time.Minute,
		KeyTTL:   25 * time.Hour, // Temporal Cloud requires API keys to expire more than 24h from now
	}

	we, err := c.ExecuteWorkflow(context.Background(), workflowOptions, shared.KeyRotationWorkflow, request)
	if err != nil {
		log.Fatalln("Unable to execute workflow", err)
	}

	// The workflow runs until terminated, so don't wait for a result.
	log.Println("Started workflow", "WorkflowID", we.GetID(), "RunID", we.GetRunID())
}
