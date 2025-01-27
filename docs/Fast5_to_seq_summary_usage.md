# Using Fast5_to_seq_summary

In case you do not have access to a summary sequencing file, pycoQC comes with `Fast5_to_seq_summary`, a simple yet efficient tool to generate such file from a directory containing basecalled fast5 files.

## User interface

`Fast5_to_seq_summary` was designed to be used either through a python Application programming interface (API) for Jupyter notebook or a command line interface (CLI).

### Jupyter API

* [pycoQC API usage notebook](https://a-slide.github.io/pycoQC/demo/Fast5_to_seq_summary_API_demo/)

### Shell CLI

* [pycoQC CLI usage notebook](https://a-slide.github.io/pycoQC/demo/Fast5_to_seq_summary_CLI_demo/)


## Input files and options

The program can also attempt to extract additional information including the file path (include_path) corresponding to each read and the following fields:

* mean_qscore_template
* sequence_length_template
* called_events
* skip_prob
* stay_prob
* step_prob
* strand_score
* read_id
* start_time
* duration
* start_mux
* read_number
* channel
* channel_digitisation
* channel_offset
* channel_range
* channel_sampling
* run_id
* sample_id
* device_id
* protocol_run
* flow_cell
* calibration_strand
* calibration_strand
* calibration_strand
* calibration_strand
* barcode_arrangement
* barcode_full
* barcode_score

If a field in not found or invalid it is simply ignored for the current fast5 file.

Multiprocessing is supported to speed up the data extraction.

If generated with the minimal default fields, the file is compatible with pycoQC.

### Input files

`Fast5_to_seq_summary` requires a directory containing FAST5 file basecalled with Albacore or Guppy.

At the moment multi-fast5 files generated by Guppy are not supported.

### Example files

pycoQC repository contains a small number of example fast5 files that can be use to test `Fast5_to_seq_summary`.

* docs/demo/data/fast5
