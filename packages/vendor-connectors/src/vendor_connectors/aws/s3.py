"""AWS S3 operations.

This module provides operations for working with S3 buckets and objects.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Optional

from botocore.exceptions import ClientError
from extended_data_types import unhump_map

if TYPE_CHECKING:
    pass


class AWSS3Mixin:
    """Mixin providing AWS S3 operations.

    This mixin requires the base AWSConnector class to provide:
    - get_aws_client()
    - get_aws_resource()
    - logger
    - execution_role_arn
    """

    def list_s3_buckets(
        self,
        unhump_buckets: bool = True,
        execution_role_arn: Optional[str] = None,
    ) -> dict[str, dict[str, Any]]:
        """List all S3 buckets.

        Args:
            unhump_buckets: Convert keys to snake_case. Defaults to True.
            execution_role_arn: ARN of role to assume for cross-account access.

        Returns:
            Dictionary mapping bucket names to bucket data.
        """
        self.logger.info("Listing S3 buckets")
        role_arn = execution_role_arn or getattr(self, 'execution_role_arn', None)

        s3 = self.get_aws_client(
            client_name="s3",
            execution_role_arn=role_arn,
        )

        response = s3.list_buckets()
        buckets: dict[str, dict[str, Any]] = {}

        for bucket in response.get("Buckets", []):
            name = bucket["Name"]
            buckets[name] = bucket

        if unhump_buckets:
            buckets = {k: unhump_map(v) for k, v in buckets.items()}

        self.logger.info(f"Retrieved {len(buckets)} buckets")
        return buckets

    def get_bucket_location(
        self,
        bucket_name: str,
        execution_role_arn: Optional[str] = None,
    ) -> str:
        """Get the region of an S3 bucket.

        Args:
            bucket_name: Name of the S3 bucket.
            execution_role_arn: ARN of role to assume for cross-account access.

        Returns:
            The AWS region where the bucket is located.
        """
        self.logger.debug(f"Getting location for bucket: {bucket_name}")
        role_arn = execution_role_arn or getattr(self, 'execution_role_arn', None)

        s3 = self.get_aws_client(
            client_name="s3",
            execution_role_arn=role_arn,
        )

        response = s3.get_bucket_location(Bucket=bucket_name)
        location = response.get("LocationConstraint") or "us-east-1"
        return location

    def get_object(
        self,
        bucket: str,
        key: str,
        decode: bool = True,
        execution_role_arn: Optional[str] = None,
    ) -> Optional[str | bytes]:
        """Get an object from S3.

        Args:
            bucket: S3 bucket name.
            key: S3 object key.
            decode: Decode bytes to string. Defaults to True.
            execution_role_arn: ARN of role to assume for cross-account access.

        Returns:
            The object contents, or None if not found.
        """
        self.logger.debug(f"Getting S3 object: s3://{bucket}/{key}")
        role_arn = execution_role_arn or getattr(self, 'execution_role_arn', None)

        s3 = self.get_aws_client(
            client_name="s3",
            execution_role_arn=role_arn,
        )

        try:
            response = s3.get_object(Bucket=bucket, Key=key)
            body = response["Body"].read()

            if decode:
                return body.decode("utf-8")
            return body
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") == "NoSuchKey":
                self.logger.warning(f"S3 object not found: s3://{bucket}/{key}")
                return None
            raise

    def get_json_object(
        self,
        bucket: str,
        key: str,
        execution_role_arn: Optional[str] = None,
    ) -> Optional[dict[str, Any] | list]:
        """Get a JSON object from S3.

        Args:
            bucket: S3 bucket name.
            key: S3 object key.
            execution_role_arn: ARN of role to assume for cross-account access.

        Returns:
            The parsed JSON object, or None if not found.
        """
        content = self.get_object(
            bucket=bucket,
            key=key,
            decode=True,
            execution_role_arn=execution_role_arn,
        )

        if content is None:
            return None

        return json.loads(content)

    def put_object(
        self,
        bucket: str,
        key: str,
        body: str | bytes,
        content_type: Optional[str] = None,
        metadata: Optional[dict[str, str]] = None,
        execution_role_arn: Optional[str] = None,
    ) -> dict[str, Any]:
        """Put an object to S3.

        Args:
            bucket: S3 bucket name.
            key: S3 object key.
            body: Object content.
            content_type: Content-Type header. Auto-detected if not provided.
            metadata: Optional metadata to attach to object.
            execution_role_arn: ARN of role to assume for cross-account access.

        Returns:
            The S3 put_object response.
        """
        self.logger.debug(f"Putting S3 object: s3://{bucket}/{key}")
        role_arn = execution_role_arn or getattr(self, 'execution_role_arn', None)

        s3 = self.get_aws_client(
            client_name="s3",
            execution_role_arn=role_arn,
        )

        if isinstance(body, str):
            body = body.encode("utf-8")

        put_args: dict[str, Any] = {
            "Bucket": bucket,
            "Key": key,
            "Body": body,
        }

        if content_type:
            put_args["ContentType"] = content_type
        elif key.endswith(".json"):
            put_args["ContentType"] = "application/json"
        elif key.endswith(".tf.json"):
            put_args["ContentType"] = "application/json"
        elif key.endswith(".yaml") or key.endswith(".yml"):
            put_args["ContentType"] = "text/yaml"

        if metadata:
            put_args["Metadata"] = metadata

        response = s3.put_object(**put_args)
        self.logger.debug(f"Put object to s3://{bucket}/{key}")
        return response

    def put_json_object(
        self,
        bucket: str,
        key: str,
        data: dict[str, Any] | list,
        indent: int = 2,
        metadata: Optional[dict[str, str]] = None,
        execution_role_arn: Optional[str] = None,
    ) -> dict[str, Any]:
        """Put a JSON object to S3.

        Args:
            bucket: S3 bucket name.
            key: S3 object key.
            data: Data to serialize to JSON.
            indent: JSON indentation. Defaults to 2.
            metadata: Optional metadata to attach to object.
            execution_role_arn: ARN of role to assume for cross-account access.

        Returns:
            The S3 put_object response.
        """
        body = json.dumps(data, indent=indent, default=str)
        return self.put_object(
            bucket=bucket,
            key=key,
            body=body,
            content_type="application/json",
            metadata=metadata,
            execution_role_arn=execution_role_arn,
        )

    def delete_object(
        self,
        bucket: str,
        key: str,
        execution_role_arn: Optional[str] = None,
    ) -> dict[str, Any]:
        """Delete an object from S3.

        Args:
            bucket: S3 bucket name.
            key: S3 object key.
            execution_role_arn: ARN of role to assume for cross-account access.

        Returns:
            The S3 delete_object response.
        """
        self.logger.debug(f"Deleting S3 object: s3://{bucket}/{key}")
        role_arn = execution_role_arn or getattr(self, 'execution_role_arn', None)

        s3 = self.get_aws_client(
            client_name="s3",
            execution_role_arn=role_arn,
        )

        response = s3.delete_object(Bucket=bucket, Key=key)
        self.logger.debug(f"Deleted object s3://{bucket}/{key}")
        return response

    def list_objects(
        self,
        bucket: str,
        prefix: Optional[str] = None,
        delimiter: Optional[str] = None,
        max_keys: Optional[int] = None,
        unhump_objects: bool = True,
        execution_role_arn: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """List objects in an S3 bucket.

        Args:
            bucket: S3 bucket name.
            prefix: Key prefix to filter by.
            delimiter: Delimiter for hierarchical listing.
            max_keys: Maximum number of keys to return.
            unhump_objects: Convert keys to snake_case. Defaults to True.
            execution_role_arn: ARN of role to assume for cross-account access.

        Returns:
            List of object metadata dictionaries.
        """
        self.logger.debug(f"Listing objects in s3://{bucket}/{prefix or ''}")
        role_arn = execution_role_arn or getattr(self, 'execution_role_arn', None)

        s3 = self.get_aws_client(
            client_name="s3",
            execution_role_arn=role_arn,
        )

        objects: list[dict[str, Any]] = []
        paginator = s3.get_paginator("list_objects_v2")

        paginate_args: dict[str, Any] = {"Bucket": bucket}
        if prefix:
            paginate_args["Prefix"] = prefix
        if delimiter:
            paginate_args["Delimiter"] = delimiter
        if max_keys:
            paginate_args["MaxKeys"] = max_keys

        for page in paginator.paginate(**paginate_args):
            for obj in page.get("Contents", []):
                objects.append(obj)

            if max_keys and len(objects) >= max_keys:
                objects = objects[:max_keys]
                break

        if unhump_objects:
            objects = [unhump_map(o) for o in objects]

        self.logger.debug(f"Found {len(objects)} objects")
        return objects

    def copy_object(
        self,
        source_bucket: str,
        source_key: str,
        dest_bucket: str,
        dest_key: str,
        execution_role_arn: Optional[str] = None,
    ) -> dict[str, Any]:
        """Copy an object within S3.

        Args:
            source_bucket: Source bucket name.
            source_key: Source object key.
            dest_bucket: Destination bucket name.
            dest_key: Destination object key.
            execution_role_arn: ARN of role to assume for cross-account access.

        Returns:
            The S3 copy_object response.
        """
        self.logger.debug(
            f"Copying s3://{source_bucket}/{source_key} to s3://{dest_bucket}/{dest_key}"
        )
        role_arn = execution_role_arn or getattr(self, 'execution_role_arn', None)

        s3 = self.get_aws_client(
            client_name="s3",
            execution_role_arn=role_arn,
        )

        response = s3.copy_object(
            Bucket=dest_bucket,
            Key=dest_key,
            CopySource={"Bucket": source_bucket, "Key": source_key},
        )
        self.logger.debug(f"Copied object to s3://{dest_bucket}/{dest_key}")
        return response
