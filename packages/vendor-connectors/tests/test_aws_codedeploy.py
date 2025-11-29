"""Tests for the AWS CodeDeploy helper module."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError, WaiterError

from vendor_connectors.aws.codedeploy import (
    create_codedeploy_deployment,
    get_aws_codedeploy_deployments,
)


def _client_error(operation: str) -> ClientError:
    return ClientError(
        error_response={"Error": {"Code": "AccessDenied", "Message": "denied"}},
        operation_name=operation,
    )


class TestGetAwsCodeDeployDeployments:
    def test_returns_details_and_normalizes_statuses(self):
        codedeploy_client = MagicMock()
        codedeploy_client.list_deployments.side_effect = [
            {"deployments": ["dep-1", "dep-2"], "nextToken": "token-1"},
            {"deployments": ["dep-3"]},
        ]
        codedeploy_client.batch_get_deployments.return_value = {
            "deploymentsInfo": [
                {"deploymentId": "dep-1", "status": "Succeeded"},
                {"deploymentId": "dep-2", "status": "Failed"},
                {"deploymentId": "dep-3", "status": "Created"},
            ]
        }

        result = get_aws_codedeploy_deployments(
            application_name="app",
            deployment_group_name="group",
            statuses=["succeeded", "FAILED"],
            codedeploy_client=codedeploy_client,
        )

        assert result["deployment_ids"] == ["dep-1", "dep-2", "dep-3"]
        assert [item["deploymentId"] for item in result["deployments"]] == ["dep-1", "dep-2", "dep-3"]

        first_call_kwargs = codedeploy_client.list_deployments.call_args_list[0].kwargs
        assert first_call_kwargs["includeOnlyStatuses"] == ["Succeeded", "Failed"]

    def test_raises_runtime_error_on_client_failure(self):
        codedeploy_client = MagicMock()
        codedeploy_client.list_deployments.side_effect = _client_error("ListDeployments")

        with pytest.raises(RuntimeError):
            get_aws_codedeploy_deployments(codedeploy_client=codedeploy_client)


class TestCreateCodeDeployDeployment:
    def test_waits_for_success_and_returns_details(self):
        codedeploy_client = MagicMock()
        codedeploy_client.create_deployment.return_value = {"deploymentId": "dep-123"}
        codedeploy_client.get_deployment.return_value = {
            "deploymentInfo": {"deploymentId": "dep-123", "status": "Succeeded"}
        }

        waiter = MagicMock()
        codedeploy_client.get_waiter.return_value = waiter

        result = create_codedeploy_deployment(
            application_name="app",
            deployment_group_name="group",
            revision={
                "revisionType": "S3",
                "s3Location": {"bucket": "bucket", "key": "bundle.zip", "bundleType": "zip"},
            },
            wait=True,
            codedeploy_client=codedeploy_client,
        )

        assert result["deployment_id"] == "dep-123"
        assert result["status"] == "Succeeded"
        waiter.wait.assert_called_once_with(
            deploymentId="dep-123",
            WaiterConfig={"Delay": 15, "MaxAttempts": 120},
        )

    def test_waiter_failure_raises_runtime_error(self):
        codedeploy_client = MagicMock()
        codedeploy_client.create_deployment.return_value = {"deploymentId": "dep-456"}
        codedeploy_client.get_deployment.return_value = {
            "deploymentInfo": {"deploymentId": "dep-456", "status": "Failed"}
        }

        waiter = MagicMock()
        waiter.wait.side_effect = WaiterError(
            name="deployment_successful",
            reason="failure",
            last_response={},
        )
        codedeploy_client.get_waiter.return_value = waiter

        with pytest.raises(RuntimeError):
            create_codedeploy_deployment(
                application_name="app",
                deployment_group_name="group",
                revision={
                    "revisionType": "S3",
                    "s3Location": {"bucket": "bucket", "key": "bundle.zip", "bundleType": "zip"},
                },
                wait=True,
                codedeploy_client=codedeploy_client,
            )

    def test_validates_file_exists_behavior(self):
        codedeploy_client = MagicMock()

        with pytest.raises(ValueError):
            create_codedeploy_deployment(
                application_name="app",
                deployment_group_name="group",
                revision={
                    "revisionType": "S3",
                    "s3Location": {"bucket": "bucket", "key": "bundle.zip", "bundleType": "zip"},
                },
                file_exists_behavior="skip",
                codedeploy_client=codedeploy_client,
            )
