package main

import (
	"context"
	"fmt"
	"log"
	"os"

	"go.temporal.io/cloud-sdk/api/cloudservice/v1"
	"go.temporal.io/cloud-sdk/cloudclient"
)

func main() {

	key := os.Getenv("TEMPORAL_CLOUD_API_KEY")
	if key == "" {
		log.Fatal("TEMPORAL_CLOUD_API_KEY environment variable is required")
	}
	cloudClient, err := NewConnectionWithAPIKey(key)
	if err != nil {
		panic(err)
	}
	defer func(cloudClient *cloudclient.Client) {
		err = cloudClient.Close()
		if err != nil {
			panic(err)
		}
	}(cloudClient)

	users, err := cloudClient.CloudService().GetUserGroupMembers(context.Background(), &cloudservice.GetUserGroupMembersRequest{
		GroupId: "ad0421bb2f084882ad0483c5ecc120f8",
		//GroupId: "674c842bf5ef43529df52cd9f2a9eb12",
	})
	if err != nil {
		fmt.Println(err)
		panic(err)
	}
	fmt.Println("Users:", users)
	for _, user := range users.Members {
		fmt.Println(user.String())
	}
}

func NewConnectionWithAPIKey(apikey string) (*cloudclient.Client, error) {
	cClient, err := cloudclient.New(cloudclient.Options{
		APIKey:     apikey,
		APIVersion: "v0.8.0",
	})
	if err != nil {
		return nil, fmt.Errorf("failed to connect : %v", err)
	}
	return cClient, nil
}
