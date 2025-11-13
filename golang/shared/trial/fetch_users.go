package main

import (
	"context"
	"fmt"

	"go.temporal.io/cloud-sdk/api/cloudservice/v1"
	"go.temporal.io/cloud-sdk/cloudclient"
	"ops-lifecycle/shared"
)

func main() {
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

	users, err := cloudClient.CloudService().GetUserGroupMembers(context.Background(), &cloudservice.GetUserGroupMembersRequest{
		PageToken: "",
		GroupId:   "",
	})
	if err != nil {
		panic(err)
	}
	for _, user := range users.Members {
		fmt.Println(user)
	}
}

func NewConnectionWithAPIKey(apikey string) (*cloudclient.Client, error) {
	cClient, err := cloudclient.New(cloudclient.Options{
		APIKey:          apikey,
		APIKeyReader:    nil,
		HostPort:        "",
		AllowInsecure:   false,
		TLSConfig:       nil,
		APIVersion:      "",
		DisableRetry:    false,
		UserAgent:       "",
		GRPCDialOptions: nil,
	})
	if err != nil {
		return nil, fmt.Errorf("failed to connect : %v", err)
	}
	return cClient, nil
}
