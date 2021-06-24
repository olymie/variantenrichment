from config.celery_app import app
from .processes import assemble_case_sample, filter_samples, count_statistics
from .models import BackgroundJob, VariantFile


@app.task
def process_task(bj_id):
    bj = BackgroundJob.objects.get(pk=bj_id)
    bj.state = "running"
    bj.save()

    project = bj.project
    case_annotated = assemble_case_sample(project)

    if (project.state == "cadd-annotated") or not project.cadd_score:
        bj.state = "done"
        bj.save()

        bj_new = BackgroundJob(
            name="Filtering",
            project=bj.project,
            state="new"
        )
        bj_new.save()
        filter_task.apply_async(args=[bj_new.pk, case_annotated], countdown=1)

    # return scores


@app.task
def filter_task(bj_id, case_vcf):
    bj = BackgroundJob.objects.get(pk=bj_id)
    bj.state = "running"
    bj.save()

    (case_filtered, control_filtered, genes_dict) = filter_samples(project=bj.project, case_file=case_vcf)

    print(case_filtered, control_filtered, genes_dict)

    scores = count_statistics(project=bj.project,
                              case_file=case_filtered,
                              control_file=control_filtered,
                              genes_dict=genes_dict)

    bj.state = "done"
    bj.save()
    return scores


# @app.task
# def stats_task(bj_id)
