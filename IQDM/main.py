# -*- coding: utf-8 -*-
"""
main program for IMRT QA PDF report parser
Created on Thu May 30 2019
@author: Dan Cutright, PhD
"""

from __future__ import print_function
import sys
from os.path import isdir, isfile, join
from os import walk
from datetime import datetime
from .parsers.parser import ReportParser
from .utilities import DELIMITER
from .pdf_to_text import convert_pdf_to_txt


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


def process_files(init_directory, require_pdf_ext=True):
    """
    Given an initial directory, process all pdf files into parser classes, write their csv property to results_file
    :param init_directory: initial scanning directory
    :param require_pdf_ext: if you'd like to catch pdf files that are missing .pdf extension, set to False
    :type require_pdf_ext: bool
    """

    time_stamp = str(datetime.now()).replace(':', '-').replace('.', '-')
    results_file = "results_%s.csv" % time_stamp

    for dirName, subdirList, fileList in walk(init_directory):  # iterate through files and all sub-directories
        for fileName in fileList:
            if not require_pdf_ext or fileName.endswith('.pdf'):
                file_path = join(dirName, fileName)
                try:
                    row, report_type, columns = pdf_to_qa_result(file_path)  # process file
                    current_file = "%s_%s" % (report_type, results_file)  # prepend report type to file name
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

    if len(sys.argv) > 2:
        print("Too many arguments provided.")
        return

    if len(sys.argv) < 2:
        print("Please include an initial directory for scanning when calling.")
        return

    init_directory = sys.argv[1]
    if not isdir(init_directory):
        print("%s is not a valid path" % init_directory)
        return

    process_files(init_directory)


if __name__ == '__main__':
    main()
