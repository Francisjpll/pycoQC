#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#~~~~~~~~~~~~~~IMPORTS~~~~~~~~~~~~~~#
# Standard library imports
import argparse
import sys
import os
import json
import logging
import datetime
import hashlib

# Third party imports
import plotly.offline as py
from jinja2 import Environment, PackageLoader, Template

# Local imports
from pycoQC.pycoQC import pycoQC
from pycoQC.Fast5_to_seq_summary import Fast5_to_seq_summary
from pycoQC.common import pycoQCError, pycoQCWarning, is_readable_file, print_help
from pycoQC import __version__ as package_version
from pycoQC import __name__ as package_name

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# List of current valid plotting methods names
plot_methods = [
    "summary",
    "reads_len_1D",
    "reads_qual_1D",
    "reads_len_qual_2D",
    "output_over_time",
    "len_over_time",
    "qual_over_time",
    "barcode_counts",
    "channels_activity"]

#~~~~~~~~~~~~~~Fast5_to_seq_summary CLI ENTRY POINT~~~~~~~~~~~~~~#
def main_Fast5_to_seq_summary (args=None):
    if args is None:
        args = sys.argv[1:]

    # Define parser object
    parser = argparse.ArgumentParser(
        description ="Fast5_to_seq_summary generate a sequencing summary like file from a directory containing Fast5 files")
    parser.add_argument('--version', '-v', action='version', version="{} v{}".format(package_name, package_version))

    # Define arguments
    parser.add_argument("--fast5_dir", "-f", required=True, type=str,
        help="""Directory containing fast5 files. Can contain multiple subdirectories""")
    parser.add_argument("--seq_summary_fn", "-s", required=True, type=str,
        help="""path of the summary sequencing file where to write the data extracted from the fast5 files""")
    parser.add_argument("--max_fast5", type=int, default=0,
        help="Maximum number of file to try to parse. 0 to deactivate (default: %(default)s)")
    parser.add_argument("--threads", "-t", type=int, default=4,
        help="Total number of threads to use. 1 thread is used for the reader and 1 for the writer. Minimum 3 (default: %(default)s)")
    parser.add_argument("--basecall_id", type=int, default=0,
        help="id of the basecalling group. By default leave to 0, but if you perfome multiple basecalling on the same fast5 files, this can be used to indicate the corresponding group (1, 2 ...) (default: %(default)s)")
    parser.add_argument("--fields", type=str, default="read_id run_id channel start_time sequence_length_template mean_qscore_template calibration_strand_genome_template barcode_arrangement",
        help="list of field names corresponding to attributes to try to fetch from the fast5 files (default: %(default)s)")
    parser.add_argument("--include_path", action='store_true', default=False,
        help="If given, the absolute path to the corresponding file is added in an extra column (default: %(default)s)")
    parser.add_argument("--verbose_level", type=int, default=0,
        help="Level of verbosity, from 2 (Chatty) to 0 (Nothing) (default: %(default)s)")

    # Try to parse arguments
    args = parser.parse_args()

    # Run main function
    Fast5_to_seq_summary (
        fast5_dir = args.fast5_dir,
        seq_summary_fn = args.seq_summary_fn,
        max_fast5 = args.max_fast5,
        threads = args.threads,
        basecall_id = args.basecall_id,
        fields = args.fields.split(),
        include_path = args.include_path,
        verbose_level = args.verbose_level)

#~~~~~~~~~~~~~~pycoQC CLI ENTRY POINT~~~~~~~~~~~~~~#
def main_pycoQC (args=None):
    if args is None:
        args = sys.argv[1:]

    # Define parser object
    parser = argparse.ArgumentParser(
        description ="pycoQC computes metrics and generates interactive QC plots from the sequencing summary report generated by Oxford Nanopore technologies basecallers",
        add_help=False)
    parser.add_argument('--version', '-v', action='version', version="{} v{}".format(package_name, package_version))

    # Define arguments
    group = parser.add_mutually_exclusive_group (required=True)
    group.add_argument("--file", "-f", type=str,
        help="""Path to the sequencing_summary generated by Albacore 1.0.0 + (read_fast5_basecaller.py) / Guppy 2.1.3+ (guppy_basecaller).
        One can also pass a UNIX style regex to match multiple files with glob https://docs.python.org/3.6/library/glob.html (default: %(default)s)")""")
    parser.add_argument("--barcode_file", "-b", default=None, type=str,
        help="""Path to the barcode_summary_file generated by Guppy 2.1.3+ (guppy_barcoder). This is not a required file.
        One can also pass a UNIX style regex to match multiple files with glob https://docs.python.org/3.6/library/glob.html (default: %(default)s)")""")
    parser.add_argument("--outfile", "-o", default="pycoQC.html", type=str,
        help="Path to the output html file (default: %(default)s)")
    parser.add_argument("--min_pass_qual", "-q", default=7, type=int,
        help="Minimum quality to consider a read as 'pass' (default: %(default)s)")
    parser.add_argument("--title", "-t", default=None, type=str,
        help="A title to be used in the html report (default: %(default)s)")
    parser.add_argument("--filter_calibration", default=False, action='store_true',
        help="If given reads flagged as calibration strand by the basecaller are removed (default: %(default)s)")
    parser.add_argument("--verbose_level", choices=[2,1,0], type=int, default=1,
        help="Level of verbosity, from 2 (Chatty) to 0 (Nothing) (default: %(default)s)")
    parser.add_argument("--config", "-c", type=str, default=None,
        help="""Path to a JSON configuration file. If not provided, looks for it in ~/.pycoQC and ~/.config/pycoQC/config. If it's still not found, falls back to default parameters.
        The first level keys are the names of the plots to be included. The second level keys are the parameters to pass to each plotting function (default: %(default)s)")""")
    parser.add_argument("--template_file", type=str, default=None,
        help="Jinja2 html template (default: %(default)s)")
    group.add_argument("--default_config", "-d", action='store_true',
        help="Print default configuration file. Can be used to generate a template JSON file (default: %(default)s)")
    group.add_argument("--list_plots", "-l", default=None, action='store_true',
        help="Print the list of available plotting functions and exit (default: %(default)s)")
    group.add_argument("--help", "-h", action='store_true',
        help="Print a help message and exit. If a plotting function name is also given, print a function specific help message (default: %(default)s)")
    parser.add_argument('method', nargs='?')

    # Try to parse arguments
    args = parser.parse_args()

    # Print customized help message
    if args.help:
        if args.method:
            if args.method in plot_methods:
                print ("pycoQC {} Usage\n".format(args.method))
                print_help (getattr(pycoQC, args.method))
            else:
                print ("{} is not a valid pycoQC plotting method".format(args.method))
                print ("Please choose ammong the following")
                for i in plot_methods:
                    print ("* {}".format(i))
        else:
            parser.print_help()
        print()
        exit()

    # Print the default config parameters and exit
    if args.default_config:
        print_config_file()
        exit()

    # Print the names of valid pycoQC plotting functions
    if args.list_plots:
        print ("Available pycoQC methods")
        for i in plot_methods:
            print ("* {}".format(i))
        exit()

    # Set logging level
    logLevel_dict = {2:logging.DEBUG, 1:logging.INFO, 0:logging.WARNING}
    logger.setLevel (logLevel_dict.get (args.verbose_level, logging.INFO))

    # Run main function
    generate_report(
        summary_file = args.file,
        barcode_file= args.barcode_file,
        outfile = args.outfile,
        qual = args.min_pass_qual,
        filter_calibration = args.filter_calibration,
        config = args.config,
        template_file = args.template_file,
        verbose_level=args.verbose_level,
        title=args.title)

#~~~~~~~~~~~~~~MAIN FUNCTION~~~~~~~~~~~~~~#
def generate_report(
    summary_file,
    barcode_file,
    outfile,
    qual=7,
    filter_calibration=False,
    config=None,
    template_file=None,
    verbose_level=1,
    title=None):
    """ Runs pycoQC and generates the HTML report"""

    # Parse configuration file
    logger.warning("PARSE CONFIGURATION FILE")
    config_dict = parse_config_file(config)
    logger.debug(config_dict)

    # Initiate pycoQC
    logger.warning("PARSE DATA FILES")
    p = pycoQC (
        seq_summary_file=summary_file,
        barcode_summary_file=barcode_file,
        verbose_level=verbose_level,
        min_pass_qual=qual,
        filter_calibration=filter_calibration)

    # Loop over configuration file and run the pycoQC functions defined
    logger.warning("GENERATES PLOTS")
    plots = list()
    titles = list()
    for method_name, method_args in config_dict.items ():

        # Check if method exists and is callable
        if not method_name in plot_methods:
            logger.info("\tWarning: Method {} is defined in configuration but not supported".format(method_name))

        try:
            logger.info("\tRunning method {}".format(method_name))
            logger.debug ("\t{} ({})".format(method_name, method_args))

            # Store plot title for HTML tittle and remove from data passed to plotly
            plot_title = method_args["plot_title"]
            method_args["plot_title"]=""

            # Get method and generate plot
            method = getattr(p, method_name)
            fig = method(**method_args)
            plot = py.plot(
                fig,
                output_type='div',
                include_plotlyjs=False,
                image_width='',
                image_height='',
                show_link=False,
                auto_open=False)

            plots.append(plot)
            titles.append(plot_title)

        except pycoQCError as E:
            logger.info("\t\t{}".format(E))

    logger.warning("WRITE HTML REPORT")

    # Load HTML template for Jinja
    logger.info("\tLoad HTML template")
    template = get_jinja_template(template_file)

    # Set a title for the HTML report
    report_title=""
    if title:
        report_title+=title+"<br>"
    report_title+="generated on "+datetime.datetime.now().strftime("%d/%m/%y")

    # # Calculate SHA checksum and pass it to template
    # with open(summary_file, 'rb') as f:
    #     contents = f.read()
    # summary_file_hash = hashlib.sha256(contents).hexdigest()

    # Render plots
    logger.info("\tRender plots with Jinja2")
    rendering = template.render(
        plots=plots,
        titles=titles,
        plotlyjs=py.get_plotlyjs(),
        report_title=report_title)

    # Write to HTML file
    logger.info("\tWrite to HTML file")
    with open(outfile, "w") as f:
        f.write(rendering)

#~~~~~~~~~~~~~~TEMPLATE AND CONFIG FILE FUNCTIONS~~~~~~~~~~~~~~#
def print_config_file():
    json.dump (default_config(), sys.stdout, indent=2)

def parse_config_file(config_file):

    # First, try to read provided configuration file if given
    if config_file:
        logger.debug ("\tTry to read provided config file")
        try:
            with open(config_file, 'r') as cf:
                return json.load(cf)
        except (FileNotFoundError, IOError,json.JSONDecodeError):
            logger.debug ("\t\tFile not found, non-readable or invalid")

    # Second, look into default system folder
    home=os.path.expanduser('~')
    for config_file in [home+"/.pycoQC", home+"/.config/pycoQC/config"]:
        logger.debug ("\tTry to read config file from system directory:{}".format(config_file))
        try:
            with open(config_file, 'r') as cf:
                return json.load(cf)
        except (FileNotFoundError, IOError,json.JSONDecodeError):
            logger.debug ("\t\tFile not found, non-readable or invalid")

    # Last use the default harcoded config_dict
    logger.debug ("\tFall back to default configuration")
    return default_config()

def get_jinja_template(template_file=None):

    # First, try to read provided configuration file if given
    if template_file:
        logger.debug("\tTry to load provided template file")
        try:
            with open(template_file) as fp:
                template = Template(fp.read())
                return template
        except (FileNotFoundError, IOError):
            logger.debug ("\t\tFile not found, non-readable or invalid")

    # Last use the default harcoded config_dict
    logger.debug ("\tFall back to default template")
    env = Environment (loader=PackageLoader('pycoQC', 'templates'), autoescape=False)
    template = env.get_template('spectre.html.j2')
    return template

def default_config():
    config_dict = {
        'summary': dict(
            plot_title="Summary"),
        'reads_len_1D': dict(
            plot_title='Distribution of read length',
            color='lightsteelblue',
            nbins=200,
            smooth_sigma=2,
            sample=100000),
        'reads_qual_1D': dict(
            plot_title='Distribution of read quality',
            color='salmon',
            nbins=200,
            smooth_sigma=2,
            sample=100000),
        'reads_len_qual_2D': dict(
            plot_title='Mean read quality per sequence length',
            colorscale=[[0.0, 'rgba(255,255,255,0)'], [0.1, 'rgba(255,150,0,0)'], [0.25, 'rgb(255,100,0)'], [0.5, 'rgb(200,0,0)'], [0.75, 'rgb(120,0,0)'], [1.0, 'rgb(70,0,0)']],
            len_nbins=200,
            qual_nbins=75,
            smooth_sigma=2,
            sample=100000),
        'output_over_time': dict(
            plot_title='Output over experiment time',
            cumulative_color="rgb(204,226,255)",
            interval_color="rgb(102,168,255)",
            sample=100000),
        'len_over_time': dict(
            plot_title='Read length over time',
            median_color="rgb(102,168,255)",
            quartile_color="rgb(153,197,255)",
            extreme_color="rgba(153,197,255,0.5)",
            smooth_sigma=1,
            sample=100000),
        'qual_over_time': dict(
            plot_title='Mean read quality over time',
            median_color="rgb(250,128,114)",
            quartile_color="rgb(250,170,160)",
            extreme_color="rgba(250,170,160,0.5)",
            smooth_sigma=1,
            sample=100000),
        'barcode_counts': dict(
            plot_title='Number of reads per barcode',
            min_percent_barcode = 0.1,
            colors = ["#f8bc9c", "#f6e9a1", "#f5f8f2", "#92d9f5", "#4f97ba"]),
        'channels_activity': dict(
            plot_title='Channel activity over time',
            colorscale = [[0.0,'rgba(255,255,255,0)'], [0.01,'rgb(255,255,200)'], [0.25,'rgb(255,200,0)'], [0.5,'rgb(200,0,0)'], [0.75,'rgb(120,0,0)'], [1.0,'rgb(0,0,0)']],
            smooth_sigma=1,
            sample=100000),
        }
    return(config_dict)


if __name__ == "__main__":
    # execute only if run as a script
    main_pycoQC()
