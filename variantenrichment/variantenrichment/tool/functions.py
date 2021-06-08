import subprocess
from os import path
import numpy as np
import pandas as pd
import vcfpy as vp


def get_directory(path_to_dir):
    """ creates a directory if it doesn't exist
        :param path_to_dir: a path to check on
        :return: a created directory or an existing one with the given path
    """
    if not path.exists(path_to_dir):
        subprocess.run([
            "mkdir", "-p",
            path_to_dir
        ])
    return path_to_dir


def merge_files(vcf_files, output_file):
    """ merges multiple vcf files into one
        :param vcf_files: list of vcf files' names to merge
        :param output_file: name of an output file WITHOUT SUFFICES
        :return: output file name with the right extension
    """

    if len(vcf_files) > 1:
        names_file = "file_names.txt"
        with open(names_file, "w") as file:
            for vcf in vcf_files:
                subprocess.run([
                    "tabix", "-p", "vcf", vcf
                ])
                file.write(vcf + '\n')

        subprocess.run([
            "bcftools", "merge", "-0", "-l", names_file, "-m", "none", "-o", "tmp.vcf"
        ])

        subprocess.run([
            "rm", names_file
        ])

        vcf_merged = "tmp.vcf"

    else:
        vcf_merged = vcf_files[0]

    normalized = normalize_sample(vcf_merged, output_file)

    subprocess.run([
        "rm", "tmp.vcf"
    ])

    return normalized


def normalize_sample(vcf_file, output_file):
    """ sorts and normalizes the variant file
        :param vcf_file: variant file.
        :param output_file: name of an output file WITHOUT SUFFICES
        :return: output file name with the right extension
    """

    subprocess.run([
        "bcftools", "sort", "-o", vcf_file, vcf_file
    ])

    subprocess.run([
        "bcftools", "norm", "-d", "none", "-o", output_file + ".vcf", vcf_file
    ])

    subprocess.run([
        "bgzip", "-f", output_file + ".vcf"
    ])

    subprocess.run([
        "tabix", "-f", "-p", "vcf", output_file + ".vcf.gz"
    ])

    return output_file + ".vcf.gz"


def annotate_sample(vcf_file, fasta_file, gnomad_file, db_file, output_file):
    """ annotates the variant file
        :param vcf_file: variant file
        :param fasta_file: reference fasta file for annotating
        :param gnomad_file: vcf with gnomad exomes
        :param db_file: reference database
        :param output_file: name of an output file WITHOUT SUFFICES
        :return: output file name with the right extension
    """

    subprocess.run([
        "jannovar",
        "annotate-vcf",
        "--show-all",
        "--ref-fasta", fasta_file,
        "--gnomad-exomes-vcf", gnomad_file,
        "-d", db_file,
        "-i", vcf_file,
        "-o", output_file + ".vcf.gz"
    ])

    subprocess.run([
        "tabix", "-p", "vcf", output_file + ".vcf.gz"
    ])

    return output_file + ".vcf.gz"


def filter_by_gene(vcf_file, gene_file, output_file):
    """ filters vcf_file to only include variations on given positions
        :param vcf_file: vcf file with listed variants
        :param gene_file: bed file with chr numbers and positions for interesting variations
        :param output_file: name of an output file WITHOUT SUFFICES
        :return: output file name with the right extension
    """
    filtered_variants = subprocess.check_output([
        "tabix", "-R", gene_file, vcf_file
    ])

    header = subprocess.check_output([
        "tabix", "-H", vcf_file
    ])

    with open("tmp.vcf", "w") as o_file:
        o_file.write(header.decode())
        o_file.write(filtered_variants.decode())

    normalized = normalize_sample("tmp.vcf", output_file)

    subprocess.run([
        "rm", "tmp.vcf"
    ])

    return normalized


def filter_by_impact_frequency(vcf_file, impact, impact_mod, genes_mod, frequency, output_file):
    """ filters variant file by impact and frequency
        :param vcf_file: variant file
        :param impact: variant impact HIGH/MODERATE/LOW
        :param impact_mod: a different variant impact for a group of genes
        :param genes_mod: list of gene names for which the impact is impact_mod
        :param frequency: variant frequency in population
        :param output_file: name of an output file WITHOUT SUFFICES
        :return: string: output file name with the right extension
    """

    impact_str = get_impact_str(impact, impact_mod, genes_mod)

    print(impact_str)

    subprocess.run([
        "bcftools", "filter", "-i",
        impact_str,
        "-o", "tmp.vcf", vcf_file
    ])

    subprocess.run([
        "bcftools", "filter", "-i",
        'INFO/GNOMAD_EXOMES_AF_ALL = "." || INFO/GNOMAD_EXOMES_AF_ALL < ' + str(frequency),
        "-o", output_file + ".vcf", "tmp.vcf"
    ])

    subprocess.run([
        "rm", "tmp.vcf"
    ])

    return output_file + ".vcf"


def get_impact_str(impact, impact_mod, genes_mod):
    """ constructs a string for filtering based on defined impact
        :param impact: default variant impact HIGH/MODERATE/LOW
        :param impact_mod: a different variant impact for a group of genes
        :param genes_mod: list of gene names for which the impact is impact_mod
        :return: a string that can be used for filtering by bcftools
    """
    impact_str = 'INFO/ANN ~ "|HIGH|"'

    if not len(genes_mod):
        if impact == "HIGH":
            return impact_str
        else:
            return impact_str + ' || INFO/ANN ~ "|MODERATE|"'

    if impact == "MODERATE" and impact_mod == "HIGH":
        for gene in genes_mod:
            impact_str += ' || (INFO/ANN ~ "|MODERATE|" && INFO/ANN !~ "|' + gene + '|")'

    if impact == "HIGH" and impact_mod == "MODERATE":
        for gene in genes_mod:
            impact_str += ' || (INFO/ANN ~ "|MODERATE|" && INFO/ANN ~ "|' + gene + '|")'

    return impact_str


def get_genes_dict(genes_file):
    """ gets list of genes along with inheritance model from the text file,
        note that genes with x-linked inheritance will be not included in the list
        :param genes_file: tab delimited file with gene codes and their inheritance model
        :return: dictionary {gene name: inheritance model}
        """
    genes = {}

    with open(genes_file, 'r') as file:
        for line in file:
            line_strip = line.strip()

            if line_strip == '':
                continue

            gene_info = line_strip.split('\t')

            # ignore genes with X-linked inheritance
            if gene_info[1].startswith('X'):
                continue

            genes[gene_info[0]] = gene_info[1]

    return genes


def is_interesting(ann, genes_names, impact_def, impact_mod):
    """ checks if the given annotation includes right gene name and impact
        :param ann: element of record.INFO['ANN'] list of jannovar annotations
        :param genes_names: list of genes names on which to look for variants
        :param impact_def: default impact defined by user
        :param impact_mod: an exception impact defined by user for a group of genes
        :return: boolean value
    """
    ann_list = ann.split('|')

    impact = ann_list[2]
    if impact not in [impact_def, impact_mod]:
        return False

    gene = ann_list[3]
    if gene not in genes_names:
        return False

    return True


# comment this function as well
def filter_file(vcf_file, genes_names, impact, impact_mod, output_file):
    """ creates a new vcf file with annotations about "interesting" variants only
        :param vcf_file: jannovar annotated vcf file
        :param genes_names: list of genes names on which to look for variants
        :param impact: default impact defined by user
        :param impact_mod: an exception impact defined by user for a group of genes
        :param output_file: name of an output file WITHOUT SUFFICES
        :return: string: output file name with the right extension
    """
    reader = vp.Reader.from_path(vcf_file)
    writer = vp.Writer.from_path(output_file + ".vcf", reader.header)

    for record in reader:
        annotations = record.INFO['ANN']
        # leave only annotations for "interesting" genes and impact
        record.INFO['ANN'][:] = [
            ann for ann in annotations
            if is_interesting(ann, genes_names, impact, impact_mod)
        ]

        if len(record.INFO['ANN']) != 0:
            writer.write_record(record)

    return output_file + ".vcf"


def get_annotated_genes(annotations):
    """ finds all genes mentioned in one variant annotation
        :param annotations: list of variant record jannovar annotations INFO/ANN
        :return: set of mentioned genes
    """
    genes = set()

    for ann in annotations:
        genes.add(ann.split('|')[3])

    return genes


def count_variants(vcf_file, genes, output_file):
    """ creates two csv files for a vcf file:
        -one with a number of variants pro gene in each sample,
        -the other with 1/0 values: 1 if there are any variations on this gene in this sample, 0 if none
        :param vcf_file: jannovar annotated vcf file
        :param genes: dictionary {gene name: gene inheritance info} with genes on which to look for variants
        :param output_file: name of an output file WITHOUT SUFFICES
        :return: string: output file name with the right extension
    """

    reader = vp.Reader.from_path(vcf_file)
    samples = reader.header.samples.names

    df = pd.DataFrame(
       np.zeros((len(genes), len(samples))),
       dtype=np.dtype("int32"),
       index=genes.keys(),
       columns=samples
    )

    df_collapse = df.copy()

    # if a variant is shared between multiple genes, count it for each one
    for record in reader:
        for gene_name in get_annotated_genes(record.INFO['ANN']):
            for call in record.calls:
                # don't count wild genotypes
                if not call.is_variant:
                    continue

                # don't count heterozygous variants if they're inherited rezessively
                if call.is_het and genes[gene_name] != 'Autosomal dominant':
                    continue

                df[call.sample][gene_name] += 1
                # only "1" values for gen-wise collapsed table
                df_collapse[call.sample][gene_name] = 1

    # make two different tables (normal and gen-wise collapsed)
    df.to_csv(output_file + '.csv')
    df_collapse.to_csv(output_file + '.collapsed.csv')
