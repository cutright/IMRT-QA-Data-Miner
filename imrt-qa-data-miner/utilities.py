# -*- coding: utf-8 -*-


DELIMITER = ';'
ALTERNATE = '^'


def are_all_of_these_strings_in_text_data(text_data, list_of_strings):
    """
    :param text_data: output from convert_pdf_to_text
    :type text_data: list of str
    :param list_of_strings: a list of strings used to identify document type
    :type list_of_strings: list of str
    :return: Will return true if every string in list_of_strings is found in the text data
    :rtype: bool
    """
    for str_to_find in list_of_strings:
        if str_to_find not in text_data:
            return False
    return True


def get_csv(data, columns):
    clean_csv = [str(data[column]).replace(DELIMITER, ALTERNATE) for column in columns]
    return DELIMITER.join(clean_csv)
