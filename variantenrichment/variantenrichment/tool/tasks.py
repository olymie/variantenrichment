from config.celery_app import app


# test tasks
@app.task
def add(x, y):
    return x + y


@app.task
def mul(x, y):
    return x * y
