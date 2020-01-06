# -*- coding: utf-8 -*-
"""
main program for IMRT QA PDF report parser
Created on Thu May 30 2019
@author: Dan Cutright, PhD
"""

from os.path import isdir, join, splitext
from os import walk
import zipfile
from datetime import datetime
import numpy as np
import codecs

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
                        if not isdir(file_name) and (extension is None or splitext(file_name)[1].lower == extension):
                            temp_path = join(extract_to_path)
                            z.extract(file_name, path=temp_path)


def import_csv(file_path, date_format):
    with codecs.open(file_path, 'r', encoding='utf-8', errors='ignore') as doc:
        raw_data = []
        for line in doc:
            raw_data.append(line.split(','))

    keys = raw_data.pop(0)
    keys = [key.strip() for key in keys if key] + ['file_name']
    data = {key: [] for key in keys}
    for row in raw_data:
        for col, key in enumerate(keys):
            data[key].append(row[col])

    sorted_data = {key: [] for key in keys}

    to_sort = [string_to_date_time(v, date_format) for v in data['Plan Date']]

    for i in get_sorted_indices(to_sort):
        for key in keys:
            sorted_data[key].append(data[key][i])

    return sorted_data


def collapse_into_single_dates(x, y):
    """
    Function used for a time plot to convert multiple values into one value, while retaining enough information
    to perform a moving average over time
    :param x: a list of dates in ascending order
    :param y: a list of values and can use the '+' operator as a function of date
    :return: a unique list of dates, sum of y for that date, and number of original points for that date
    :rtype: dict
    """

    # average daily data and keep track of points per day
    x_collapsed = [x[0]]
    y_collapsed = [y[0]]
    w_collapsed = [1]
    for n in range(1, len(x)):
        if x[n] == x_collapsed[-1]:
            y_collapsed[-1] = (y_collapsed[-1] + y[n])
            w_collapsed[-1] += 1
        else:
            x_collapsed.append(x[n])
            y_collapsed.append(y[n])
            w_collapsed.append(1)

    return {'x': x_collapsed, 'y': y_collapsed, 'w': w_collapsed}


def moving_avg(xyw, avg_len):
    """
    Calculate a moving average for a given averaging length
    :param xyw: output from collapse_into_single_dates
    :type xyw: dict
    :param avg_len: average of these number of points, i.e., look-back window
    :type avg_len: int
    :return: list of x values, list of y values
    :rtype: tuple
    """
    cumsum, moving_aves, x_final = [0], [], []

    for i, y in enumerate(xyw['y'], 1):
        cumsum.append(cumsum[i - 1] + y / xyw['w'][i - 1])
        if i >= avg_len:
            moving_ave = (cumsum[i] - cumsum[i - avg_len]) / avg_len
            moving_aves.append(moving_ave)
    x_final = [xyw['x'][i] for i in range(avg_len - 1, len(xyw['x']))]

    return x_final, moving_aves


def get_sorted_indices(some_list):
    try:
        return [i[0] for i in sorted(enumerate(some_list), key=lambda x: x[1])]
    except TypeError:  # can't sort if a mix of str and float
        try:
            temp_data = [[value, -float('inf')][value == 'None'] for value in some_list]
            return [i[0] for i in sorted(enumerate(temp_data), key=lambda x: x[1])]
        except TypeError:
            temp_data = [str(value) for value in some_list]
            return [i[0] for i in sorted(enumerate(temp_data), key=lambda x: x[1])]


def string_to_date_time(date_string, date_format):
    return datetime.strptime(date_string, date_format).date()


def get_control_limits(y):
    """
    Calculate control limits for Control Chart
    :param y: data
    :type y: list
    :return: center line, upper control limit, and lower control limit
    """
    y = np.array(y)

    center_line = np.mean(y)
    avg_moving_range = np.mean(np.absolute(np.diff(y)))

    scalar_d = 1.128

    ucl = center_line + 3 * avg_moving_range / scalar_d
    lcl = center_line - 3 * avg_moving_range / scalar_d

    return center_line, ucl, lcl