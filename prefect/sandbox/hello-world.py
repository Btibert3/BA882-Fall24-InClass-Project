from prefect import flow, task

# Define the first task
@task
def task_one():
    print("Executing Task One")

# Define the second task
@task
def task_two():
    print("Executing Task Two")

# Define the flow that calls the tasks
@flow
def simple_flow():
    task_one()
    task_two()

# Run the flow
if __name__ == "__main__":
    simple_flow()