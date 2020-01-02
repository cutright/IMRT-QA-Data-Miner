# -*- coding: utf-8 -*-
"""
main program for IMRT QA PDF report parser
Created on Thu May 30 2019
@author: Dan Cutright, PhD
"""

from os.path import isdir, join
from os import walk
import zipfile

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


def extract_files_from_zipped_files(init_directory, extract_to_path, extension='.pdf'):
    """
    Function to extract .pdf files from zipped files
    :param init_directory: initial top-level directory to walk through
    :type init_directory: str
    :param extract_to_path: directory to extract pdfs into
    :type extract_to_path: str
    :param extension: file extension of file type to extract, set to None to extract all files
    :type extension: str or None
    """
    for dirName, subdirList, fileList in walk(init_directory):  # iterate through files and all sub-directories
        for fileName in fileList:
            if fileName.endswith('.zip'):
                zip_file_path = join(dirName, fileName)
                with zipfile.ZipFile(zip_file_path, 'r') as z:
                    for file_name in z.namelist():
                        if not isdir(file_name) and (extension is None or file_name.endswith(extension)):
                            temp_path = join(extract_to_path)
                            z.extract(file_name, path=temp_path)