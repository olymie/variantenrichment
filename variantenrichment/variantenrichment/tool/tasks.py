from config.celery_app import app
from .processes import assemble_case_sample, filter_samples, count_statistics
from .models import BackgroundJob, VariantFile


@app.task
def process_task(bj_id):
    bj = BackgroundJob.objects.get(pk=bj_id)
    bj.state = "running"
    bj.save()

    case_annotated = assemble_case_sample(project=bj.project)

    (case_filtered, control_filtered, genes_dict) = filter_samples(project=bj.project, case_file=case_annotated)

    scores = count_statistics(project=bj.project,
                              case_file=case_filtered,
                              control_file=control_filtered,
                              genes_dict=genes_dict)

    bj.state = "done"
    bj.save()

    return scores
