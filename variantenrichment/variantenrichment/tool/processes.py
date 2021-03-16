from time import sleep
from .models import BackgroundJob

def change_project_state(bj: BackgroundJob):
    sleep(5)
    bj.state = "running"
    bj.save()

    sleep(10)
    bj.project.state = "done"
    bj.state = "done"
    bj.save()
    bj.project.save()
