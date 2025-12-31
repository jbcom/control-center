from crewai import Crew, Process
from .agents import asset_designer, meshy_operator
from .tasks import design_prompt_task, generate_asset_task

# Define the crew
asset_generation_crew = Crew(
  agents=[asset_designer, meshy_operator],
  tasks=[design_prompt_task, generate_asset_task],
  process=Process.sequential,  # Sequential process for this workflow
  verbose=2,
)

def run_crew(concept: str):
    """
    Kicks off the asset generation crew with a high-level concept.
    """
    inputs = {'concept': concept}
    result = asset_generation_crew.kickoff(inputs=inputs)
    return result

if __name__ == '__main__':
    # Example usage:
    # This would typically be called from another part of the strata library
    # For now, we'll just print the result of a sample run.
    concept = "A futuristic, low-poly sword with glowing blue runes"
    print(f"Running asset generation crew for concept: {concept}")
    crew_result = run_crew(concept)
    print("\n\n########################")
    print("## Crew Execution Result:")
    print("########################")
    print(crew_result)
