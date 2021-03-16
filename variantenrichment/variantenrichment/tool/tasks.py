from config.celery_app import app
from .processes import change_project_state
from .models import BackgroundJob

# test tasks
@app.task
def change_project_state_task(bj_id):
    bj = BackgroundJob.objects.get(pk=bj_id)
    return change_project_state(bj)
