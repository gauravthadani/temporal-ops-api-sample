package shared

import (
	"crypto/tls"
	"flag"
	"fmt"
	"log"
	"os"
	"strings"
	
	"go.temporal.io/sdk/client"
)

func ParseClientOptionFlags(args []string) (client.Options, error) {
	set := flag.NewFlagSet("hello-world-api-key", flag.ExitOnError)
	targetHost := set.String("target-host", "localhost:7233", "Host:port for the server")
	namespace := set.String("namespace", "default", "Namespace for the server")
	apiKey := set.String("api-key", "", "Optional API key, mutually exclusive with cert/key")

	if err := set.Parse(args); err != nil {
		return client.Options{}, fmt.Errorf("failed parsing args: %w", err)
	}

	if *apiKey == "" {
		*apiKey = os.Getenv("TEMPORAL_CLIENT_API_KEY")
	}
	if *apiKey == "" {
		*apiKey = ReadApiKey()
	}
	if *apiKey == "" {
		return client.Options{}, fmt.Errorf("-api-key or TEMPORAL_CLIENT_API_KEY env is required required")
	}

	return client.Options{
		HostPort:          *targetHost,
		Namespace:         *namespace,
		ConnectionOptions: client.ConnectionOptions{TLS: &tls.Config{}},
		Credentials:       client.NewAPIKeyStaticCredentials(*apiKey),
	}, nil
}

func ReadApiKey() string {
	name := "api_key"
	apiKeyBytes, err := os.ReadFile(name)
	if err != nil {
		log.Fatalln("Unable to read API key file:", err)
	}
	return strings.TrimSpace(string(apiKeyBytes))
}
