# -*- coding: utf-8 -*-
"""
main program for IMRT QA PDF report parser
Created on Thu May 30 2019
@author: Dan Cutright, PhD
"""


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
