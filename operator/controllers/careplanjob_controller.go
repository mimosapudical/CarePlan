package controllers

import (
	"context"
	"fmt"
	"reflect"

	batchv1 "k8s.io/api/batch/v1"
	corev1 "k8s.io/api/core/v1"
	apierrors "k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/types"
	"k8s.io/apimachinery/pkg/runtime"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/controller/controllerutil"

	careplanv1alpha1 "careplan.example.io/operator/api/v1alpha1"
)

type CarePlanJobReconciler struct {
	client.Client
	Scheme *runtime.Scheme
}

func (r *CarePlanJobReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
	var carePlanJob careplanv1alpha1.CarePlanJob
	if err := r.Get(ctx, req.NamespacedName, &carePlanJob); err != nil {
		return ctrl.Result{}, client.IgnoreNotFound(err)
	}

	childName := childJobName(carePlanJob.Name)

	var child batchv1.Job
	err := r.Get(ctx, types.NamespacedName{Name: childName, Namespace: carePlanJob.Namespace}, &child)
	if err != nil {
		if !apierrors.IsNotFound(err) {
			return ctrl.Result{}, err
		}
		if isTerminalPhase(carePlanJob.Status.Phase) {
			return ctrl.Result{}, nil
		}
		if err := r.createChildJob(ctx, &carePlanJob, childName); err != nil {
			return ctrl.Result{}, err
		}
		return ctrl.Result{}, r.updateStatus(ctx, &carePlanJob, careplanv1alpha1.CarePlanJobStatus{
			Phase:   careplanv1alpha1.CarePlanJobPhasePending,
			JobName: childName,
		})
	}

	desired := desiredStatusFromJob(&child, childName)
	return ctrl.Result{}, r.updateStatus(ctx, &carePlanJob, desired)
}

func (r *CarePlanJobReconciler) createChildJob(ctx context.Context, carePlanJob *careplanv1alpha1.CarePlanJob, childName string) error {
	backoff := int32(3)
	if carePlanJob.Spec.BackoffLimit != nil {
		backoff = *carePlanJob.Spec.BackoffLimit
	}

	child := batchv1.Job{
		ObjectMeta: metav1.ObjectMeta{
			Name:      childName,
			Namespace: carePlanJob.Namespace,
		},
		Spec: batchv1.JobSpec{
			BackoffLimit: &backoff,
			Template: corev1.PodTemplateSpec{
				Spec: corev1.PodSpec{
					RestartPolicy: corev1.RestartPolicyNever,
					Containers: []corev1.Container{
						{
							Name:            "careplan-worker",
							Image:           carePlanJob.Spec.Image,
							ImagePullPolicy: corev1.PullIfNotPresent,
							Command: []string{
								"python",
								"manage.py",
								"generate_careplan_once",
								carePlanJob.Spec.CarePlanID,
							},
						},
					},
				},
			},
		},
	}

	if err := controllerutil.SetControllerReference(carePlanJob, &child, r.Scheme); err != nil {
		return err
	}
	if err := r.Create(ctx, &child); err != nil {
		if apierrors.IsAlreadyExists(err) {
			return nil
		}
		return err
	}
	return nil
}

func (r *CarePlanJobReconciler) updateStatus(ctx context.Context, carePlanJob *careplanv1alpha1.CarePlanJob, desired careplanv1alpha1.CarePlanJobStatus) error {
	if reflect.DeepEqual(carePlanJob.Status, desired) {
		return nil
	}
	latest := carePlanJob.DeepCopy()
	latest.Status = desired
	return r.Status().Update(ctx, latest)
}

func childJobName(name string) string {
	return fmt.Sprintf("%s-worker", name)
}

func isTerminalPhase(phase careplanv1alpha1.CarePlanJobPhase) bool {
	return phase == careplanv1alpha1.CarePlanJobPhaseSucceeded || phase == careplanv1alpha1.CarePlanJobPhaseFailed
}

func desiredStatusFromJob(job *batchv1.Job, childName string) careplanv1alpha1.CarePlanJobStatus {
	status := careplanv1alpha1.CarePlanJobStatus{JobName: childName, Phase: careplanv1alpha1.CarePlanJobPhasePending}

	for _, condition := range job.Status.Conditions {
		switch condition.Type {
		case batchv1.JobComplete:
			if condition.Status == corev1.ConditionTrue {
				status.Phase = careplanv1alpha1.CarePlanJobPhaseSucceeded
				return status
			}
		case batchv1.JobFailed:
			if condition.Status == corev1.ConditionTrue {
				status.Phase = careplanv1alpha1.CarePlanJobPhaseFailed
				if condition.Message != "" {
					status.Message = condition.Message
				} else if condition.Reason != "" {
					status.Message = condition.Reason
				} else {
					status.Message = "Job failed"
				}
				return status
			}
		}
	}

	if job.Status.Active > 0 {
		status.Phase = careplanv1alpha1.CarePlanJobPhaseRunning
	}
	return status
}

func (r *CarePlanJobReconciler) SetupWithManager(mgr ctrl.Manager) error {
	return ctrl.NewControllerManagedBy(mgr).
		For(&careplanv1alpha1.CarePlanJob{}).
		Owns(&batchv1.Job{}).
		Complete(r)
}
