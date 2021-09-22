import subprocess
import re
import sys
import requests
from os import path
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import vcfpy as vp
import scipy.stats as stats
import matplotlib.pyplot as plt


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
                if not vcf.endswith(".gz"):
                    subprocess.run([
                        "bgzip", "-f", vcf
                    ])
                    vcf += ".gz"

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

    else:
        vcf_content = subprocess.check_output([
            "zcat", vcf_files[0]
        ])

        with open("tmp.vcf", "w+") as tmp_file:
            tmp_file.write(vcf_content.decode())

    normalized = normalize_sample("tmp.vcf", output_file)

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
    ], check=True)

    print("Done with Jannovar, tabix is next", file=sys.stderr)

    subprocess.run([
        "tabix", "-p", "vcf", output_file + ".vcf.gz"
    ], check=True)

    print("Done with tabix, result is %s" % (output_file + ".vcf.gz"), file=sys.stderr)

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


def filter_by_frequency(vcf_file, frequency, output_file):
    """ filters variant file by frequency
        :param vcf_file: variant file
        :param frequency: variant frequency in population
        :param output_file: name of an output file WITHOUT SUFFICES
        :return: string: output file name with the right extension
    """

    freq_str = 'INFO/GNOMAD_EXOMES_AF_ALL = "." || INFO/GNOMAD_EXOMES_AF_ALL < ' + str(frequency)
    print(freq_str)

    subprocess.run([
        "bcftools", "filter", "-i",
        freq_str,
        "-o", output_file + ".vcf", vcf_file
    ])

    return output_file + ".vcf"


def filter_by_impact(vcf_file, impact, impact_mod, genes_mod, output_file):
    impact_str = 'INFO/ANN ~ "|HIGH|"'

    if impact == "synonymous_variant":
        impact_str = 'INFO/ANN ~ "|' + impact + '|"'

    elif not len(genes_mod):
        if impact != "HIGH":
            impact_str += ' || INFO/ANN ~ "|MODERATE|"'

    elif impact == "MODERATE" and impact_mod == "HIGH":
        for gene in genes_mod:
            impact_str += ' || (INFO/ANN ~ "|MODERATE|" && INFO/ANN !~ "|' + gene + '|")'

    elif impact == "HIGH" and impact_mod == "MODERATE":
        for gene in genes_mod:
            impact_str += ' || (INFO/ANN ~ "|MODERATE|" && INFO/ANN ~ "|' + gene + '|")'

    print("FILTER BY IMPACT:", impact_str)

    subprocess.run([
        "bcftools", "filter", "-i",
        impact_str,
        "-o", output_file + ".vcf", vcf_file
    ])

    return output_file + ".vcf"


def filter_population(vcf_file, samples_file, population, output_file):
    samples_df = pd.read_csv(samples_file,
                             delimiter="\t",
                             header=0,
                             usecols=["Sample name", "Superpopulation code"],
                             index_col=None)

    samples_filtered = samples_df[samples_df["Superpopulation code"].isin(population)]["Sample name"]
    samples_filtered.to_csv("sample_names.txt", index=False, header=False)

    subprocess.run([
        "bcftools", "view", "-S", "sample_names.txt", "-c1", "--force-samples", "-o", output_file + ".vcf", vcf_file
    ])

    # subprocess.run([
    #     "rm", "sample_names.txt"
    # ])

    return output_file + ".vcf"


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


def is_interesting(ann, genes_names, impact_def, impact_mod, impact_position):
    """ checks if the given annotation includes right gene name and impact
        :param ann: element of record.INFO['ANN'] list of jannovar annotations
        :param genes_names: list of genes names on which to look for variants
        :param impact_def: default impact defined by user
        :param impact_mod: an exception impact defined by user for a group of genes
        :param impact_position: position of impact value in ANN string to use for filtering
            2: LOW/MODERATE/HIGH
            1: synonymous_variant
        :return: boolean value
    """
    ann_list = ann.split('|')

    impact = ann_list[impact_position]
    if impact not in [impact_def, impact_mod]:
        return False

    gene = ann_list[3]
    if gene not in genes_names:
        return False

    return True


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

    # position of impact value in ANN string to use for filtering
    # 2: LOW/MODERATE/HIGH
    # 1: synonymous_variant
    impact_position = 1 if impact == "synonymous_variant" else 2

    for record in reader:
        annotations = record.INFO['ANN']
        # leave only annotations for "interesting" genes and impact
        record.INFO['ANN'][:] = [
            ann for ann in annotations
            if is_interesting(ann, genes_names, impact, impact_mod, impact_position)
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

                # don't count heterozygous variants if they're inherited recessively
                if call.is_het and genes[gene_name] != 'Autosomal dominant':
                    continue

                df[call.sample][gene_name] += 1
                # only "1" values for gen-wise collapsed table
                df_collapse[call.sample][gene_name] = 1

    # make two different tables (normal and gen-wise collapsed)
    df.to_csv(output_file + '.csv')
    df_collapse.to_csv(output_file + '.collapsed.csv')

    return output_file + '.collapsed.csv'


CADD_URL = "https://cadd.gs.washington.edu/"
CADD_URL_UPLOAD = CADD_URL + "upload"


def post_file_cadd(vcf_file):
    if not vcf_file.endswith(".gz"):
        vcf_compressed = subprocess.check_output([
            "bgzip", "-c", vcf_file
        ])
        with open(vcf_file + ".gz", "wb+") as tmp_file:
            tmp_file.write(vcf_compressed)
        vcf_file += ".gz"

    try:
        file = {"file": open(vcf_file, "rb")}

        data = {
            "version": "GRCh37-v1.6",
            "inclAnno": "No",
            "submit": "Upload variants",
        }

        r = requests.post(CADD_URL_UPLOAD, data=data, files=file)

        soup = BeautifulSoup(r.text, "html.parser")
        p_success = soup.find("p", string=re.compile("You successfully uploaded"))
        print(p_success)
        link_parts = p_success.find_next_sibling("p").find("a")["href"].split("/")
        return link_parts[len(link_parts) - 1]

    except Exception as e:
        print("error:", e)
        return ""


def save_cadd_file(cadd_id, output_file):
    cadd_file_url = CADD_URL + "static/finished/" + cadd_id

    if requests.head(cadd_file_url).status_code == 200:
        cadd_scores = requests.get(cadd_file_url)

        with open(output_file + ".tsv.gz", "wb") as tsv_file:
            tsv_file.write(cadd_scores.content)

        subprocess.run([
            "bgzip", "-d", "-f", output_file + ".tsv.gz"
        ])

        return output_file + ".tsv"

    else:
        print("try again later, sorry")
        return ""


def add_cadd_annotations(vcf_file, cadd_file, output_file):
    reader = vp.Reader.from_path(vcf_file)
    reader.header.add_info_line(vp.OrderedDict([
        ("ID", "CADDRS"), ("Number", "1"), ("Type", "Float"), ("Description", "CADD raw score")
    ]))
    reader.header.add_info_line(vp.OrderedDict([
        ("ID", "CADDPHRED"), ("Number", "1"), ("Type", "Float"), ("Description", "CADD PHRED-scaled score")
    ]))
    writer = vp.Writer.from_path(output_file + ".vcf", reader.header)

    cadd_df = pd.read_csv(cadd_file,
                          delimiter="\t",
                          header=1,
                          index_col=None)
    cadd_df["#Chrom"] = cadd_df["#Chrom"].astype(str)
    cadd_line_num = 0
    cadd_len = len(cadd_df)

    for record in reader:
        counter = 0
        cadd_line = cadd_df.iloc[cadd_line_num]

        while record.CHROM != cadd_line["#Chrom"] or record.POS != cadd_line["Pos"]:
            cadd_line_num = (cadd_line_num + 1) % cadd_len
            cadd_line = cadd_df.iloc[cadd_line_num]
            counter += 1

            if counter == cadd_len:
                print("made a round, not found")
                record.INFO["CADDRS"] = "."
                record.INFO["CADDPHRED"] = "."
                writer.write_record(record)
                break

        if counter == cadd_len:
            continue

        record.INFO["CADDRS"] = cadd_line["RawScore"]
        record.INFO["CADDPHRED"] = cadd_line["PHRED"]
        cadd_line_num = (cadd_line_num + 1) % cadd_len
        writer.write_record(record)

    return output_file + ".vcf"


def filter_by_cadd(vcf_file, cadd_score, output_file):
    subprocess.run([
        "bcftools", "filter", "-i",
        'INFO/CADDPHRED = "." || INFO/CADDPHRED >= ' + str(cadd_score),
        "-o", output_file + ".vcf", vcf_file
    ])

    return output_file + ".vcf"


def find_fisher_scores(csv_case, csv_control, output_file):
    case_df = pd.read_csv(csv_case,
                          header=0,
                          index_col=0)
    control_df = pd.read_csv(csv_control,
                             header=0,
                             index_col=0)

    score_df = pd.DataFrame(index=case_df.index.values,
                            columns=["case_pos", "case_neg", "control_pos", "control_neg", "p"])

    score_df["case_pos"] = case_df.sum(axis=1)
    score_df["case_neg"] = len(case_df.columns) - score_df["case_pos"]
    score_df["control_pos"] = control_df.sum(axis=1)
    score_df["control_neg"] = len(control_df.columns) - score_df["control_pos"]

    pvalues = []

    for index, row in score_df.iterrows():
        oddratio, pvalue = stats.fisher_exact([
            [row["case_pos"], row["case_neg"]],
            [row["control_pos"], row["control_neg"]]
        ])
        pvalues.append(pvalue)

    score_df["p"] = pvalues
    score_df = score_df.sort_values("p")
    score_df.to_csv(output_file + '.csv')

    return output_file + '.csv'


def visualize_p_values(scores_file, output_file):
    scores_df = pd.read_csv(scores_file,
                            header=0,
                            index_col=0)
    p_obs = -np.log10(scores_df["p"])
    p_exp = -np.log10(np.linspace(0, 1, num=len(p_obs) + 1, endpoint=False)[1:])
    save_qq_plot(p_exp, p_obs, output_file + ".png")

    return output_file + ".png"


def save_qq_plot(x_sample, y_sample, output_file):
    plt.xlim(0, 1)
    plt.ylim(0, 1)
    fig, ax = plt.subplots()
    ax.scatter(x_sample, y_sample, color="royalblue")
    ax.plot([x_sample[0], x_sample[len(x_sample)-1]], [x_sample[0], x_sample[len(x_sample)-1]], color="dimgrey", ls="dashed")
    fig.savefig(output_file, bbox_inches='tight')

