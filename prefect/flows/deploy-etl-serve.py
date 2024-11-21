from prefect import flow

if __name__ == "__main__":
    flow.from_source(
        source="https://github.com/Btibert3/BA882-Fall24-InClass-Project.git",
        entrypoint="prefect/flows/etl.py:etl_flow",
    ).serve(
        name="aws-blogs-etl2",
        # work_pool_name="brock-pool1",
        # job_variables={"env": {"BROCK": "loves-to-code"},
        #                "pip_packages": ["pandas", "requests"]},
        cron="15 0 * * *",
        tags=["prod"],
        description="The pipeline to populate the stage schema with the newest posts.  Version is just for illustration",
        version="1.0.0",
    )