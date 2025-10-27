package shared

import (
	"errors"
	
	"go.temporal.io/cloud-sdk/api/identity/v1"
)

type BreakglassRequest struct {
	UserID        string `json:"user_id"`
	RequestedBy   string `json:"requested_by"`
	Justification string `json:"justification"`
	Duration      string `json:"duration"`
	EmailID       string `json:"email_id"`
}

type PrivilegeRequest struct {
	BreakglassRequest
	AccountAccessRole identity.AccountAccess_Role `json:"account_access_role"`
}

func NewPrivilegeRequest(request BreakglassRequest, role identity.AccountAccess_Role) *PrivilegeRequest {
	return &PrivilegeRequest{
		BreakglassRequest: request,
		AccountAccessRole: role,
	}
}

type PrivilegeResponse struct {
}

var UserNotFoundError = errors.New("user not found")
