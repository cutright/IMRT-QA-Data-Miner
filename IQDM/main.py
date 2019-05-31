# -*- coding: utf-8 -*-
"""
main program for IMRT QA PDF report parser
Created on Thu May 30 2019
@author: Dan Cutright, PhD
"""

from __future__ import print_function
from os.path import isdir, isfile, join
from os import walk, listdir
from datetime import datetime
from .parsers.parser import ReportParser
from .utilities import DELIMITER
from .pdf_to_text import convert_pdf_to_txt
import argparse
from pathvalidate import sanitize_filename


CURRENT_VERSION = '0.2.7'


def pdf_to_qa_result(abs_file_path):
    """
    Given an absolute file path, convert file to text
    :param abs_file_path: file to be converted to text
    :return: csv row to be written to csv file, report type, column headers for csv
    :rtype: tuple
    """

    try:
        text = convert_pdf_to_txt(abs_file_path)
    except Exception as e:
        print("Non-compatible PDF detected: %s" % abs_file_path)
        print(str(e))
        return ''

    report_obj = ReportParser(text)
    if report_obj.report is not None:
        return report_obj.csv + DELIMITER + abs_file_path, report_obj.report_type, report_obj.columns


def process_files(init_directory, ignore_extension=False, output_file=None, output_dir=None, no_recursive_search=False):
    """
    Given an initial directory, process all pdf files into parser classes, write their csv property to results_file
    :param init_directory: initial scanning directory
    :param ignore_extension: if you'd like to catch pdf files that are missing .pdf extension, set to True
    :type ignore_extension: bool
    :param output_file: user specified output file name, report type will be prepended to this value
    :param output_dir: user specified output directory, default value is to local directory
    :param no_recursive_search: to ignore sub-directories, set to True
    :type no_recursive_search: bool
    """

    time_stamp = str(datetime.now()).replace(':', '-').replace('.', '-')
    if output_file is None:
        output_file = "results_%s.csv" % time_stamp

    if no_recursive_search:
        for file_name in listdir(init_directory):
            if ignore_extension or file_name.endswith('.pdf'):
                file_path = join(init_directory, file_name)
                process_file(file_path, output_file, output_dir)
    else:
        for dirName, subdirList, fileList in walk(init_directory):  # iterate through files and all sub-directories
            for fileName in fileList:
                if ignore_extension or fileName.endswith('.pdf'):
                    file_path = join(dirName, fileName)
                    process_file(file_path, output_file, output_dir)


def process_file(file_path, output_file, output_dir):
    try:
        row, report_type, columns = pdf_to_qa_result(file_path)  # process file
        current_file = "%s_%s" % (report_type, output_file)  # prepend report type to file name
        if output_dir:
            current_file = join(output_dir, current_file)
        if row:
            if not isfile(current_file):  # if file doesn't exist, need to write columns
                with open(current_file, 'w') as csv:
                    csv.write(DELIMITER.join(columns) + '\n')
            with open(current_file, "a") as csv:  # write the processed data
                csv.write(row + '\n')
            print("Processed: %s" % file_path)
    except Exception as e:  # error likely occurred in pdf_to_qa_result()
        print("Non-compatible PDF detected: %s" % file_path)
        print(str(e))


def main():

    cmd_parser = argparse.ArgumentParser(description="Command line interface for IQDM")
    cmd_parser.add_argument('-ie', '--ignore-extension',
                            dest='ignore_extension',
                            help='Script will check all files, not just ones with .pdf extensions',
                            default=False,
                            action='store_true')
    cmd_parser.add_argument('-od', '--output-dir',
                            dest='output_dir',
                            help='Output stored in local directory by default, specify otherwise here',
                            default=None)
    cmd_parser.add_argument('-of', '--output-file',
                            dest='output_file',
                            help='Output will be saved as <report_type>_results_<time-stamp>.csv by default. '
                                 'Define this tag to customize file name after <report_type>_',
                            default=None)
    cmd_parser.add_argument('-ver', '--version',
                            dest='print_version',
                            help='Print the IQDM version',
                            default=False,
                            action='store_true')
    cmd_parser.add_argument('--no-recursive-search',
                            dest='no_recursive_search',
                            help='Include this flag to skip sub-directories',
                            default=False,
                            action='store_true')
    cmd_parser.add_argument('initial_directory', nargs='?',
                            help='Scan this directory and all sub-directories')
    args = cmd_parser.parse_args()

    # if args.initial_directory and len(args.initial_directory) > 2:
    #     print("Too many arguments provided. Please only provide the initial scanning directory after IQDM")
    #     return

    if not args.initial_directory or len(args.initial_directory) < 2:
        if args.print_version:
            print('IMRT-QA-Data-Miner: IQDM v%s' % CURRENT_VERSION)
            return
        else:
            print('Initial directory not provided!')
            return

    if not isdir(args.initial_directory):
        print("%s is not a valid or accessible directory" % args.initial_directory)
        return

    output_file, print_file_name_change = None, False
    if args.output_file:
        output_file = sanitize_filename(args.output_file)
        if output_file not in args.output_file:
            print_file_name_change = True

    process_files(args.initial_directory,
                  ignore_extension=args.ignore_extension,
                  output_file=output_file,
                  output_dir=args.output_dir,
                  no_recursive_search=args.no_recursive_search)

    if args.print_version:
        print('IMRT-QA-Data-Miner: IQDM v%s' % CURRENT_VERSION)

    if print_file_name_change:
        print('Output file name was changed to <report_type>_%s' % output_file)


if __name__ == '__main__':
    main()
