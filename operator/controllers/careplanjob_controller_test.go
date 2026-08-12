package controllers

import (
	"context"
	"testing"

	batchv1 "k8s.io/api/batch/v1"
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/types"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client/fake"

	careplanv1alpha1 "careplan.example.io/operator/api/v1alpha1"
)

func newReconciler(t *testing.T, objs ...runtime.Object) (*CarePlanJobReconciler, context.Context) {
	t.Helper()
	scheme := runtime.NewScheme()
	if err := batchv1.AddToScheme(scheme); err != nil {
		t.Fatal(err)
	}
	if err := corev1.AddToScheme(scheme); err != nil {
		t.Fatal(err)
	}
	if err := careplanv1alpha1.AddToScheme(scheme); err != nil {
		t.Fatal(err)
	}

	builder := fake.NewClientBuilder().WithScheme(scheme).WithRuntimeObjects(objs...)
	builder.WithStatusSubresource(&careplanv1alpha1.CarePlanJob{})

	return &CarePlanJobReconciler{
		Client: builder.Build(),
		Scheme: scheme,
	}, context.Background()
}

func TestReconcileCreatesOneChildJob(t *testing.T) {
	parent := &careplanv1alpha1.CarePlanJob{
		ObjectMeta: metav1.ObjectMeta{Name: "careplan-abc", Namespace: "default"},
		Spec: careplanv1alpha1.CarePlanJobSpec{
			CarePlanID: "abc",
			Image:      "careplan:test",
		},
	}
	r, ctx := newReconciler(t, parent)

	if _, err := r.Reconcile(ctx, ctrl.Request{NamespacedName: types.NamespacedName{Name: parent.Name, Namespace: parent.Namespace}}); err != nil {
		t.Fatal(err)
	}

	var jobs batchv1.JobList
	if err := r.List(ctx, &jobs); err != nil {
		t.Fatal(err)
	}
	if len(jobs.Items) != 1 {
		t.Fatalf("expected one child job, got %d", len(jobs.Items))
	}
	if jobs.Items[0].Name != "careplan-abc-worker" {
		t.Fatalf("unexpected child job name: %s", jobs.Items[0].Name)
	}
	if jobs.Items[0].Spec.Template.Spec.Containers[0].Image != "careplan:test" {
		t.Fatalf("unexpected image: %s", jobs.Items[0].Spec.Template.Spec.Containers[0].Image)
	}
	if jobs.Items[0].Spec.Template.Spec.Containers[0].Command[2] != "generate_careplan_once" {
		t.Fatalf("unexpected command: %#v", jobs.Items[0].Spec.Template.Spec.Containers[0].Command)
	}

	var updated careplanv1alpha1.CarePlanJob
	if err := r.Get(ctx, types.NamespacedName{Name: parent.Name, Namespace: parent.Namespace}, &updated); err != nil {
		t.Fatal(err)
	}
	if updated.Status.JobName != "careplan-abc-worker" {
		t.Fatalf("unexpected job name in status: %s", updated.Status.JobName)
	}
}

func TestReconcileIsIdempotent(t *testing.T) {
	parent := &careplanv1alpha1.CarePlanJob{
		ObjectMeta: metav1.ObjectMeta{Name: "careplan-abc", Namespace: "default"},
		Spec: careplanv1alpha1.CarePlanJobSpec{
			CarePlanID: "abc",
			Image:      "careplan:test",
		},
	}
	r, ctx := newReconciler(t, parent)
	req := ctrl.Request{NamespacedName: types.NamespacedName{Name: parent.Name, Namespace: parent.Namespace}}

	if _, err := r.Reconcile(ctx, req); err != nil {
		t.Fatal(err)
	}
	if _, err := r.Reconcile(ctx, req); err != nil {
		t.Fatal(err)
	}

	var jobs batchv1.JobList
	if err := r.List(ctx, &jobs); err != nil {
		t.Fatal(err)
	}
	if len(jobs.Items) != 1 {
		t.Fatalf("expected one child job after repeated reconcile, got %d", len(jobs.Items))
	}
}

func TestReconcileSetsRunningStatus(t *testing.T) {
	parent := &careplanv1alpha1.CarePlanJob{
		ObjectMeta: metav1.ObjectMeta{Name: "careplan-abc", Namespace: "default"},
		Spec: careplanv1alpha1.CarePlanJobSpec{
			CarePlanID: "abc",
			Image:      "careplan:test",
		},
	}
	child := &batchv1.Job{
		ObjectMeta: metav1.ObjectMeta{Name: "careplan-abc-worker", Namespace: "default"},
		Status:     batchv1.JobStatus{Active: 1},
	}
	r, ctx := newReconciler(t, parent, child)

	if _, err := r.Reconcile(ctx, ctrl.Request{NamespacedName: types.NamespacedName{Name: parent.Name, Namespace: parent.Namespace}}); err != nil {
		t.Fatal(err)
	}

	var updated careplanv1alpha1.CarePlanJob
	if err := r.Get(ctx, types.NamespacedName{Name: parent.Name, Namespace: parent.Namespace}, &updated); err != nil {
		t.Fatal(err)
	}
	if updated.Status.Phase != careplanv1alpha1.CarePlanJobPhaseRunning {
		t.Fatalf("expected Running, got %s", updated.Status.Phase)
	}
}

func TestReconcileSetsSucceededStatus(t *testing.T) {
	parent := &careplanv1alpha1.CarePlanJob{
		ObjectMeta: metav1.ObjectMeta{Name: "careplan-abc", Namespace: "default"},
		Spec: careplanv1alpha1.CarePlanJobSpec{
			CarePlanID: "abc",
			Image:      "careplan:test",
		},
	}
	child := &batchv1.Job{
		ObjectMeta: metav1.ObjectMeta{Name: "careplan-abc-worker", Namespace: "default"},
		Status: batchv1.JobStatus{
			Conditions: []batchv1.JobCondition{{
				Type:   batchv1.JobComplete,
				Status: corev1.ConditionTrue,
			}},
		},
	}
	r, ctx := newReconciler(t, parent, child)

	if _, err := r.Reconcile(ctx, ctrl.Request{NamespacedName: types.NamespacedName{Name: parent.Name, Namespace: parent.Namespace}}); err != nil {
		t.Fatal(err)
	}

	var updated careplanv1alpha1.CarePlanJob
	if err := r.Get(ctx, types.NamespacedName{Name: parent.Name, Namespace: parent.Namespace}, &updated); err != nil {
		t.Fatal(err)
	}
	if updated.Status.Phase != careplanv1alpha1.CarePlanJobPhaseSucceeded {
		t.Fatalf("expected Succeeded, got %s", updated.Status.Phase)
	}
}

func TestReconcileSetsFailedStatus(t *testing.T) {
	parent := &careplanv1alpha1.CarePlanJob{
		ObjectMeta: metav1.ObjectMeta{Name: "careplan-abc", Namespace: "default"},
		Spec: careplanv1alpha1.CarePlanJobSpec{
			CarePlanID: "abc",
			Image:      "careplan:test",
		},
	}
	child := &batchv1.Job{
		ObjectMeta: metav1.ObjectMeta{Name: "careplan-abc-worker", Namespace: "default"},
		Status: batchv1.JobStatus{
			Conditions: []batchv1.JobCondition{{
				Type:    batchv1.JobFailed,
				Status:  corev1.ConditionTrue,
				Reason:  "BackoffLimitExceeded",
				Message: "job reached backoff limit",
			}},
		},
	}
	r, ctx := newReconciler(t, parent, child)

	if _, err := r.Reconcile(ctx, ctrl.Request{NamespacedName: types.NamespacedName{Name: parent.Name, Namespace: parent.Namespace}}); err != nil {
		t.Fatal(err)
	}

	var updated careplanv1alpha1.CarePlanJob
	if err := r.Get(ctx, types.NamespacedName{Name: parent.Name, Namespace: parent.Namespace}, &updated); err != nil {
		t.Fatal(err)
	}
	if updated.Status.Phase != careplanv1alpha1.CarePlanJobPhaseFailed {
		t.Fatalf("expected Failed, got %s", updated.Status.Phase)
	}
	if updated.Status.Message != "job reached backoff limit" {
		t.Fatalf("unexpected failure message: %s", updated.Status.Message)
	}
}

func TestReconcileMissingResourceReturnsNoError(t *testing.T) {
	r, ctx := newReconciler(t)
	if _, err := r.Reconcile(ctx, ctrl.Request{NamespacedName: types.NamespacedName{Name: "missing", Namespace: "default"}}); err != nil {
		t.Fatal(err)
	}
}
