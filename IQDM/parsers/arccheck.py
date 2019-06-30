# -*- coding: utf-8 -*-
"""
ArcCheck Report class
Created on Fri Jun 21 2019
@author: Dan Cutright, PhD
@contributor: Marc J.P. Chamberland, PhD
"""

from ..utilities import get_csv
import re


class ArcCheckReport:
    def __init__(self):
        self.report_type = 'arccheck'
        self.columns = ['Patient Last Name', 'Patient First Name', 'Patient ID', 'Plan Date', 'Dose Type', 'Difference (%)', 'Distance (mm)',
                        'Threshold (%)', 'Meas Uncertainty', 'Analysis Type', 'Total Points', 'Passed', 'Failed',
                        '% Passed', 'Min', 'Max', 'Average', 'Std Dev', 'X offset (mm)', 'Y offset (mm)', 'Notes']
        self.identifiers = ['QA File Parameter', 'Threshold', 'Notes', 'Reviewed By :', 'SSD', 'Depth', 'Energy', 'ArcCHECK']
        self.text = None
        self.data = {}

    def process_data(self, text_data):
        self.text = text_data.split('\n')
        self.data['date'], self.data['hospital'] = [], []
        for row in self.text:
            if row.find('Date: ') > -1:
                self.data['date'] = row.strip('Date: ')
            if row.find('Hospital Name: ') > -1:
                self.data['hospital'] = row.split('Hospital Name: ', 1)[-1]

            if self.data['date'] and self.data['hospital']:
                break

        self.data['qa_file_parameter'] = self.get_group_results('QA File Parameter')

        x_offset = '0'
        y_offset = '0'
        try:
            plan_index = self.text.index('Plan')
            if self.text[plan_index + 2].find('CAX') > -1:
                x_offset, y_offset = re.findall(r'[-+]?[.]?[\d]+(?:,\d\d\d)*[\.]?\d*(?:[eE][-+]?\d+)?',
                                                self.text[plan_index + 2])
        except ValueError:
            pass

        self.data['cax_offset'] = {'X offset': str(x_offset), 'Y offset': str(y_offset)}

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
            try:
                self.data['analysis_type'] = 'DTA'
            except ValueError:
                self.data['analysis_type'] = 'GC'  # Gradient Correction

        self.data['summary'] = self.get_group_results('Summary (%s Analysis)' % self.data['analysis_type'])

        # Gamma Index Summary Block
        try:
            self.text.index('Gamma Index Summary')
            self.data['gamma_stats'] = 'Gamma Index Summary'
        except ValueError:
            self.data['gamma_stats'] = {'Minimum': 'n/a',
                                'Maximum': 'n/a',
                                'Average': 'n/a',
                                'Stdv': 'n/a'}

        self.data['gamma_stats'] = self.get_gamma_statistics(self.data['gamma_stats'])

        self.data['notes'] = self.text[self.text.index('Notes') + 1]

    def get_gamma_statistics(self, stats_delimiter):
        gamma_stats = {}
        stats_fields = ['Minimum', 'Maximum', 'Average', 'Stdv']

        group_start = self.text.index(stats_delimiter)

        for field in stats_fields:
            field_start = self.text[group_start:-1].index(field) + 1
            gamma_stats[field] = self.text[group_start:-1][field_start]

        return gamma_stats

    def get_group_results(self, data_group):
        """
        ArcCheck reports contain three blocks of results. data_group may be among the following:
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
        patient_name = self.data['qa_file_parameter']['Patient Name'].replace('^', ' ').split(', ')
        if len(patient_name) > 1:
            last_name = patient_name[0].title()
            first_name = patient_name[1].title()
        elif len(patient_name) == 1:
            last_name = patient_name[0].title()
            first_name = 'n/a'
        else:
            last_name = 'n/a'
            first_name = 'n/a'

        return {'Patient Last Name': last_name,
                'Patient First Name': first_name,
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
                '% Passed': self.data['summary']['% Passed'],
                'Min': self.data['gamma_stats']['Minimum'],
                'Max': self.data['gamma_stats']['Maximum'],
                'Average': self.data['gamma_stats']['Average'],
                'Std Dev': self.data['gamma_stats']['Stdv'],
                'X offset (mm)': self.data['cax_offset']['X offset'],
                'Y offset (mm)':self.data['cax_offset']['Y offset'],
                'Notes': self.data['notes']}

    @property
    def csv(self):
        return get_csv(self.summary_data, self.columns)
