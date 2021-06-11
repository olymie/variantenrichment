from time import sleep
from .models import Project, VariantFile
from .functions import get_directory, merge_files, annotate_sample, filter_by_gene, filter_by_impact_frequency, filter_file, get_genes_dict, count_variants, find_fisher_scores, post_file_cadd, save_cadd_file

FILES_DIR = "variantenrichment/data/projects/"
DB_FILE = "variantenrichment/data/hg19_refseq_curated.ser"
FASTA_FILE = "variantenrichment/data/hs37d5.fa"
GNOMAD_EXOMES_FILE = "variantenrichment/data/gnomad.exomes.r2.0.2.sites.vcf.gz"


def assemble_case_sample(project: Project):
    """ merges and annotates vcf files provided by user
    :param project: Project object for which the annotation should be done
    :return: name of the merged and annotated vcf file
    """
    project_files_dir = get_directory(FILES_DIR + str(project.uuid))
    vcf_files = [
        'variantenrichment/media/' + str(vcf.uploaded_file) for vcf in VariantFile.objects.filter(project=project)
    ]

    project.state = "annotating"
    project.save()

    merged = merge_files(vcf_files=vcf_files,
                         output_file=project_files_dir + "/case")

    if project.cadd_score:
        project.cadd_job = post_file_cadd(vcf_file=merged)

    annotated = annotate_sample(vcf_file=merged,
                                fasta_file=FASTA_FILE,
                                gnomad_file=GNOMAD_EXOMES_FILE,
                                db_file=DB_FILE,
                                output_file=project_files_dir + "/case.annotated")

    project.state = "annotated"

    if project.cadd_score:

        project.cadd_job = save_cadd_file(cadd_id=project.cadd_job,
                                          output_file=project_files_dir + "/case_cadd")

        if project.cadd_job == "done":
            project.state = "cadd-annotated"
        elif project.cadd_job:
            project.state = "cadd-annotating"

    project.save()

    return annotated


def filter_samples(project: Project, case_file):
    project_files_dir = get_directory(FILES_DIR + str(project.uuid))
    project.state = "analysing"
    project.save()

    control_file = str(project.background.file)
    genes = project.genes

    # filter case and control files by user provided genes.bed with chromosomes and position numbers
    if genes:
        genes = 'variantenrichment/media/' + str(genes)
        case_file = filter_by_gene(vcf_file=case_file,
                                   gene_file=genes,
                                   output_file=project_files_dir + "/case.gene_filtered")

        control_file = filter_by_gene(vcf_file=control_file,
                                      gene_file=genes,
                                      output_file=project_files_dir + "/control.gene_filtered")

    # prepare the list of gene names set up as genes with a different impact by user
    genes_exception = project.genes_exception

    if genes_exception:
        genes_exception = genes_exception.split(",")

    # filter case and control files by values set up by user
    case_file = filter_by_impact_frequency(vcf_file=case_file,
                                           impact=project.impact,
                                           impact_mod=project.impact_exception,
                                           genes_mod=genes_exception,
                                           frequency=project.frequency,
                                           output_file=project_files_dir + "/case.frequency_filtered")

    control_file = filter_by_impact_frequency(vcf_file=control_file,
                                              impact=project.impact,
                                              impact_mod=project.impact_exception,
                                              genes_mod=genes_exception,
                                              frequency=project.frequency,
                                              output_file=project_files_dir + "/control.frequency_filtered")

    # prepare a dictionary with gene names and inheritance models from the file provided by user
    genes_dict = get_genes_dict('variantenrichment/media/' + str(project.inheritance))

    # only leave genes which are mentioned in inheritance file + remove variants on X-linked genes
    case_file = filter_file(vcf_file=case_file,
                            genes_names=genes_dict.keys(),
                            impact=project.impact,
                            impact_mod=project.impact_exception,
                            output_file=project_files_dir + "/case.filtered")

    control_file = filter_file(vcf_file=control_file,
                               genes_names=genes_dict.keys(),
                               impact=project.impact,
                               impact_mod=project.impact_exception,
                               output_file=project_files_dir + "/control.filtered")

    return case_file, control_file, genes_dict


def count_statistics(project: Project, case_file, control_file, genes_dict):
    project_files_dir = get_directory(FILES_DIR + str(project.uuid))

    project.state = "computing"
    project.save()

    case_csv = count_variants(vcf_file=case_file,
                              genes=genes_dict,
                              output_file=project_files_dir + "/case")

    control_csv = count_variants(vcf_file=control_file,
                                 genes=genes_dict,
                                 output_file=project_files_dir + "/control")

    scores_csv = find_fisher_scores(csv_case=case_csv,
                                    csv_control=control_csv,
                                    output_file=project_files_dir + "/scores")

    project.state = "done"
    project.save()

    return scores_csv
