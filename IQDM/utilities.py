# -*- coding: utf-8 -*-
"""
main program for IMRT QA PDF report parser
Created on Thu May 30 2019
@author: Dan Cutright, PhD
"""

from os.path import isdir, join, splitext, normpath
from os import walk, listdir
import zipfile
from datetime import datetime
from dateutil.parser import parse as date_parser
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


#############################################################
# CSV related functions
#############################################################
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


def load_csv_file(file_path):
    with codecs.open(file_path, 'r', encoding='utf-8', errors='ignore') as doc:
        return [line.split(',') for line in doc]


def import_csv(file_path, day_first=False):
    raw_data = load_csv_file(file_path)
    keys = raw_data.pop(0)  # remove column header row
    keys = [key.strip() for key in keys if key.strip()] + ['file_name']
    data = {key: [] for key in keys}
    for row in raw_data:
        for col, key in enumerate(keys):
            data[key].append(row[col])

    sorted_data = {key: [] for key in keys}
    sorted_data['date_time_obj'] = []

    date_time_objs = get_date_times(data, day_first=day_first)

    for i in get_sorted_indices(date_time_objs):
        for key in keys:
            sorted_data[key].append(data[key][i])
        sorted_data['date_time_obj'].append(date_time_objs[i])

    return sorted_data


def get_file_names_from_csv_file(file_path):
    raw_data = load_csv_file(file_path)
    column_headers = raw_data.pop(0)  # remove column header row
    fp_start = len(column_headers)
    file_names = []
    for row in raw_data:
        file_name_fields = [value for value in row[fp_start:]]
        file_name = ','.join(file_name_fields)
        file_names.append(normpath(file_name.strip()))
    return file_names


#############################################################
# Plotting and Stat related functions
#############################################################
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


def get_date_times(data, datetime_key='Plan Date', row_id_key='Patient ID', day_first=False):
    dates = []
    for i, date_str in enumerate(data[datetime_key]):
        try:
            dates.append(date_parser(date_str, dayfirst=day_first).date())
        except ValueError:
            print('ERROR: Could not parse the following into a date: %s' % date_str)
            print("\tPatient ID: %s" % data[row_id_key][i])
            print("\tUsing today's date instead")
            dates.append(datetime.today().date())
    return dates


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


#############################################################
# File related functions
#############################################################
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
            if splitext(fileName)[1].lower == '.zip':
                zip_file_path = join(dirName, fileName)
                with zipfile.ZipFile(zip_file_path, 'r') as z:
                    for file_name in z.namelist():
                        if not isdir(file_name) and (extension is None or splitext(file_name)[1].lower == extension):
                            temp_path = join(extract_to_path)
                            z.extract(file_name, path=temp_path)


def find_latest_results(init_directory, no_recursive_search=False):
    """
    Find the most recent IQDM results csv file within the provided directory
    :param init_directory: initial scan directory
    :type init_directory: str
    :param no_recursive_search: set to True to ignore subdirectories
    :type no_recursive_search: bool
    :return: a dictionary like {report_type: {'time_stamp': datetime, 'file_path': str}}
    :rtype: dict
    """
    results = {}
    if no_recursive_search:
        process_result_csvs(listdir(init_directory), results)
    else:
        for dirName, subdirList, fileList in walk(init_directory):  # iterate through files and all sub-directories
            process_result_csvs(fileList, results, directory_name=dirName)
    return results


def process_result_csvs(file_list, results, directory_name=None):
    """
    Parse each file for report type and time stamp, edit results with the latest file_path for each report_type
    :param file_list: files to be parsed
    :type file_list: list
    :param results: results dict from find_latest_results()
    :type results: dict
    :param directory_name: optionally specify the directory
    :type directory_name: str
    """
    for file_name in file_list:
        fn = splitext(file_name)[0].lower()
        ext = splitext(file_name)[1].lower()
        if ext == '.csv' and '_results_' in fn:
            try:
                result_info = file_name.split('_')
                report_type = result_info[0]
                time_stamp = result_info[2].replace(ext, '')
                time_stamp = datetime.strptime(time_stamp[:-7], '%Y-%m-%d %H-%M-%S')

                if report_type and report_type not in results.keys() \
                        or results[report_type]['time_stamp'] < time_stamp:
                    if directory_name is None:
                        file_path = file_name
                    else:
                        file_path = join(directory_name, file_name)
                    results[report_type] = {'time_stamp': time_stamp, 'file_path': file_path}
            except Exception:
                continue


def get_processed_files(init_directory, no_recursive_search=False):
    processed = []
    if no_recursive_search:
        get_file_names_from_result_csvs(listdir(init_directory), processed)
    else:
        for dirName, subdirList, fileList in walk(init_directory):  # iterate through files and all sub-directories
            get_file_names_from_result_csvs(fileList, processed, directory_name=dirName)
    return list(set(processed))


def get_file_names_from_result_csvs(file_list, processed, directory_name=None):
    for file_name in file_list:
        fn = splitext(file_name)[0].lower()
        ext = splitext(file_name)[1].lower()
        if ext == '.csv' and '_results_' in fn:
            if directory_name is None:
                file_path = file_name
            else:
                file_path = join(directory_name, file_name)
            try:
                file_names = get_file_names_from_csv_file(file_path)
                processed.extend(file_names)
            except Exception:
                continue


def is_file_name_found_in_processed_files(file_name, directory, processed_files):
    for processed_file in processed_files:
        if normpath(file_name) in processed_file or normpath(join(directory, file_name)) in processed_files:
            return True
    return False
