# -*- coding: utf-8 -*-
"""
main program for IMRT QA PDF report parser
Created on Thu May 30 2019
@author: Dan Cutright, PhD
"""

from ..utilities import get_csv


class MapcheckReport:
    def __init__(self):
        self.report_type = 'mapcheck'
        self.columns = ['Patient Name', 'Patient ID', 'Plan Date', 'Dose Type', 'Difference (%)', 'Distance (mm)',
                        'Threshold (%)', 'Meas Uncertainty', 'Analysis Type', 'Total Points', 'Passed', 'Failed',
                        '% Passed']
        self.identifiers = ['QA File Parameter', 'Threshold', 'Notes', 'Reviewed By :', 'SSD', 'Depth', 'Energy']
        self.text = None
        self.data = {}

    def process_data(self, text_data):
        self.text = text_data.split('\n')
        self.data['date'], self.data['hospital'] = [], []
        for row in self.text:
            if row.find('Date: ') > -1:
                self.data['date'] = row.strip('Date: ')
            if row.find('Hospital Name: ') > -1:
                self.data['hospital'] = row.strip('Hospital Name: ')

            if self.data['date'] and self.data['hospital']:
                break

        self.data['qa_file_parameter'] = self.get_group_results('QA File Parameter')

        # Dose Comparison Block
        try:
            self.text.index('Absolute Dose Comparison')
            self.data['dose_comparison_type'] = 'Absolute Dose Comparison'
        except ValueError:
            self.data['dose_comparison_type'] = 'Relative Comparison'
        self.data['dose_comparison'] = self.get_group_results(self.data['dose_comparison_type'])
        if '% Diff' in list(self.data['dose_comparison']):  # Alternate for Difference (%) for some versions of report?
            self.data['dose_comparison']['Difference (%)'] = self.data['dose_comparison']['% Diff']
        if 'Threshold' in list(self.data['dose_comparison']):  # Alternate for Threshold (%) for some versions of report?
            self.data['dose_comparison']['Threshold (%)'] = self.data['dose_comparison']['Threshold']

        # Summary Analysis Block
        try:
            self.text.index('Summary (Gamma Analysis)')
            self.data['analysis_type'] = 'Gamma'
        except ValueError:
            self.data['analysis_type'] = 'DTA'
        self.data['summary'] = self.get_group_results('Summary (%s Analysis)' % self.data['analysis_type'])

    def get_group_results(self, data_group):
        """
        Mapcheck reports contain three blocks of results. data_group may be among the following:
            'QA File Parameter'
            'Absolute Dose Comparison' or 'Relative Comparison'
            'Gamma' or 'DTA'
        """
        group_start = self.text.index(data_group)
        var_name_start = group_start + 1
        data_start = self.text[var_name_start:-1].index('') + 1 + var_name_start
        data_count = data_start - var_name_start

        # If patient name is too long, sometimes the pdf parsing gets off-set
        if self.text[data_start] == 'Set1':
            data_start += 1

        group_results = {}
        for i in range(data_count):
            if self.text[var_name_start+i]:
                group_results[self.text[var_name_start+i]] = self.text[data_start+i].replace(' : ', '')

        return group_results

    @property
    def summary_data(self):
        """
        Collect the parsed data into a dictionary with keys corresponding to columns
        :return: parsed data
        :rtype: dict
        """
        return {'Patient Name': self.data['qa_file_parameter']['Patient Name'],
                'Patient ID': self.data['qa_file_parameter']['Patient ID'],
                'Plan Date': self.data['qa_file_parameter']['Plan Date'],
                'Dose Type': self.data['dose_comparison_type'],
                'Difference (%)': self.data['dose_comparison']['Difference (%)'],
                'Distance (mm)': self.data['dose_comparison']['Distance (mm)'],
                'Threshold (%)': self.data['dose_comparison']['Threshold (%)'],
                'Meas Uncertainty': self.data['dose_comparison']['Meas Uncertainty'],
                'Analysis Type': self.data['analysis_type'],
                'Total Points': self.data['summary']['Total Points'],
                'Passed': self.data['summary']['Passed'],
                'Failed': self.data['summary']['Failed'],
                '% Passed': self.data['summary']['% Passed']}

    @property
    def csv(self):
        return get_csv(self.summary_data, self.columns)
