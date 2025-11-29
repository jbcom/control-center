"""Google Cloud services discovery operations.

This module provides operations for discovering resources across Google Cloud
services like GKE, Compute Engine, Cloud Storage, Cloud SQL, Pub/Sub, etc.
"""

from __future__ import annotations

from typing import Any, Optional

from extended_data_types import unhump_map


class GoogleServicesMixin:
    """Mixin providing Google Cloud services discovery operations.

    This mixin requires the base GoogleConnector class to provide:
    - get_compute_service()
    - get_container_service()
    - get_storage_service()
    - get_sqladmin_service()
    - get_pubsub_service()
    - get_serviceusage_service()
    - get_cloudkms_service()
    - logger
    """

    # =========================================================================
    # Compute Engine
    # =========================================================================

    def list_compute_instances(
        self,
        project_id: str,
        zone: Optional[str] = None,
        unhump_instances: bool = False,
    ) -> list[dict[str, Any]]:
        """List Compute Engine instances in a project.

        Args:
            project_id: The project ID.
            zone: Optional zone filter. If not provided, lists all zones.
            unhump_instances: Convert keys to snake_case. Defaults to False.

        Returns:
            List of instance dictionaries.
        """
        self.logger.info(f"Listing Compute Engine instances in {project_id}")
        service = self.get_compute_service()

        instances: list[dict[str, Any]] = []

        if zone:
            # List instances in specific zone
            page_token = None
            while True:
                params: dict[str, Any] = {"project": project_id, "zone": zone}
                if page_token:
                    params["pageToken"] = page_token

                response = service.instances().list(**params).execute()
                instances.extend(response.get("items", []))

                page_token = response.get("nextPageToken")
                if not page_token:
                    break
        else:
            # Aggregate list across all zones
            page_token = None
            while True:
                params: dict[str, Any] = {"project": project_id}
                if page_token:
                    params["pageToken"] = page_token

                response = service.instances().aggregatedList(**params).execute()
                for zone_data in response.get("items", {}).values():
                    instances.extend(zone_data.get("instances", []))

                page_token = response.get("nextPageToken")
                if not page_token:
                    break

        self.logger.info(f"Retrieved {len(instances)} instances")

        if unhump_instances:
            instances = [unhump_map(i) for i in instances]

        return instances

    # =========================================================================
    # Google Kubernetes Engine
    # =========================================================================

    def list_gke_clusters(
        self,
        project_id: str,
        location: str = "-",
        unhump_clusters: bool = False,
    ) -> list[dict[str, Any]]:
        """List GKE clusters in a project.

        Args:
            project_id: The project ID.
            location: Zone or region. Use '-' for all locations.
            unhump_clusters: Convert keys to snake_case. Defaults to False.

        Returns:
            List of cluster dictionaries.
        """
        self.logger.info(f"Listing GKE clusters in {project_id}")
        service = self.get_container_service()

        parent = f"projects/{project_id}/locations/{location}"
        response = service.projects().locations().clusters().list(parent=parent).execute()

        clusters = response.get("clusters", [])
        self.logger.info(f"Retrieved {len(clusters)} GKE clusters")

        if unhump_clusters:
            clusters = [unhump_map(c) for c in clusters]

        return clusters

    def get_gke_cluster(
        self,
        project_id: str,
        location: str,
        cluster_id: str,
    ) -> Optional[dict[str, Any]]:
        """Get a specific GKE cluster.

        Args:
            project_id: The project ID.
            location: Zone or region.
            cluster_id: The cluster ID.

        Returns:
            Cluster dictionary or None if not found.
        """
        from googleapiclient.errors import HttpError

        service = self.get_container_service()
        name = f"projects/{project_id}/locations/{location}/clusters/{cluster_id}"

        try:
            cluster = service.projects().locations().clusters().get(name=name).execute()
            return cluster
        except HttpError as e:
            if e.resp.status == 404:
                self.logger.warning(f"GKE cluster not found: {cluster_id}")
                return None
            raise

    # =========================================================================
    # Cloud Storage
    # =========================================================================

    def list_storage_buckets(
        self,
        project_id: str,
        unhump_buckets: bool = False,
    ) -> list[dict[str, Any]]:
        """List Cloud Storage buckets in a project.

        Args:
            project_id: The project ID.
            unhump_buckets: Convert keys to snake_case. Defaults to False.

        Returns:
            List of bucket dictionaries.
        """
        self.logger.info(f"Listing Cloud Storage buckets in {project_id}")
        service = self.get_storage_service()

        buckets: list[dict[str, Any]] = []
        page_token = None

        while True:
            params: dict[str, Any] = {"project": project_id}
            if page_token:
                params["pageToken"] = page_token

            response = service.buckets().list(**params).execute()
            buckets.extend(response.get("items", []))

            page_token = response.get("nextPageToken")
            if not page_token:
                break

        self.logger.info(f"Retrieved {len(buckets)} buckets")

        if unhump_buckets:
            buckets = [unhump_map(b) for b in buckets]

        return buckets

    # =========================================================================
    # Cloud SQL
    # =========================================================================

    def list_sql_instances(
        self,
        project_id: str,
        unhump_instances: bool = False,
    ) -> list[dict[str, Any]]:
        """List Cloud SQL instances in a project.

        Args:
            project_id: The project ID.
            unhump_instances: Convert keys to snake_case. Defaults to False.

        Returns:
            List of SQL instance dictionaries.
        """
        self.logger.info(f"Listing Cloud SQL instances in {project_id}")
        service = self.get_sqladmin_service()

        instances: list[dict[str, Any]] = []
        page_token = None

        while True:
            params: dict[str, Any] = {"project": project_id}
            if page_token:
                params["pageToken"] = page_token

            response = service.instances().list(**params).execute()
            instances.extend(response.get("items", []))

            page_token = response.get("nextPageToken")
            if not page_token:
                break

        self.logger.info(f"Retrieved {len(instances)} SQL instances")

        if unhump_instances:
            instances = [unhump_map(i) for i in instances]

        return instances

    # =========================================================================
    # Pub/Sub
    # =========================================================================

    def list_pubsub_topics(
        self,
        project_id: str,
        unhump_topics: bool = False,
    ) -> list[dict[str, Any]]:
        """List Pub/Sub topics in a project.

        Args:
            project_id: The project ID.
            unhump_topics: Convert keys to snake_case. Defaults to False.

        Returns:
            List of topic dictionaries.
        """
        self.logger.info(f"Listing Pub/Sub topics in {project_id}")
        service = self.get_pubsub_service()

        topics: list[dict[str, Any]] = []
        page_token = None

        while True:
            params: dict[str, Any] = {"project": f"projects/{project_id}"}
            if page_token:
                params["pageToken"] = page_token

            response = service.projects().topics().list(**params).execute()
            topics.extend(response.get("topics", []))

            page_token = response.get("nextPageToken")
            if not page_token:
                break

        self.logger.info(f"Retrieved {len(topics)} Pub/Sub topics")

        if unhump_topics:
            topics = [unhump_map(t) for t in topics]

        return topics

    def list_pubsub_subscriptions(
        self,
        project_id: str,
        unhump_subscriptions: bool = False,
    ) -> list[dict[str, Any]]:
        """List Pub/Sub subscriptions in a project.

        Args:
            project_id: The project ID.
            unhump_subscriptions: Convert keys to snake_case. Defaults to False.

        Returns:
            List of subscription dictionaries.
        """
        self.logger.info(f"Listing Pub/Sub subscriptions in {project_id}")
        service = self.get_pubsub_service()

        subscriptions: list[dict[str, Any]] = []
        page_token = None

        while True:
            params: dict[str, Any] = {"project": f"projects/{project_id}"}
            if page_token:
                params["pageToken"] = page_token

            response = service.projects().subscriptions().list(**params).execute()
            subscriptions.extend(response.get("subscriptions", []))

            page_token = response.get("nextPageToken")
            if not page_token:
                break

        self.logger.info(f"Retrieved {len(subscriptions)} Pub/Sub subscriptions")

        if unhump_subscriptions:
            subscriptions = [unhump_map(s) for s in subscriptions]

        return subscriptions

    # =========================================================================
    # Service Usage (Enabled APIs)
    # =========================================================================

    def list_enabled_services(
        self,
        project_id: str,
        unhump_services: bool = False,
    ) -> list[dict[str, Any]]:
        """List enabled APIs/services in a project.

        Args:
            project_id: The project ID.
            unhump_services: Convert keys to snake_case. Defaults to False.

        Returns:
            List of service dictionaries.
        """
        self.logger.info(f"Listing enabled services in {project_id}")
        service = self.get_serviceusage_service()

        services: list[dict[str, Any]] = []
        page_token = None

        while True:
            params: dict[str, Any] = {
                "parent": f"projects/{project_id}",
                "filter": "state:ENABLED",
            }
            if page_token:
                params["pageToken"] = page_token

            response = service.services().list(**params).execute()
            services.extend(response.get("services", []))

            page_token = response.get("nextPageToken")
            if not page_token:
                break

        self.logger.info(f"Retrieved {len(services)} enabled services")

        if unhump_services:
            services = [unhump_map(s) for s in services]

        return services

    def enable_service(
        self,
        project_id: str,
        service_name: str,
    ) -> dict[str, Any]:
        """Enable an API/service in a project.

        Args:
            project_id: The project ID.
            service_name: Service name (e.g., 'compute.googleapis.com').

        Returns:
            Operation response dictionary.
        """
        self.logger.info(f"Enabling service {service_name} in {project_id}")
        service = self.get_serviceusage_service()

        name = f"projects/{project_id}/services/{service_name}"
        result = service.services().enable(name=name).execute()

        self.logger.info(f"Enabled service {service_name}")
        return result

    def disable_service(
        self,
        project_id: str,
        service_name: str,
        force: bool = False,
    ) -> dict[str, Any]:
        """Disable an API/service in a project.

        Args:
            project_id: The project ID.
            service_name: Service name (e.g., 'compute.googleapis.com').
            force: Force disable even if dependencies exist.

        Returns:
            Operation response dictionary.
        """
        self.logger.info(f"Disabling service {service_name} in {project_id}")
        service = self.get_serviceusage_service()

        name = f"projects/{project_id}/services/{service_name}"
        body: dict[str, Any] = {}
        if force:
            body["disableDependentServices"] = True

        result = service.services().disable(name=name, body=body).execute()

        self.logger.info(f"Disabled service {service_name}")
        return result

    def batch_enable_services(
        self,
        project_id: str,
        service_names: list[str],
    ) -> dict[str, Any]:
        """Enable multiple APIs/services in a project.

        Args:
            project_id: The project ID.
            service_names: List of service names to enable.

        Returns:
            Operation response dictionary.
        """
        self.logger.info(f"Batch enabling {len(service_names)} services in {project_id}")
        service = self.get_serviceusage_service()

        parent = f"projects/{project_id}"
        result = (
            service.services()
            .batchEnable(
                parent=parent,
                body={"serviceIds": service_names},
            )
            .execute()
        )

        self.logger.info(f"Batch enabled {len(service_names)} services")
        return result

    # =========================================================================
    # Cloud KMS
    # =========================================================================

    def list_kms_keyrings(
        self,
        project_id: str,
        location: str,
        unhump_keyrings: bool = False,
    ) -> list[dict[str, Any]]:
        """List KMS key rings in a project location.

        Args:
            project_id: The project ID.
            location: The location (e.g., 'us-central1', 'global').
            unhump_keyrings: Convert keys to snake_case. Defaults to False.

        Returns:
            List of key ring dictionaries.
        """
        self.logger.info(f"Listing KMS key rings in {project_id}/{location}")
        service = self.get_cloudkms_service()

        keyrings: list[dict[str, Any]] = []
        page_token = None
        parent = f"projects/{project_id}/locations/{location}"

        while True:
            params: dict[str, Any] = {"parent": parent}
            if page_token:
                params["pageToken"] = page_token

            response = service.projects().locations().keyRings().list(**params).execute()
            keyrings.extend(response.get("keyRings", []))

            page_token = response.get("nextPageToken")
            if not page_token:
                break

        self.logger.info(f"Retrieved {len(keyrings)} key rings")

        if unhump_keyrings:
            keyrings = [unhump_map(k) for k in keyrings]

        return keyrings

    def create_kms_keyring(
        self,
        project_id: str,
        location: str,
        keyring_id: str,
    ) -> dict[str, Any]:
        """Create a KMS key ring.

        Args:
            project_id: The project ID.
            location: The location (e.g., 'us-central1', 'global').
            keyring_id: Unique key ring ID.

        Returns:
            Created key ring dictionary.
        """
        self.logger.info(f"Creating KMS key ring {keyring_id} in {project_id}/{location}")
        service = self.get_cloudkms_service()

        parent = f"projects/{project_id}/locations/{location}"
        result = (
            service.projects()
            .locations()
            .keyRings()
            .create(
                parent=parent,
                keyRingId=keyring_id,
                body={},
            )
            .execute()
        )

        self.logger.info(f"Created key ring {keyring_id}")
        return result

    def create_kms_key(
        self,
        project_id: str,
        location: str,
        keyring_id: str,
        key_id: str,
        purpose: str = "ENCRYPT_DECRYPT",
        algorithm: str = "GOOGLE_SYMMETRIC_ENCRYPTION",
    ) -> dict[str, Any]:
        """Create a KMS crypto key.

        Args:
            project_id: The project ID.
            location: The location.
            keyring_id: The key ring ID.
            key_id: Unique key ID.
            purpose: Key purpose (ENCRYPT_DECRYPT, ASYMMETRIC_SIGN, etc.).
            algorithm: Key algorithm.

        Returns:
            Created crypto key dictionary.
        """
        self.logger.info(f"Creating KMS key {key_id} in {keyring_id}")
        service = self.get_cloudkms_service()

        parent = f"projects/{project_id}/locations/{location}/keyRings/{keyring_id}"

        body: dict[str, Any] = {"purpose": purpose}
        if purpose == "ENCRYPT_DECRYPT":
            body["versionTemplate"] = {"algorithm": algorithm}

        result = (
            service.projects()
            .locations()
            .keyRings()
            .cryptoKeys()
            .create(
                parent=parent,
                cryptoKeyId=key_id,
                body=body,
            )
            .execute()
        )

        self.logger.info(f"Created crypto key {key_id}")
        return result

    # =========================================================================
    # Project Resource Summary
    # =========================================================================

    def is_project_empty(
        self,
        project_id: str,
        check_compute: bool = True,
        check_gke: bool = True,
        check_storage: bool = True,
        check_sql: bool = True,
        check_pubsub: bool = True,
    ) -> bool:
        """Check if a project has no resources.

        Args:
            project_id: The project ID.
            check_compute: Check for Compute Engine instances.
            check_gke: Check for GKE clusters.
            check_storage: Check for Cloud Storage buckets.
            check_sql: Check for Cloud SQL instances.
            check_pubsub: Check for Pub/Sub topics.

        Returns:
            True if the project has no resources.
        """
        self.logger.info(f"Checking if project {project_id} is empty")

        from googleapiclient.errors import HttpError

        try:
            if check_compute:
                instances = self.list_compute_instances(project_id)
                if instances:
                    self.logger.info(f"Project {project_id} has {len(instances)} compute instances")
                    return False

            if check_gke:
                clusters = self.list_gke_clusters(project_id)
                if clusters:
                    self.logger.info(f"Project {project_id} has {len(clusters)} GKE clusters")
                    return False

            if check_storage:
                buckets = self.list_storage_buckets(project_id)
                if buckets:
                    self.logger.info(f"Project {project_id} has {len(buckets)} storage buckets")
                    return False

            if check_sql:
                sql_instances = self.list_sql_instances(project_id)
                if sql_instances:
                    self.logger.info(f"Project {project_id} has {len(sql_instances)} SQL instances")
                    return False

            if check_pubsub:
                topics = self.list_pubsub_topics(project_id)
                if topics:
                    self.logger.info(f"Project {project_id} has {len(topics)} Pub/Sub topics")
                    return False

        except HttpError as e:
            # API might not be enabled, treat as empty for that service
            if e.resp.status == 403:
                self.logger.debug(f"API access denied, skipping check: {e}")
            else:
                raise

        self.logger.info(f"Project {project_id} appears to be empty")
        return True

    # =========================================================================
    # IAM and Resource Aggregation
    # =========================================================================

    def get_project_iam_users(
        self,
        project_id: str,
    ) -> dict[str, dict[str, Any]]:
        """Get human users (non-service accounts) with IAM bindings on a project.

        Parses the project IAM policy and extracts users with their roles.

        Args:
            project_id: The project ID.

        Returns:
            Dictionary mapping user emails to their IAM roles:
            {
                "user@example.com": {
                    "roles": ["roles/viewer", "roles/editor"]
                }
            }
        """
        from googleapiclient.errors import HttpError

        self.logger.info(f"Retrieving IAM users for project '{project_id}'")

        cloud_resource_manager = self.get_service("cloudresourcemanager", "v1")

        users_map: dict[str, dict[str, Any]] = {}

        try:
            response = (
                cloud_resource_manager.projects()
                .getIamPolicy(resource=project_id, body={})
                .execute()
            )

            bindings = response.get("bindings", [])
            for binding in bindings:
                role = binding.get("role", "")
                members = binding.get("members", [])
                for member in members:
                    if member.startswith("user:"):
                        user_email = member.split("user:")[1]
                        if user_email not in users_map:
                            users_map[user_email] = {"roles": []}
                        users_map[user_email]["roles"].append(role)

            self.logger.info(f"Found {len(users_map)} users for project '{project_id}'")

        except HttpError as e:
            self.logger.warning(f"Error retrieving users for project '{project_id}': {e}")

        return users_map

    def get_pubsub_resources_for_project(
        self,
        project_id: str,
    ) -> dict[str, dict[str, Any]]:
        """Get all Pub/Sub topics and subscriptions for a project.

        Aggregates topics and subscriptions into a single map.

        Args:
            project_id: The project ID.

        Returns:
            Dictionary mapping resource names to their type and details:
            {
                "projects/myproject/topics/mytopic": {
                    "type": "topic",
                    "details": {...}
                },
                "projects/myproject/subscriptions/mysub": {
                    "type": "subscription",
                    "details": {...}
                }
            }
        """
        self.logger.info(f"Retrieving Pub/Sub resources for project '{project_id}'")

        pubsub_map: dict[str, dict[str, Any]] = {}

        # Get topics
        topics = self.list_pubsub_topics(project_id)
        for topic in topics:
            topic_name = topic.get("name", "")
            if topic_name:
                pubsub_map[topic_name] = {
                    "type": "topic",
                    "details": topic,
                }

        # Get subscriptions
        subscriptions = self.list_pubsub_subscriptions(project_id)
        for subscription in subscriptions:
            subscription_name = subscription.get("name", "")
            if subscription_name:
                pubsub_map[subscription_name] = {
                    "type": "subscription",
                    "details": subscription,
                }

        self.logger.info(
            f"Found {len(pubsub_map)} Pub/Sub resources for project '{project_id}'"
        )
        return pubsub_map

    def find_inactive_projects(
        self,
        inactivity_period_days: int = 30,
        billing_project_id: str = "",
        billing_dataset_id: str = "billing_dataset",
    ) -> list[str]:
        """Find GCP projects with no billing activity in the specified period.

        Uses BigQuery to query billing export data and identify projects
        with zero or null costs.

        Args:
            inactivity_period_days: Number of days to check for inactivity.
                Defaults to 30.
            billing_project_id: Project ID containing the billing export dataset.
            billing_dataset_id: BigQuery dataset ID for billing export.
                Defaults to "billing_dataset".

        Returns:
            List of project IDs with no billing activity.

        Raises:
            ValueError: If billing_project_id is not provided.
        """
        from googleapiclient.errors import HttpError

        if not billing_project_id:
            raise ValueError("billing_project_id is required")

        self.logger.info(
            f"Finding inactive projects (no activity in {inactivity_period_days} days)"
        )

        bigquery = self.get_service("bigquery", "v2")

        # Construct the query
        query = f"""
            SELECT project.id AS project_id, SUM(cost) AS total_cost
            FROM `{billing_project_id}.{billing_dataset_id}.*`
            WHERE usage_start_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {inactivity_period_days} DAY)
            GROUP BY project.id
            HAVING total_cost IS NULL OR total_cost = 0
        """

        try:
            self.logger.debug(f"Executing BigQuery: {query}")

            results = (
                bigquery.jobs()
                .query(
                    projectId=billing_project_id,
                    body={"query": query, "useLegacySql": False},
                )
                .execute()
            )

            rows = results.get("rows", [])
            if not rows:
                self.logger.info("No inactive projects found")
                return []

            # Extract project IDs from results
            projects = []
            for row in rows:
                if "f" in row and len(row["f"]) > 0:
                    project_id = row["f"][0].get("v")
                    if project_id:
                        projects.append(project_id)

            self.logger.info(f"Found {len(projects)} inactive projects")
            return projects

        except HttpError as e:
            self.logger.error(f"Failed to query for inactive projects: {e}")
            raise
