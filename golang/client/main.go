package main

import (
	"context"
	"log"
	"os"

	"go.temporal.io/sdk/client"

	"ops-lifecycle/shared"
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

	workflowOptions := client.StartWorkflowOptions{
		ID:        "privilege-request-workflow-1",
		TaskQueue: "privilege-request-queue",
	}

	request := shared.BreakglassRequest{
		UserID:        "",
		RequestedBy:   "",
		Justification: "Why not",
		EmailID:       "",
	}

	we, err := c.ExecuteWorkflow(context.Background(), workflowOptions, shared.BreakglassRequestWorkflow, request)
	if err != nil {
		log.Fatalln("Unable to execute workflow", err)
	}

	log.Println("Started workflow", "WorkflowID", we.GetID(), "RunID", we.GetRunID())

	var result shared.PrivilegeResponse
	err = we.Get(context.Background(), &result)
	if err != nil {
		log.Fatalln("Unable to get workflow result", err)
	}

	log.Printf("Workflow completed with result: %v", result)
}
