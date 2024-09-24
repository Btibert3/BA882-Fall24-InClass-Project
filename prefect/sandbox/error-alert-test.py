# this should trigger the failure and then the mamanged Slack post to Webhoook
from prefect import flow, task

# Task that will succeed
@task
def success_task():
    print("This task succeeds!")

# Task that will fail
@task
def fail_task():
    print("This task will fail...")
    raise ValueError("Something went wrong!")

# Flow that runs the tasks
@flow
def example_flow():
    success_task()  # This will run fine
    fail_task()     # This will raise an error

if __name__ == "__main__":
    example_flow()