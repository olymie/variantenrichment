from time import sleep
from .models import Project, VariantFile, ProjectFiles
from .functions import get_directory, merge_files, annotate_sample, \
    filter_by_gene, filter_by_impact_frequency, filter_file, \
    get_genes_dict, count_variants, find_fisher_scores, \
    post_file_cadd, save_cadd_file, add_cadd_annotations, filter_by_cadd

FILES_DIR = "variantenrichment/data/projects/"
DB_FILE = "variantenrichment/data/hg19_refseq_curated.ser"
FASTA_FILE = "variantenrichment/data/hs37d5.fa"
GNOMAD_EXOMES_FILE = "variantenrichment/data/gnomad.exomes.r2.0.2.sites.vcf.gz"


def assemble_case_sample(project: Project):
    """ merges and annotates vcf files provided by user
    :param project: Project object for which the annotation should be done
    :return: name of the merged and annotated vcf file
    """
    project.state = "annotating"
    project.save()

    project_files_dir = get_directory(FILES_DIR + str(project.uuid))
    vcf_files = [
        'variantenrichment/media/' + str(vcf.uploaded_file) for vcf in VariantFile.objects.filter(project=project)
    ]

    merged = merge_files(vcf_files=vcf_files,
                         output_file=project_files_dir + "/case")

    annotated = annotate_sample(vcf_file=merged,
                                fasta_file=FASTA_FILE,
                                gnomad_file=GNOMAD_EXOMES_FILE,
                                db_file=DB_FILE,
                                output_file=project_files_dir + "/case.annotated")

    project_files, created = ProjectFiles.objects.get_or_create(project=project)
    project_files.case_annotated = annotated
    project_files.save()


def filter_samples(project: Project):
    project.state = "filtering"
    project.save()

    project_files_dir = get_directory(FILES_DIR + str(project.uuid))
    project_files = ProjectFiles.objects.get(project=project)
    case_file = project_files.case_annotated

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

    # post filtered vcf files to cadd server if user provided cadd cutoff value
    if project.cadd_score:
        project_files.cadd_case_id = post_file_cadd(vcf_file=case_file)
        project_files.cadd_control_id = post_file_cadd(vcf_file=control_file)
        project_files.save()

        project.state = "cadd-waiting"
        project.save()

    project_files.case_filtered, project_files.control_filtered = case_file, control_file
    project_files.save()


def count_statistics(project: Project):
    project.state = "analyzing"
    project.save()

    project_files_dir = get_directory(FILES_DIR + str(project.uuid))
    project_files = ProjectFiles.objects.get(project=project)

    genes_dict = get_genes_dict('variantenrichment/media/' + str(project.inheritance))

    case_csv = count_variants(vcf_file=project_files.case_filtered,
                              genes=genes_dict,
                              output_file=project_files_dir + "/case")

    control_csv = count_variants(vcf_file=project_files.control_filtered,
                                 genes=genes_dict,
                                 output_file=project_files_dir + "/control")

    project_files.scores_csv = find_fisher_scores(csv_case=case_csv,
                                                  csv_control=control_csv,
                                                  output_file=project_files_dir + "/scores")

    project_files.case_csv, project_files.control_csv = case_csv, control_csv
    project_files.save()

    project.state = "done"
    project.save()


def check_cadd(project: Project):
    project.state = "cadd-checking"
    project.save()

    project_files_dir = get_directory(FILES_DIR + str(project.uuid))
    project_files = ProjectFiles.objects.get(project=project)

    if not project_files.cadd_case:
        project_files.cadd_case = save_cadd_file(cadd_id=project_files.cadd_case_id,
                                                 output_file=project_files_dir + "/case")

    if not project_files.cadd_control:
        project_files.cadd_control = save_cadd_file(cadd_id=project_files.cadd_control_id,
                                                    output_file=project_files_dir + "/control")
    project_files.save()

    return project_files.cadd_case and project_files.cadd_control


def cadd_filter_samples(project: Project):
    project.state = "cadd-filtering"
    project.save()

    project_files_dir = get_directory(FILES_DIR + str(project.uuid))
    project_files = ProjectFiles.objects.get(project=project)

    case_file = add_cadd_annotations(vcf_file=project_files.case_filtered,
                                     cadd_file=project_files.cadd_case,
                                     output_file=project_files_dir + "/case.filtered.cadd-annotated")

    control_file = add_cadd_annotations(vcf_file=project_files.control_filtered,
                                        cadd_file=project_files.cadd_control,
                                        output_file=project_files_dir + "/control.filtered.cadd-annotated")

    project_files.case_filtered = filter_by_cadd(vcf_file=case_file,
                                                 cadd_score=project.cadd_score,
                                                 output_file=project_files_dir + "/case.cadd-filtered")

    project_files.control_filtered = filter_by_cadd(vcf_file=control_file,
                                                    cadd_score=project.cadd_score,
                                                    output_file=project_files_dir + "/control.cadd-filtered")

    project_files.save()
