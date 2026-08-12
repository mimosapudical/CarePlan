from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from careplans.execution import (
    CeleryExecutionBackend,
    KubernetesExecutionBackend,
    careplan_job_name,
    get_execution_backend,
)

pytestmark = pytest.mark.unit


def test_default_backend_is_celery():
    backend = get_execution_backend()
    assert isinstance(backend, CeleryExecutionBackend)


def test_invalid_backend_raises_clear_error():
    with override_settings(CAREPLAN_EXECUTION_BACKEND="something-else"):
        with pytest.raises(ImproperlyConfigured):
            get_execution_backend()


def test_celery_backend_submit_calls_task_delay():
    backend = CeleryExecutionBackend()
    with patch("careplans.tasks.generate_care_plan_task.delay") as delay:
        backend.submit("123")
    delay.assert_called_once_with("123")


def test_kubernetes_backend_creates_custom_object():
    fake_api = MagicMock()
    fake_client = SimpleNamespace(CustomObjectsApi=MagicMock(return_value=fake_api))
    fake_config = SimpleNamespace(load_kube_config=MagicMock(), load_incluster_config=MagicMock())

    with override_settings(
        CAREPLAN_EXECUTION_BACKEND="kubernetes",
        CAREPLAN_K8S_IMAGE="careplan:test",
        CAREPLAN_K8S_NAMESPACE="testing",
        CAREPLAN_K8S_BACKOFF_LIMIT=4,
    ):
        with patch(
            "careplans.execution._load_kubernetes_modules",
            return_value=(fake_client, fake_config, RuntimeError),
        ):
            backend = get_execution_backend()
            backend.submit("00000000-0000-0000-0000-000000000123")

    fake_config.load_kube_config.assert_called_once()
    fake_api.create_namespaced_custom_object.assert_called_once()
    kwargs = fake_api.create_namespaced_custom_object.call_args.kwargs
    assert kwargs["namespace"] == "testing"
    assert kwargs["group"] == "careplan.example.io"
    assert kwargs["version"] == "v1alpha1"
    assert kwargs["plural"] == "careplanjobs"
    assert kwargs["body"]["metadata"]["name"] == careplan_job_name("00000000-0000-0000-0000-000000000123")
    assert kwargs["body"]["spec"]["carePlanId"] == "00000000-0000-0000-0000-000000000123"
    assert kwargs["body"]["spec"]["image"] == "careplan:test"
    assert kwargs["body"]["spec"]["backoffLimit"] == 4


def test_kubernetes_backend_already_exists_is_idempotent():
    class AlreadyExists(Exception):
        def __init__(self):
            self.status = 409

    fake_api = MagicMock()
    fake_api.create_namespaced_custom_object.side_effect = AlreadyExists()
    fake_client = SimpleNamespace(CustomObjectsApi=MagicMock(return_value=fake_api))
    fake_config = SimpleNamespace(load_kube_config=MagicMock(), load_incluster_config=MagicMock())

    with override_settings(
        CAREPLAN_EXECUTION_BACKEND="kubernetes",
        CAREPLAN_K8S_IMAGE="careplan:test",
    ):
        with patch(
            "careplans.execution._load_kubernetes_modules",
            return_value=(fake_client, fake_config, AlreadyExists),
        ):
            backend = get_execution_backend()
            backend.submit("00000000-0000-0000-0000-000000000123")

    fake_api.create_namespaced_custom_object.assert_called_once()


def test_kubernetes_backend_api_error_propagates():
    class ApiError(Exception):
        def __init__(self):
            self.status = 500

    fake_api = MagicMock()
    fake_api.create_namespaced_custom_object.side_effect = ApiError()
    fake_client = SimpleNamespace(CustomObjectsApi=MagicMock(return_value=fake_api))
    fake_config = SimpleNamespace(load_kube_config=MagicMock(), load_incluster_config=MagicMock())

    with override_settings(
        CAREPLAN_EXECUTION_BACKEND="kubernetes",
        CAREPLAN_K8S_IMAGE="careplan:test",
    ):
        with patch(
            "careplans.execution._load_kubernetes_modules",
            return_value=(fake_client, fake_config, ApiError),
        ):
            backend = get_execution_backend()
            with pytest.raises(ApiError):
                backend.submit("00000000-0000-0000-0000-000000000123")

