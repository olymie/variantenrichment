from config.celery_app import app
from .processes import assemble_case_sample, filter_samples_initial, filter_samples_final, \
    check_quality, count_statistics, check_cadd, cadd_filter_samples
from .models import BackgroundJob


@app.task
def annotate_task(bj_id):
    bj = BackgroundJob.objects.get(pk=bj_id)
    bj.state = "running"
    bj.save()

    assemble_case_sample(bj.project)

    bj.state = "done"
    bj.save()

    bj_new = BackgroundJob(
        name="Initial filtering",
        project=bj.project,
        state="new"
    )
    bj_new.save()
    prefilter_task.apply_async(args=[bj_new.pk], countdown=1)


@app.task
def prefilter_task(bj_id):
    bj = BackgroundJob.objects.get(pk=bj_id)
    bj.state = "running"
    bj.save()

    filter_samples_initial(project=bj.project)

    bj.state = "done"
    bj.save()

    bj_new = BackgroundJob(
        name="Quality checking",
        project=bj.project,
        state="new"
    )
    bj_new.save()
    check_quality_task.apply_async(args=[bj_new.pk], countdown=1)


@app.task
def filter_task(bj_id):
    bj = BackgroundJob.objects.get(pk=bj_id)
    bj.state = "running"
    bj.save()

    filter_samples_final(project=bj.project)

    bj.state = "done"
    bj.save()

    if not bj.project.cadd_score:
        bj_new = BackgroundJob(
            name="Analyzing",
            project=bj.project,
            state="new"
        )
        bj_new.save()
        stats_task.apply_async(args=[bj_new.pk], countdown=1)

    elif check_cadd(project=bj.project):
        bj_new = BackgroundJob(
            name="CADD filtering",
            project=bj.project,
            state="new"
        )
        bj_new.save()
        filter_cadd_task.apply_async(args=[bj_new.pk], countdown=1)


@app.task
def check_quality_task(bj_id):
    bj = BackgroundJob.objects.get(pk=bj_id)
    bj.state = "running"
    bj.save()

    check_quality(project=bj.project)

    bj.state = "done"
    bj.save()

    bj_new = BackgroundJob(
        name="Filtering",
        project=bj.project,
        state="new"
    )
    bj_new.save()
    filter_task.apply_async(args=[bj_new.pk], countdown=1)


@app.task
def stats_task(bj_id):
    bj = BackgroundJob.objects.get(pk=bj_id)
    bj.state = "running"
    bj.save()

    count_statistics(project=bj.project)

    bj.state = "done"
    bj.save()


@app.task
def check_cadd_task(bj_id):
    bj = BackgroundJob.objects.get(pk=bj_id)
    bj.state = "running"
    bj.save()

    cadd_ready = check_cadd(project=bj.project)

    bj.state = "done"
    bj.save()

    if cadd_ready:
        bj_new = BackgroundJob(
            name="CADD filtering",
            project=bj.project,
            state="new"
        )
        bj_new.save()
        filter_cadd_task.apply_async(args=[bj_new.pk], countdown=1)
    else:
        print("try again later")


@app.task
def filter_cadd_task(bj_id):
    bj = BackgroundJob.objects.get(pk=bj_id)
    bj.state = "running"
    bj.save()

    cadd_filter_samples(project=bj.project)

    bj.state = "done"
    bj.save()

    bj_new = BackgroundJob(
        name="Analyzing",
        project=bj.project,
        state="new"
    )
    bj_new.save()
    stats_task.apply_async(args=[bj_new.pk], countdown=1)
