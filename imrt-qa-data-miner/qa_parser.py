#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
IMRT QA PDF report parser
Created on Wed Apr 18 2018
@author: Dan Cutright, PhD
"""

from pdf_to_text import convert_pdf_to_txt
from os.path import basename
from dateutil.parser import parse as date_parser


def pdf_to_qa_result(abs_file_path):

    try:
        text = convert_pdf_to_txt(abs_file_path).split('\n')
    except:
        return False

    if is_file_snc_mapcheck(text):
        return MapcheckReport(text).data_to_csv() + ',' + basename(abs_file_path)

    elif is_file_scandidos_delta4(text):
        return Delta4Report(text).summary_csv + ',' + basename(abs_file_path)


class MapcheckReport:
    def __init__(self, text_data):
        self.text = text_data
        self.date, self.hospital = [], []
        for row in text_data:
            if row.find('Date: ') > -1:
                self.date = row.strip('Date: ')
            if row.find('Hospital Name: ') > -1:
                self.hospital = row.strip('Hospital Name: ')

            if self.date and self.hospital:
                break

        self.qa_file_parameter = self.get_group_results('QA File Parameter')

        try:
            self.text.index('Absolute Dose Comparison')
            self.dose_comparison_type = 'Absolute Dose Comparison'
        except ValueError:
            self.dose_comparison_type = 'Relative Comparison'
        self.dose_comparison = self.get_group_results(self.dose_comparison_type)

        try:
            self.text.index('Summary (Gamma Analysis)')
            self.analysis_type = 'Gamma'
        except ValueError:
            self.analysis_type = 'DTA'
        self.summary = self.get_group_results('Summary (%s Analysis)' % self.analysis_type)

    def get_group_results(self, data_group):
        group_start = self.text.index(data_group)
        var_name_start = group_start + 1
        data_start = self.text[var_name_start:-1].index('') + 1 + var_name_start
        data_count = data_start - var_name_start

        # If patient name is too long, sometimes the pdf parsing gets off-set
        if self.text[data_start] == 'Set1':
            data_start += 1

        group_results = {}
        for i in range(0, data_count):
            if self.text[var_name_start+i]:
                group_results[self.text[var_name_start+i]] = self.text[data_start+i].replace(' : ', '')

        return group_results

    def data_to_csv(self):
        row = [self.qa_file_parameter['Patient Name'].replace(',', '^'),
               self.qa_file_parameter['Patient ID'].replace(',', '^'),
               self.qa_file_parameter['Plan Date'].replace(',', '^'),
               self.dose_comparison_type,
               self.dose_comparison['Difference (%)'],
               self.dose_comparison['Distance (mm)'],
               self.dose_comparison['Threshold (%)'],
               self.dose_comparison['Meas Uncertainty'],
               self.analysis_type,
               self.summary['Total Points'],
               self.summary['Passed'],
               self.summary['Failed'],
               self.summary['% Passed']]
        return ','.join(row)


class Delta4Report:
    def __init__(self, text_data):
        self.text = text_data.split('\n')

        self.patient_name = self.text[2]
        self.patient_id = self.text[3]

        self.index_of_first_date = self.get_index_of_first_date()
        self.index_of_first_degree = self.get_index_of_first_degree()

        # Reconstruct Treatment Summary table
        self.treatment_summary_columns = ['Beam', 'Gantry', 'Energy', 'Daily Corr', 'Norm Dose',
                                          'Dev', 'DTA', 'Gamma-Index', 'Dose Dev']
        self.data = {col: None for col in self.treatment_summary_columns}
        self.index_start = {col: None for col in self.treatment_summary_columns}
        self.index_end = {col: None for col in self.treatment_summary_columns}

        # Beam
        self.index_start['Beam'] = self.find_index_of_next_text_block(self.index_of_first_degree)
        self.index_end['Beam'] = self.find_index_of_next_text_block(self.index_start['Beam']) - 1
        self.data['Beam'] = self.get_data_block('Beam')

        # Gantry
        self.index_start['Gantry'] = self.find_index_of_next_text_block(self.index_end['Beam'])
        self.index_end['Gantry'] = self.find_index_of_next_text_block(self.index_start['Gantry']) - 1
        self.data['Gantry'] = ['N/A'] + self.get_data_block('Gantry')
        for i, row in enumerate(self.data['Gantry']):
            self.data['Gantry'][i] = row.replace('\xc2', '').replace('\xb0', '')

        # Dose and analysis
        self.index_start['Analysis'] = self.text.index('Energy Daily corr Norm') + 2
        self.index_end['Analysis'] = self.find_index_of_next_text_block(self.index_start['Analysis']) - 1
        analysis_data = []
        for i, row in enumerate(self.text[self.index_start['Analysis']:self.index_end['Analysis']]):
            if 'cGy' in row and '%' in row:
                analysis_data.append(row.split(' '))
            elif 'cGy' not in row:
                analysis_data.append(("%s %s" % (self.text[self.index_start['Analysis']+i+1], row)).split(' '))

        self.data['Norm Dose'] = [row[0] for row in analysis_data]
        self.data['Dev'] = [row[2].replace('%', '').strip() for row in analysis_data]
        self.data['DTA'] = [row[3].replace('%', '').strip() for row in analysis_data]
        self.data['Gamma-Index'] = [row[4].replace('%', '').strip() for row in analysis_data]
        self.data['Dose Dev'] = [row[5].replace('%', '').strip() for row in analysis_data]

        # Daily Correction Factor
        self.index_start['Daily Corr'] = self.find_index_of_next_text_block(self.index_end['Analysis'])
        if 'Det within acceptance' in self.text[self.index_start['Daily Corr']]:
            self.index_start['Daily Corr'] = self.find_index_of_next_text_block(self.index_start['Daily Corr'])
        self.index_end['Daily Corr'] = self.find_index_of_next_text_block(self.index_start['Daily Corr']) - 1
        self.data['Daily Corr'] = ['N/A'] + self.get_data_block('Daily Corr')

        # Energy
        self.index_start['Energy'] = self.find_index_of_next_text_block(self.index_end['Daily Corr'])
        if 'dose dev' in self.text[self.index_start['Energy']]:
            self.index_start['Energy'] = self.find_index_of_next_text_block(self.index_start['Energy'])
        self.index_end['Energy'] = self.find_index_of_next_text_block( self.index_start['Energy']) - 1
        self.data['Energy'] = ['N/A'] + self.get_data_block('Energy')

        # Gamma Criteria
        self.index_start['Gamma Criteria'] = self.text.index('Parameter Definitions & Acceptance Criteria, Detectors')
        self.index_start['Acceptance Limits'] = self.text.index('Acceptance Limits')
        self.index_end['Gamma Criteria'] =  self.index_start['Acceptance Limits'] - 1
        self.index_end['Acceptance Limits'] = self.find_index_of_next_text_block(self.index_start['Acceptance Limits']) - 1

        for row in self.get_data_block('Gamma Criteria'):
            if 'mm' in row:
                temp = row.split('mm')[0].strip()
                try:
                    float(temp)
                    self.gamma_dist = temp
                except:
                    pass
            elif '±' in row:
                self.gamma_dose = row.split('±')[1].replace('%', '')

        self.gamma_pass = self.get_data_block('Acceptance Limits')[-1].split('%')[0]

    def __repr__(self):
        prefix = "%-15s" * len(self.treatment_summary_columns)
        ans = ['Radiation Device: %s' % self.radiation_device,
               'Measured Date: %s' % self.measured_date,
               'Gamma Criteria: %s%% at %s%%/%smm' % (self.gamma_pass, self.gamma_dose, self.gamma_dist),
               '',
               prefix % tuple(self.treatment_summary_columns),
               prefix % tuple(['-' * 11] * len(self.treatment_summary_columns))]
        for i in range(len(self.data['Beam'])):
            row = []
            for col in self.treatment_summary_columns:
                row.append(self.data[col][i])
            row = prefix % tuple(row)
            ans.append(row)
        return '\n'.join(ans)

    @property
    def summary_data(self):
        return {'Patient Name': self.patient_name,
                'Patient ID': self.patient_id,
                'Plan Date': self.measured_date,
                'Energy': '/'.join(list(set([e for e in self.data['Energy'] if e != 'N/A']))),
                'Daily Corr': sum([float(f) for f in self.data['Daily Corr'] if f != 'N/A']) / (len(self.data['Daily Corr'])-1),
                'Norm Dose': float(self.data['Norm Dose'][0]),
                'Dev': float(self.data['Dev'][0]),
                'DTA': float(self.data['DTA'][0]),
                'Gamma-Index': float(self.data['Gamma-Index'][0]),
                'Dose Dev': float(self.data['Dose Dev'][0]),
                'Radiation Dev': self.radiation_device,
                'Gamma Pass Criteria': float(self.gamma_pass),
                'Gamma Dose Criteria': float(self.gamma_dose),
                'Gamma Dist Criteria': float(self.gamma_dist)}

    @property
    def measured_date(self):
        try:
            return str(date_parser(self.text[self.index_of_first_date+1].split(' ')[0])).split(' ')[0]
        except:
            return None

    @property
    def radiation_device(self):
        for row in self.text:
            if row.startswith('Radiation Device: '):
                return row.replace('Radiation Device: ', '')
        return None

    def get_index_of_first_date(self):
        for i, row in enumerate(self.text):
            if are_all_of_these_strings_in_text_data(row, ['/', ':', 'M']):
                try:
                    date_parser(row.split(' ')[0].strip())
                    return i
                except:
                    pass
        return None

    def get_index_of_first_degree(self):
        for i, row in enumerate(self.text):
            if '°' in row:
                return i
        return None

    def find_index_of_next_text_block(self, start_index):
        for i, row in enumerate(self.text[start_index:]):
            if row.strip() == '':
                return i + start_index + 1
        return None

    def get_data_block(self, data_type):
        return self.text[self.index_start[data_type]:self.index_end[data_type]]


def is_file_snc_mapcheck(text_data):
    find_these = ['QA File Parameter', 'Threshold (%)', 'Notes', 'Reviewed By :']
    return are_all_of_these_strings_in_text_data(text_data, find_these)


def is_file_scandidos_delta4(text_data):
    find_these = ['ScandiDos AB', 'Treatment Summary', 'Parameter Definitions & Acceptance Criteria, Detectors',
                  'Acceptance Limits', 'Daily corr', 'Selected Detectors']
    return are_all_of_these_strings_in_text_data(text_data, find_these)


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
