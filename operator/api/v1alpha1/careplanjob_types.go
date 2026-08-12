package v1alpha1

import (
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// +kubebuilder:validation:Enum=Pending;Running;Succeeded;Failed
type CarePlanJobPhase string

const (
	CarePlanJobPhasePending   CarePlanJobPhase = "Pending"
	CarePlanJobPhaseRunning   CarePlanJobPhase = "Running"
	CarePlanJobPhaseSucceeded CarePlanJobPhase = "Succeeded"
	CarePlanJobPhaseFailed    CarePlanJobPhase = "Failed"
)

// CarePlanJobSpec defines the desired state of CarePlanJob.
type CarePlanJobSpec struct {
	// +kubebuilder:validation:MinLength=1
	CarePlanID string `json:"carePlanId"`

	// +kubebuilder:validation:MinLength=1
	Image string `json:"image"`

	// +kubebuilder:validation:Minimum=1
	BackoffLimit *int32 `json:"backoffLimit,omitempty"`
}

// CarePlanJobStatus defines the observed state of CarePlanJob.
type CarePlanJobStatus struct {
	Phase   CarePlanJobPhase `json:"phase,omitempty"`
	JobName string           `json:"jobName,omitempty"`
	Message string           `json:"message,omitempty"`
}

// +kubebuilder:object:root=true
// +kubebuilder:subresource:status
// +kubebuilder:resource:path=careplanjobs,scope=Namespaced
type CarePlanJob struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec   CarePlanJobSpec   `json:"spec,omitempty"`
	Status CarePlanJobStatus `json:"status,omitempty"`
}

// +kubebuilder:object:root=true
type CarePlanJobList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty"`
	Items           []CarePlanJob `json:"items"`
}

func init() {
	SchemeBuilder.Register(&CarePlanJob{}, &CarePlanJobList{})
}
