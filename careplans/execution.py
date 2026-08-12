from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Protocol

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)

CAREPLAN_JOB_GROUP = "careplan.example.io"
CAREPLAN_JOB_VERSION = "v1alpha1"
CAREPLAN_JOB_PLURAL = "careplanjobs"
CAREPLAN_JOB_KIND = "CarePlanJob"


class ExecutionBackend(Protocol):
    def submit(self, careplan_id: str) -> None:
        ...


def get_execution_backend() -> ExecutionBackend:
    backend_name = getattr(settings, "CAREPLAN_EXECUTION_BACKEND", "celery").strip().lower()

    if backend_name == "celery":
        return CeleryExecutionBackend()

    if backend_name == "kubernetes":
        return KubernetesExecutionBackend()

    raise ImproperlyConfigured(
        f"Unknown CAREPLAN_EXECUTION_BACKEND value: {backend_name!r}. Expected 'celery' or 'kubernetes'."
    )


class CeleryExecutionBackend:
    def submit(self, careplan_id: str) -> None:
        from .tasks import generate_care_plan_task

        generate_care_plan_task.delay(careplan_id)


def _load_kubernetes_modules():
    from kubernetes import client, config
    from kubernetes.client.rest import ApiException

    return client, config, ApiException


def careplan_job_name(careplan_id: str) -> str:
    safe_id = str(careplan_id).strip().lower().replace("-", "")
    return f"careplan-{safe_id}"


@dataclass
class KubernetesExecutionBackend:
    namespace: str | None = None
    image: str | None = None
    backoff_limit: int | None = None

    def __post_init__(self) -> None:
        self.namespace = self.namespace or getattr(settings, "CAREPLAN_K8S_NAMESPACE", "default")
        self.image = self.image or getattr(settings, "CAREPLAN_K8S_IMAGE", "").strip()
        self.backoff_limit = self.backoff_limit or int(getattr(settings, "CAREPLAN_K8S_BACKOFF_LIMIT", 3))

        if not self.image:
            raise ImproperlyConfigured(
                "CAREPLAN_K8S_IMAGE must be set when CAREPLAN_EXECUTION_BACKEND=kubernetes"
            )

    def submit(self, careplan_id: str) -> None:
        client, config, ApiException = _load_kubernetes_modules()

        if os.environ.get("KUBERNETES_SERVICE_HOST"):
            config.load_incluster_config()
        else:
            config.load_kube_config()

        api = client.CustomObjectsApi()
        resource_name = careplan_job_name(careplan_id)
        body = {
            "apiVersion": f"{CAREPLAN_JOB_GROUP}/{CAREPLAN_JOB_VERSION}",
            "kind": CAREPLAN_JOB_KIND,
            "metadata": {"name": resource_name},
            "spec": {
                "carePlanId": str(careplan_id),
                "image": self.image,
                "backoffLimit": self.backoff_limit,
            },
        }

        try:
            api.create_namespaced_custom_object(
                group=CAREPLAN_JOB_GROUP,
                version=CAREPLAN_JOB_VERSION,
                namespace=self.namespace,
                plural=CAREPLAN_JOB_PLURAL,
                body=body,
            )
        except ApiException as exc:
            if getattr(exc, "status", None) == 409:
                logger.info(
                    "KubernetesExecutionBackend: CarePlanJob already exists careplan_id=%s name=%s",
                    careplan_id,
                    resource_name,
                )
                return
            raise

