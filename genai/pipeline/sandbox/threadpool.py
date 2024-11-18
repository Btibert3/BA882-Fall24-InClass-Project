# threadpool concurrency
# will also force me to re-login after a full sweep of the shell

##

## resources: 
## https://docs.prefect.io/3.0/develop/task-runners#configure-a-task-runner

from prefect import flow, task
from prefect.futures import wait
from prefect.task_runners import ThreadPoolTaskRunner
import time

## NOTE:
## didn't have to do this before, IIRC, but need to set the prefect local variable
## prefect config set PREFECT_API_URL=http://127.0.0.1:4200/api. <--- which shows after prefect server start
## then run the script


@task
def stop_at_floor(floor):
    print(f"elevator moving to floor {floor}")
    time.sleep(floor)
    print(f"elevator stops on floor {floor}")


@flow(task_runner=ThreadPoolTaskRunner(max_workers=3), log_prints=True)
def elevator():
    floors = []

    for floor in range(10, 0, -1):
        floors.append(stop_at_floor.submit(floor))

    wait(floors)

# the job
if __name__ == "__main__":
    elevator()



######### test


# from prefect import flow

# @flow
# def my_flow():
#     print("Running a local Prefect flow!")

# if __name__ == "__main__":
#     my_flow()