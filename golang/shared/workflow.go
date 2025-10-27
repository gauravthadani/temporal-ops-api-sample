package shared

import (
	"time"

	"go.temporal.io/cloud-sdk/api/identity/v1"
	"go.temporal.io/sdk/temporal"
	"go.temporal.io/sdk/workflow"
)

func BreakglassRequestWorkflow(ctx workflow.Context, request BreakglassRequest) (*PrivilegeResponse, error) {
	ctx = workflow.WithActivityOptions(ctx, activityOpts)
	var result PrivilegeResponse
	err := workflow.ExecuteActivity(ctx,
		"ProcessPrivilegeRequest",
		NewPrivilegeRequest(request, identity.AccountAccess_ROLE_DEVELOPER)).Get(ctx, &result)
	if err != nil {
		return nil, err
	}

	err = workflow.Sleep(ctx, time.Minute*3)
	if err != nil {
		return nil, err
	}

	err = workflow.ExecuteActivity(ctx,
		"ProcessPrivilegeRequest",
		NewPrivilegeRequest(request, identity.AccountAccess_ROLE_READ)).Get(ctx, &result)
	if err != nil {
		return nil, err
	}

	return &result, nil
}

var activityOpts = workflow.ActivityOptions{
	StartToCloseTimeout: time.Minute,
	RetryPolicy: &temporal.RetryPolicy{
		InitialInterval:    5,
		BackoffCoefficient: 2,
		MaximumInterval:    10,
		MaximumAttempts:    2,
		NonRetryableErrorTypes: []string{
			"UserNotFoundError",
		},
	},
}
