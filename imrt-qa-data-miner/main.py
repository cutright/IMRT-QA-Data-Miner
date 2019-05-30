#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
main program for IMRT QA PDF report parser
Created on Wed Apr 18 2018
@author: Dan Cutright, PhD
"""

from __future__ import print_function
import os
import sys
from datetime import datetime
from pdf_to_text import convert_pdf_to_txt
from os.path import basename
from utilities import DELIMITER
from parsers.parser import ReportParser


def pdf_to_qa_result(abs_file_path):

    try:
        text = convert_pdf_to_txt(abs_file_path)
    except:
        print("Non-compatible PDF detected: %s" % abs_file_path)
        return ''

    report_obj = ReportParser(text)
    if report_obj.report is not None:
        return report_obj.csv + DELIMITER + basename(abs_file_path), report_obj.report_type, report_obj.columns


def process_data(init_directory, results_file, require_pdf_ext=True):

    # don't forget to write column headers
    for dirName, subdirList, fileList in os.walk(init_directory):
        for fileName in fileList:
            if not require_pdf_ext or fileName.endswith('.pdf'):
                file_path = os.path.join(dirName, fileName)
                try:
                    row, report_type, columns = pdf_to_qa_result(file_path)
                    current_file = "%s_%s" % (report_type, results_file)
                    if row:
                        if not os.path.isfile(current_file):
                            with open(current_file, 'w') as csv:
                                csv.write(DELIMITER.join(columns))
                        with open(current_file, "a") as csv:
                            csv.write(row + '\n')
                        print("Processed: %s" % file_path)
                except Exception as e:
                    print(str(e))
                    print("Non-compatible PDF detected: %s" % file_path)


def main():

    if len(sys.argv) > 2:
        print("Too many arguments provided.")
        return

    if len(sys.argv) < 2:
        print("Please include an initial directory for scanning when calling.")
        return

    init_directory = sys.argv[1]

    output_file = "results_%s.csv" % str(datetime.now()).replace(':', '-').replace('.', '-')

    process_data(init_directory, output_file)


if __name__ == '__main__':
    main()
