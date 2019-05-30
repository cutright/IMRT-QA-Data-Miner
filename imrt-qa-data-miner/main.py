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

    parsed_report_obj = ReportParser(text)
    if parsed_report_obj.report is not None:
        return parsed_report_obj.summary_csv + DELIMITER + basename(abs_file_path)


def process_data(init_directory, results_file):

    # don't forget to write column headers
    for dirName, subdirList, fileList in os.walk(init_directory):
        for fileName in fileList:
            if fileName.endswith('.pdf'):
                file_path = os.path.join(dirName, fileName)
                try:
                    row = pdf_to_qa_result(file_path)
                    if row:
                        with open(results_file, "a") as csv:
                            csv.write(row + '\n')
                        print("Processed: %s" % file_path)
                except Exception as e:
                    print(str(e))
                    print("Non-compatible PDF detected: %s" % file_path)


def main():

    if len(sys.argv) > 3:
        print("Too many arguments provided.")
        return

    if len(sys.argv) < 2:
        print("Please include an initial directory for scanning when calling.")
        return

    if not os.path.isdir(sys.argv[1]):
        print("Invalid directory: %s" % sys.argv[1])
        return

    init_directory = sys.argv[1]

    if len(sys.argv) == 3:
        output_file = sys.argv[2]
    else:
        output_file = "results_%s.txt" % str(datetime.now()).replace(':', '-').replace('.', '-')

    process_data(init_directory, output_file)


if __name__ == '__main__':
    main()
