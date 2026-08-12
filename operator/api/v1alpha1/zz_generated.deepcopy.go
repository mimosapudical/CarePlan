package v1alpha1

import (
	runtime "k8s.io/apimachinery/pkg/runtime"
)

func (in *CarePlanJob) DeepCopyInto(out *CarePlanJob) {
	*out = *in
	in.ObjectMeta.DeepCopyInto(&out.ObjectMeta)
}

func (in *CarePlanJob) DeepCopy() *CarePlanJob {
	if in == nil {
		return nil
	}
	out := new(CarePlanJob)
	in.DeepCopyInto(out)
	return out
}

func (in *CarePlanJob) DeepCopyObject() runtime.Object {
	if c := in.DeepCopy(); c != nil {
		return c
	}
	return nil
}

func (in *CarePlanJobList) DeepCopyInto(out *CarePlanJobList) {
	*out = *in
	if in.Items != nil {
		out.Items = make([]CarePlanJob, len(in.Items))
		for i := range in.Items {
			in.Items[i].DeepCopyInto(&out.Items[i])
		}
	}
	in.ListMeta.DeepCopyInto(&out.ListMeta)
}

func (in *CarePlanJobList) DeepCopy() *CarePlanJobList {
	if in == nil {
		return nil
	}
	out := new(CarePlanJobList)
	in.DeepCopyInto(out)
	return out
}

func (in *CarePlanJobList) DeepCopyObject() runtime.Object {
	if c := in.DeepCopy(); c != nil {
		return c
	}
	return nil
}

