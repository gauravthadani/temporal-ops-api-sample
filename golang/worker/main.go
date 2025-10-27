package main

import (
	"fmt"
	"log"
	"os"

	"ops-lifecycle/shared"

	"go.temporal.io/cloud-sdk/cloudclient"
	"go.temporal.io/sdk/client"
	"go.temporal.io/sdk/worker"
)

func main() {
	clientOptions, err := shared.ParseClientOptionFlags(os.Args[1:])
	if err != nil {
		log.Fatalf("Invalid arguments: %v", err)
	}
	c, err := client.Dial(clientOptions)
	if err != nil {
		log.Fatalln("Unable to create client", err)
	}
	defer c.Close()

	// Create worker listening on the task queue
	w := worker.New(c, "privilege-request-queue", worker.Options{})

	cloudClient, err := NewConnectionWithAPIKey(shared.ReadApiKey())
	if err != nil {
		panic(err)
	}
	defer func(cloudClient *cloudclient.Client) {
		err = cloudClient.Close()
		if err != nil {
			panic(err)
		}
	}(cloudClient)

	w.RegisterWorkflow(shared.BreakglassRequestWorkflow)
	w.RegisterActivity(shared.NewCloudOps(cloudClient.CloudService()))

	err = w.Run(worker.InterruptCh())
	if err != nil {
		log.Fatalln("Unable to start Worker", err)
	}
}

func NewConnectionWithAPIKey(apikey string) (*cloudclient.Client, error) {
	cClient, err := cloudclient.New(cloudclient.Options{
		APIKey: apikey,
	})
	if err != nil {
		return nil, fmt.Errorf("failed to connect : %v", err)
	}
	return cClient, nil
}
