from crewai import Crew, Process
from agents import cypress_reviewer, playwright_refactorer
from tasks import build_tasks


def run_pipeline(cypress_code: str, output_path: str, filename: str) -> dict:
    """
    Run the review → refactor pipeline for a single Cypress file.

    Args:
        cypress_code: Raw Cypress test file content.
        output_path: Directory where output files will be written.
        filename: Base name (no extension) for output files.

    Returns:
        dict with keys 'review' and 'playwright' containing the task outputs.
    """
    task_review, task_refactor = build_tasks(cypress_code, output_path, filename)

    crew = Crew(
        agents=[cypress_reviewer, playwright_refactorer],
        tasks=[task_review, task_refactor],
        process=Process.sequential,
        verbose=True,
    )

    result = crew.kickoff(inputs={"cypress_code": cypress_code})

    return {
        "review": task_review.output.raw if task_review.output else "",
        "playwright": task_refactor.output.raw if task_refactor.output else "",
        "result": result,
    }
