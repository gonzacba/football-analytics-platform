import subprocess
import os
from prefect import flow, task, get_run_logger


DBT_PROJECT_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "02_dbt_models"
)


@task(name="dbt-run", retries=1, retry_delay_seconds=30)
def run_dbt_models() -> dict:
    """Run all dbt models."""
    logger = get_run_logger()
    logger.info("Running dbt models...")

    result = subprocess.run(
        ["dbt", "run"],
        cwd=DBT_PROJECT_DIR,
        capture_output=True,
        text=True
    )

    logger.info(result.stdout)
    if result.returncode != 0:
        logger.error(result.stderr)
        raise Exception(f"dbt run failed: {result.stderr}")

    logger.info("dbt run completed successfully")
    return {"status": "success", "output": result.stdout}


@task(name="dbt-test", retries=1, retry_delay_seconds=10)
def run_dbt_tests() -> dict:
    """Run all dbt tests."""
    logger = get_run_logger()
    logger.info("Running dbt tests...")

    result = subprocess.run(
        ["dbt", "test"],
        cwd=DBT_PROJECT_DIR,
        capture_output=True,
        text=True
    )

    logger.info(result.stdout)
    if result.returncode != 0:
        logger.error(result.stderr)
        raise Exception(f"dbt test failed: {result.stderr}")

    logger.info("dbt tests passed")
    return {"status": "success", "output": result.stdout}


@task(name="dbt-source-freshness")
def check_source_freshness() -> dict:
    """Check dbt source freshness."""
    logger = get_run_logger()
    logger.info("Checking source freshness...")

    result = subprocess.run(
        ["dbt", "source", "freshness"],
        cwd=DBT_PROJECT_DIR,
        capture_output=True,
        text=True
    )

    logger.info(result.stdout)
    return {"status": "complete", "output": result.stdout}


@flow(name="soccer-transform-flow", log_prints=True)
def transform_flow(run_tests: bool = True):
    """
    dbt transformation flow.
    Runs all dbt models and optionally runs tests.
    """
    logger = get_run_logger()
    logger.info("Starting transformation flow")

    # Run dbt models
    run_result = run_dbt_models()
    logger.info(f"dbt run status: {run_result['status']}")

    # Run tests if requested
    if run_tests:
        test_result = run_dbt_tests()
        logger.info(f"dbt test status: {test_result['status']}")

    logger.info("Transformation flow complete")
    return run_result


if __name__ == "__main__":
    transform_flow(run_tests=True)