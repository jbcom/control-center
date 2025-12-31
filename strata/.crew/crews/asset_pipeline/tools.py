from crewai_tools import BaseTool
from vendor_connectors.meshy import MeshyConnector
import time
import os

# It's good practice to get API keys from environment variables
# For now, I'll assume it's handled by the vendor-connector library configuration
meshy_connector = MeshyConnector()

class MeshyTextToAssetTool(BaseTool):
    name: str = "Meshy Text-to-Asset Generator"
    description: str = "Generates a 3D asset from a text description using Meshy. Takes a detailed prompt as input."

    def _run(self, prompt: str) -> str:
        """Use the tool."""
        # Broader exception handling is used for simplicity. In a production environment,
        # it would be better to catch more specific exceptions.
        try:
            asset_id = meshy_connector.text_to_asset(prompt)
            return f"Successfully submitted text-to-asset request to Meshy. The asset ID is: {asset_id}. You can use another tool to check the status."
        except Exception as e:
            return f"Failed to generate asset from text. Error: {e}"

class MeshyAssetStatusTool(BaseTool):
    name: str = "Meshy Asset Status Checker"
    description: str = "Checks the generation status of a 3D asset on Meshy using its asset ID. It will poll the API until the asset is fully generated or it times out."

    def _run(self, asset_id: str) -> str:
        """Use the tool."""
        max_retries = 30  # e.g., 30 retries
        poll_interval = int(os.environ.get("MESHY_POLL_INTERVAL", 10)) # Default to 10 seconds

        for _ in range(max_retries):
            try:
                status = meshy_connector.get_asset_status(asset_id)
                if status in ['SUCCEEDED', 'FAILED']:
                    return f"The final status for asset {asset_id} is: {status}."

                time.sleep(poll_interval)
            except Exception as e:
                # Broader exception handling is used for simplicity. In a production environment,
                # it would be better to catch more specific exceptions from the connector.
                return f"Failed to get asset status. Error: {e}"

        return f"Asset generation for {asset_id} timed out after {max_retries * poll_interval} seconds."

# Instantiate tools for agents to use
meshy_text_to_asset_tool = MeshyTextToAssetTool()
meshy_asset_status_tool = MeshyAssetStatusTool()
