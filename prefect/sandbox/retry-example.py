from prefect import task, flow
import random
import time

# Task 1: Simulates a task that always succeeds
@task
def task_1():
    time.sleep(3)
    print("Task 1: Success")

# Task 2: Simulates a task that fails the first time and succeeds on retry
@task(retries=2, retry_delay_seconds=3)
def task_2():
    if random.random() < 0.66:
        print("Task 2: Failed, retrying...")
        raise Exception("Task 2 failed, triggering retry.")
    else:
        print("Task 2: Success")

# Define the flow
@flow(name="retry-example", log_prints=True)
def pipeline():
    t1 = task_1()
    t2 = task_2()

# Run the flow
if __name__ == "__main__":
    pipeline()
