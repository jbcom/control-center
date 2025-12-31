from crewai import Task
from .agents import asset_designer, meshy_operator

# Define the tasks
design_prompt_task = Task(
  description="""Based on the initial concept: '{concept}', develop a detailed prompt for a 3D asset.
  The prompt should be suitable for an AI text-to-3D model generator.
  Consider the art style, level of detail, and any specific requirements for the asset.""",
  expected_output="A detailed text prompt for a 3D asset, ready to be used with the Meshy API.",
  agent=asset_designer
)

generate_asset_task = Task(
  description="""Using the detailed prompt from the 3D Asset Designer, generate the 3D asset using the Meshy API.
  After submitting the request, monitor the status of the asset generation until it is complete.
  The final output should be the asset ID and its final status.""",
  expected_output="The Meshy asset ID and a confirmation that the asset generation is complete.",
  agent=meshy_operator
)
