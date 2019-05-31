# -*- coding: utf-8 -*-
"""
main program for IMRT QA PDF report parser
Created on Thu May 30 2019
@author: Dan Cutright, PhD
"""

from ..utilities import are_all_strings_in_text
from .mapcheck import MapcheckReport
from .delta4 import Delta4Report


# These classes will be checked in ReportParser.get_report()
REPORT_CLASSES = [MapcheckReport, Delta4Report]


class ReportParser:
    """
    This class determines which Report class to use and subsequently processes the data.

    Use of this class requires each report class listed in REPORT_CLASSES contains the following properties:
        identifiers:    this is a list of strings that collectively are uniquely found in a report type
        columns:        a list of strings indicating the columns of the csv to be output
        csv:            a string of values for each column, delimited with DELIMITER in utilities.py
        report_type:    a string describing the report, this will be used in the results filename created in main.py

    This class also requires the following method:
        process_data(text_data):    processing the data does not occur until this is called

    If ReportParser.report is None, the input text was not identified to be any of the report classes listed in
    REPORT_CLASSES
    """
    def __init__(self, text):
        self.report = self.get_report(text)
        if self.report:
            self.columns = self.report.columns
            self.csv = self.report.csv
            self.report_type = self.report.report_type

    @staticmethod
    def get_report(text):
        for report_class in REPORT_CLASSES:
            rc = report_class()  # initialize class to access identifiers
            if are_all_strings_in_text(text, rc.identifiers):
                rc.process_data(text)  # parse the text data
                return rc
        return None
