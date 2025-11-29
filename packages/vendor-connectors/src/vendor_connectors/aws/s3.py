"""AWS S3 operations.

This module provides operations for working with S3 buckets and objects.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Optional

from botocore.exceptions import ClientError
from extended_data_types import unhump_map

if TYPE_CHECKING:
    from boto3.resources.base import ServiceResource


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
        role_arn = execution_role_arn or getattr(self, "execution_role_arn", None)

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
        role_arn = execution_role_arn or getattr(self, "execution_role_arn", None)

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
        role_arn = execution_role_arn or getattr(self, "execution_role_arn", None)

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
        role_arn = execution_role_arn or getattr(self, "execution_role_arn", None)

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
        role_arn = execution_role_arn or getattr(self, "execution_role_arn", None)

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
        role_arn = execution_role_arn or getattr(self, "execution_role_arn", None)

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
        self.logger.debug(f"Copying s3://{source_bucket}/{source_key} to s3://{dest_bucket}/{dest_key}")
        role_arn = execution_role_arn or getattr(self, "execution_role_arn", None)

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

    # =========================================================================
    # Bucket Features and Configuration
    # =========================================================================

    def get_bucket_features(
        self,
        bucket_name: str,
        execution_role_arn: Optional[str] = None,
    ) -> dict[str, Any]:
        """Get bucket configuration features (logging, versioning, lifecycle, policy).

        Args:
            bucket_name: S3 bucket name.
            execution_role_arn: ARN of role to assume for cross-account access.

        Returns:
            Dictionary with logging, versioning, lifecycle_rules, and policy.
        """
        self.logger.debug(f"Getting features for bucket: {bucket_name}")
        role_arn = execution_role_arn or getattr(self, "execution_role_arn", None)

        s3_resource: ServiceResource = self.get_aws_resource(
            service_name="s3",
            execution_role_arn=role_arn,
        )

        bucket = s3_resource.Bucket(bucket_name)

        # Check if bucket exists
        if not bucket.creation_date:
            self.logger.warning(f"Bucket does not exist: {bucket_name}")
            return {}

        features: dict[str, Any] = {}

        # Logging
        try:
            logging_config = bucket.Logging()
            features["logging"] = logging_config.logging_enabled
        except ClientError:
            self.logger.debug("No logging configuration for bucket")
            features["logging"] = None

        # Versioning
        try:
            versioning = bucket.Versioning()
            features["versioning"] = versioning.status
        except ClientError:
            self.logger.debug("No versioning configuration for bucket")
            features["versioning"] = None

        # Lifecycle rules
        try:
            lifecycle = bucket.LifecycleConfiguration()
            features["lifecycle_rules"] = lifecycle.rules
        except ClientError:
            self.logger.debug("No lifecycle configuration for bucket")
            features["lifecycle_rules"] = None

        # Bucket policy
        try:
            policy = bucket.Policy()
            features["policy"] = policy.policy
        except ClientError:
            self.logger.debug("No policy for bucket")
            features["policy"] = None

        return features

    def find_buckets_by_name(
        self,
        name_contains: str,
        include_features: bool = False,
        execution_role_arn: Optional[str] = None,
    ) -> dict[str, dict[str, Any]]:
        """Find S3 buckets with names containing a string.

        Args:
            name_contains: Substring to search for in bucket names.
            include_features: Include bucket features for each match. Defaults to False.
            execution_role_arn: ARN of role to assume for cross-account access.

        Returns:
            Dictionary mapping bucket names to bucket data/features.
        """
        self.logger.info(f"Finding S3 buckets containing: {name_contains}")
        role_arn = execution_role_arn or getattr(self, "execution_role_arn", None)

        s3_resource: ServiceResource = self.get_aws_resource(
            service_name="s3",
            execution_role_arn=role_arn,
        )

        buckets: dict[str, dict[str, Any]] = {}

        for bucket in s3_resource.buckets.all():
            if name_contains in bucket.name:
                self.logger.debug(f"Found matching bucket: {bucket.name}")

                if include_features:
                    buckets[bucket.name] = self.get_bucket_features(
                        bucket_name=bucket.name,
                        execution_role_arn=role_arn,
                    )
                else:
                    buckets[bucket.name] = {
                        "name": bucket.name,
                        "creation_date": str(bucket.creation_date) if bucket.creation_date else None,
                    }

        self.logger.info(f"Found {len(buckets)} matching buckets")
        return buckets

    def create_bucket(
        self,
        bucket_name: str,
        region: Optional[str] = None,
        acl: str = "private",
        enable_versioning: bool = False,
        tags: Optional[dict[str, str]] = None,
        execution_role_arn: Optional[str] = None,
    ) -> dict[str, Any]:
        """Create an S3 bucket.

        Args:
            bucket_name: Bucket name (must be globally unique).
            region: AWS region. Uses default if not specified.
            acl: Bucket ACL. Defaults to 'private'.
            enable_versioning: Enable versioning. Defaults to False.
            tags: Optional tags to apply.
            execution_role_arn: ARN of role to assume for cross-account access.

        Returns:
            Create bucket response.
        """
        self.logger.info(f"Creating S3 bucket: {bucket_name}")
        role_arn = execution_role_arn or getattr(self, "execution_role_arn", None)

        s3 = self.get_aws_client(
            client_name="s3",
            execution_role_arn=role_arn,
        )

        create_args: dict[str, Any] = {
            "Bucket": bucket_name,
            "ACL": acl,
        }

        # LocationConstraint required for non-us-east-1
        if region and region != "us-east-1":
            create_args["CreateBucketConfiguration"] = {
                "LocationConstraint": region,
            }

        result = s3.create_bucket(**create_args)
        self.logger.info(f"Created bucket: {bucket_name}")

        # Enable versioning if requested
        if enable_versioning:
            s3.put_bucket_versioning(
                Bucket=bucket_name,
                VersioningConfiguration={"Status": "Enabled"},
            )
            self.logger.info(f"Enabled versioning for bucket: {bucket_name}")

        # Apply tags if provided
        if tags:
            tag_set = [{"Key": k, "Value": v} for k, v in tags.items()]
            s3.put_bucket_tagging(
                Bucket=bucket_name,
                Tagging={"TagSet": tag_set},
            )
            self.logger.info(f"Applied {len(tags)} tags to bucket: {bucket_name}")

        return result

    def delete_bucket(
        self,
        bucket_name: str,
        force: bool = False,
        execution_role_arn: Optional[str] = None,
    ) -> None:
        """Delete an S3 bucket.

        Args:
            bucket_name: Bucket name.
            force: Delete all objects first. Defaults to False.
            execution_role_arn: ARN of role to assume for cross-account access.

        Raises:
            ClientError: If bucket not empty and force=False.
        """
        self.logger.info(f"Deleting S3 bucket: {bucket_name}")
        role_arn = execution_role_arn or getattr(self, "execution_role_arn", None)

        if force:
            s3_resource: ServiceResource = self.get_aws_resource(
                service_name="s3",
                execution_role_arn=role_arn,
            )
            bucket = s3_resource.Bucket(bucket_name)

            # Delete all objects
            self.logger.info(f"Deleting all objects in bucket: {bucket_name}")
            bucket.objects.all().delete()

            # Delete all versions
            self.logger.info(f"Deleting all versions in bucket: {bucket_name}")
            bucket.object_versions.all().delete()

        s3 = self.get_aws_client(
            client_name="s3",
            execution_role_arn=role_arn,
        )

        s3.delete_bucket(Bucket=bucket_name)
        self.logger.info(f"Deleted bucket: {bucket_name}")

    def get_bucket_tags(
        self,
        bucket_name: str,
        execution_role_arn: Optional[str] = None,
    ) -> dict[str, str]:
        """Get tags for an S3 bucket.

        Args:
            bucket_name: Bucket name.
            execution_role_arn: ARN of role to assume for cross-account access.

        Returns:
            Dictionary of tag key-value pairs.
        """
        role_arn = execution_role_arn or getattr(self, "execution_role_arn", None)

        s3 = self.get_aws_client(
            client_name="s3",
            execution_role_arn=role_arn,
        )

        try:
            response = s3.get_bucket_tagging(Bucket=bucket_name)
            tags = {tag["Key"]: tag["Value"] for tag in response.get("TagSet", [])}
            return tags
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") == "NoSuchTagSet":
                return {}
            raise

    def set_bucket_tags(
        self,
        bucket_name: str,
        tags: dict[str, str],
        execution_role_arn: Optional[str] = None,
    ) -> None:
        """Set tags for an S3 bucket.

        Args:
            bucket_name: Bucket name.
            tags: Dictionary of tag key-value pairs.
            execution_role_arn: ARN of role to assume for cross-account access.
        """
        self.logger.info(f"Setting {len(tags)} tags on bucket: {bucket_name}")
        role_arn = execution_role_arn or getattr(self, "execution_role_arn", None)

        s3 = self.get_aws_client(
            client_name="s3",
            execution_role_arn=role_arn,
        )

        tag_set = [{"Key": k, "Value": v} for k, v in tags.items()]
        s3.put_bucket_tagging(
            Bucket=bucket_name,
            Tagging={"TagSet": tag_set},
        )
        self.logger.info(f"Set tags on bucket: {bucket_name}")
