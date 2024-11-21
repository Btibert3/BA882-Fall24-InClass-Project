from prefect import flow

if __name__ == "__main__":
    flow.from_source(
        source="https://github.com/Btibert3/BA882-Fall24-InClass-Project.git",
        entrypoint="prefect/flows/ml-views.py:ml_datasets",
    ).deploy(
        name="ml-datasets",
        work_pool_name="brock-pool1",
        job_variables={"env": {"BROCK": "loves-to-code"},
                       "pip_packages": ["pandas==2.2.3", "requests==2.32.3"]},
        cron="20 0 * * *",
        tags=["prod"],
        description="The pipeline to create ML datasets off of the staged data.  Version is just for illustration",
        version="1.0.0",
    )