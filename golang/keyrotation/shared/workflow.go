package shared

import (
	"time"

	"go.temporal.io/sdk/temporal"
	"go.temporal.io/sdk/workflow"
)

// Continue-as-new after this many rotations to keep the event history small.
const maxRotationsPerRun = 100

func KeyRotationWorkflow(ctx workflow.Context, request KeyRotationRequest) error {
	ctx = workflow.WithActivityOptions(ctx, activityOpts)

	for i := 0; i < maxRotationsPerRun; i++ {
		var result CreateApiKeyResponse
		err := workflow.ExecuteActivity(ctx,
			"CreateApiKey",
			CreateApiKeyRequest{OwnerID: request.OwnerID, KeyTTL: request.KeyTTL}).Get(ctx, &result)
		if err != nil {
			return err
		}
		workflow.GetLogger(ctx).Info("Rotated API key", "KeyID", result.KeyID, "ExpiresAt", result.ExpiresAt)

		err = workflow.Sleep(ctx, request.Interval)
		if err != nil {
			return err
		}
	}

	return workflow.NewContinueAsNewError(ctx, KeyRotationWorkflow, request)
}

// HelloWorkflow is a trivial workflow to show the worker keeps working across key rotations.
func HelloWorkflow(ctx workflow.Context, name string) (string, error) {
	return "Hello " + name, nil
}

var activityOpts = workflow.ActivityOptions{
	StartToCloseTimeout: time.Minute,
	RetryPolicy: &temporal.RetryPolicy{
		InitialInterval:    5 * time.Second,
		BackoffCoefficient: 2,
		MaximumInterval:    time.Minute,
		MaximumAttempts:    5,
	},
}
