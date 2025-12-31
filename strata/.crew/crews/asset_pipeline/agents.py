from crewai import Agent
from .tools import meshy_text_to_asset_tool, meshy_asset_status_tool

# Define the agents
asset_designer = Agent(
  role='3D Asset Designer',
  goal='Generate creative and detailed prompts for 3D asset creation based on high-level concepts.',
  backstory="""You are a visionary 3D asset designer with a knack for translating abstract ideas into detailed, actionable prompts for AI-powered 3D model generation.
  You understand the nuances of 3D modeling and can articulate specific requirements for textures, polygons, and art style.""",
  verbose=True,
  allow_delegation=False,
)

meshy_operator = Agent(
  role='Meshy API Operator',
  goal='Take a detailed 3D asset prompt and use the Meshy API to generate the asset. You will then monitor the status of the generation until it is complete.',
  backstory="""You are an expert in using the Meshy API for 3D asset generation.
  You are responsible for submitting the generation requests and ensuring that the process completes successfully.
  You are meticulous and detail-oriented, ensuring that all API calls are made correctly.""",
  verbose=True,
  allow_delegation=False,
  tools=[meshy_text_to_asset_tool, meshy_asset_status_tool],
)
