# -*- coding: utf-8 -*-
"""
main program for IMRT QA PDF report parser
Created on Thu May 30 2019
@author: Dan Cutright, PhD
"""

from parsers.parser import ReportParser
from pdf_to_text import convert_pdf_to_txt
from os.path import isfile, join
from os import walk
from datetime import datetime


DELIMITER = ','  # delimiter for the csv output file for process_files
ALTERNATE = '^'  # replace the delimiter character with this so not to confuse csv file parsing


def are_all_strings_in_text(text, list_of_strings):
    """
    :param text: output from convert_pdf_to_text
    :type text: list of str
    :param list_of_strings: a list of strings used to identify document type
    :type list_of_strings: list of str
    :return: Will return true if every string in list_of_strings is found in the text data
    :rtype: bool
    """
    for str_to_find in list_of_strings:
        if str_to_find not in text:
            return False
    return True


def get_csv(data, columns):
    """
    Convert a dictionary of data into a row for a csv file
    :param data: a dictionary with values with str representations
    :type data: dict
    :param columns: a list of keys dictating the order of the csv
    :type columns: list
    :return: a csv string delimited by DELIMITER
    :rtype: str
    """
    clean_csv = [str(data[column]).replace(DELIMITER, ALTERNATE) for column in columns]
    return DELIMITER.join(clean_csv)


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
