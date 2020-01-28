# -*- coding: utf-8 -*-
"""
SNC Patient Report class
Created on Fri Jun 21 2019
@author: Dan Cutright, PhD
@contributor: Marc J.P. Chamberland, PhD
"""

from IQDM.utilities import get_csv
import re


class SNCPatientReport:
    def __init__(self):
        self.report_type = 'sncpatient'
        self.columns = ['Patient Last Name', 'Patient First Name', 'Patient ID', 'Plan Date', 'Energy', 'Angle', 'Dose Type', 'Difference (%)', 'Distance (mm)',
                        'Threshold (%)', 'Meas Uncertainty', 'Equipment', 'Analysis Type', 'Total Points', 'Passed', 'Failed',
                        '% Passed', 'Min', 'Max', 'Average', 'Std Dev', 'X offset (mm)', 'Y offset (mm)', 'Notes']
        self.identifiers = ['QA File Parameter', 'Threshold', 'Notes', 'Reviewed By :', 'SSD', 'Depth', 'Energy']
        self.text = None
        self.data = {}

        self.relative_dose = False

    @property
    def equipment_type(self):
        if self.text:
            for line in self.text:
                if 'arccheck' in line.lower():
                    return 'ArcCheck'
                elif 'mapcheck' in line.lower():
                    return 'MapCheck'
        return 'Unknown'

    def process_data(self, text_data):
        self.text = text_data.split('\n')
        with open('test.txt', 'w') as doc:
            doc.write(text_data)
        self.data['date'], self.data['hospital'] = [], []
        for row in self.text:
            if row.find('Date: ') > -1:
                self.data['date'] = row.strip('Date: ')
            if row.find('Hospital Name: ') > -1:
                self.data['hospital'] = row.split('Hospital Name: ', 1)[-1]

            if self.data['date'] and self.data['hospital']:
                break

        self.data['qa_file_parameter'] = self.get_group_qa_parameters('QA File Parameter')

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
        # self.data['dose_comparison'] = self.get_group_results(self.data['dose_comparison_type'])
        self.data['dose_comparison'] = self.get_group_dose_comparison(self.data['dose_comparison_type'])
        if '% Diff' in list(self.data['dose_comparison']):  # Alternate for Difference (%) for some versions of report?
            self.data['dose_comparison']['Difference (%)'] = self.data['dose_comparison']['% Diff']
        if 'Threshold' in list(self.data['dose_comparison']):  # Alternate for Threshold (%) for some versions of report?
            self.data['dose_comparison']['Threshold (%)'] = self.data['dose_comparison']['Threshold']

        # Summary Analysis Block
        try:
            self.text.index('Summary (Gamma Analysis)')
            self.analysis_type = 'Summary (Gamma Analysis)'
            self.data['analysis_type'] = 'Gamma'
        except ValueError:
            try:
                self.text.index('Summary (DTA Analysis)')
                self.data['analysis_type'] = 'DTA'
            except ValueError:
                self.text.index('Summary (GC Analysis)')
                self.data['analysis_type'] = 'GC'  # Gradient Correction

        # self.data['summary'] = self.get_group_results('Summary (%s Analysis)' % self.data['analysis_type'])
        self.data['summary'] = self.get_group_analysis('Summary (%s Analysis)' % self.data['analysis_type'])

        # Gamma Index Summary Block
        try:
            self.text.index('Gamma Index Summary')
            self.data['gamma_stats'] = self.get_gamma_statistics('Gamma Index Summary')
        except:
            self.data['gamma_stats'] = {'Minimum': 'n/a', 'Maximum': 'n/a', 'Average': 'n/a',  'Stdv': 'n/a'}

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
        SNC Patient reports contain three blocks of results. data_group may be among the following:
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

    def get_group_dose_comparison(self, data_group):
        group_start = self.text.index(data_group)

        group_end = False
        group_end_index = 0
        while not group_end:
            if 'Summary ' in self.text[group_start+group_end_index]:
                group_end = group_start + group_end_index
            else:
                group_end_index += 1

        keys, values = [], []
        for i in range(group_end_index-1):
            row = self.text[group_start+i+1]
            if row:
                if ':' not in row:
                    keys.append(row.strip())
                else:
                    values.append(row.replace(':', '').strip())
        return {key: values[i] for i, key in enumerate(keys)}

    def get_group_qa_parameters(self, data_group):
        group_start = self.text.index(data_group)
        ignored = ['arccheck', 'mapcheck', '.txt', '.snc', '.dcm']

        group_end = False
        group_end_index = 0
        while not group_end:
            if 'Dose Comparison' in self.text[group_start+group_end_index] or \
                    'Relative Comparison' in self.text[group_start+group_end_index]:
                self.relative_dose = 'Relative Comparison' in self.text[group_start+group_end_index]
                group_end = group_start + group_end_index
            else:
                group_end_index += 1

        keys, values = [], []
        for i in range(group_end_index-1):
            row = self.text[group_start+i+1]
            if row:
                if ' : ' in row:
                    values.append(row.replace(':', '').strip())
                else:
                    if row.lower().strip() != 'plan':
                        include_row = True
                        for ignored_value in ignored:
                            if ignored_value in row.lower():
                                include_row = False
                        if include_row:
                            keys.append(row.strip())

        extra_values = []
        i = 1
        while len(values) + len(extra_values) < len(keys):
            new_line = self.text[group_start - i]
            if new_line and ' : ' in new_line:
                extra_values.append(new_line.replace(':', '').strip())
            i += 1

        while extra_values:
            values.insert(0, extra_values.pop())

        return {key: values[i] for i, key in enumerate(keys)}

    def get_group_analysis(self, data_group):
        group_start = self.text.index(data_group)

        group_end = False
        group_end_index = 0
        while not group_end:
            if 'Dose Values in ' in self.text[group_start+group_end_index]:
                group_end = group_start + group_end_index
            else:
                group_end_index += 1

        keys, values = [], []
        for i in range(group_end_index-1):
            row = self.text[group_start+i+1]
            if row:
                if ' : ' in row:
                    values.append(row.replace(':', '').strip())
                else:
                    if '*' not in row:
                        keys.append(row.strip())

        extra_values = []
        i = 1
        while len(values) + len(extra_values) < len(keys):
            print
            new_line = self.text[group_start-i]
            if new_line and ' : ' in new_line:
                extra_values.append(new_line.replace(':', '').strip())
            i += 1

        while extra_values:
            values.append(extra_values.pop())

        return {key: values[i] for i, key in enumerate(keys)}

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
                'Energy': self.data['qa_file_parameter']['Energy'],
                'Angle': self.data['qa_file_parameter']['Angle'],
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
                'Y offset (mm)': self.data['cax_offset']['Y offset'],
                'Notes': self.data['notes'],
                'Relative Dose': self.relative_dose,
                'Equipment': self.equipment_type}

    @property
    def csv(self):
        return get_csv(self.summary_data, self.columns)
