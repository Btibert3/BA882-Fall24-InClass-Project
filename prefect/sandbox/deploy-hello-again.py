from prefect import flow

if __name__ == "__main__":
    flow.from_source(
        source="https://github.com/Btibert3/BA882-Fall24-InClass-Project.git",
        entrypoint="prefect/sandbox/hello-again.py:simple_again",
    ).deploy(
        name="hello-again",
        work_pool_name="brock-worker1",
        job_variables={"env": {"BROCK": "loves-to-code"},
                       "pip_packages": ["pandas", "requests"]},
        cron="0 * * * *",
        tags=["poc"],
        description="A simple flow to greet the world",
        version="1.0.0",
    )