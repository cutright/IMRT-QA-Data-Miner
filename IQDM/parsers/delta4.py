# -*- coding: utf-8 -*-
"""
main program for IMRT QA PDF report parser
Created on Thu May 30 2019
@author: Dan Cutright, PhD
"""

from ..utilities import are_all_strings_in_text, get_csv
from dateutil.parser import parse as date_parser


class Delta4Report:
    def __init__(self):
        self.report_type = 'delta4'
        self.columns = ['Patient Name', 'Patient ID', 'Plan Date', 'Energy', 'Daily Corr', 'Norm Dose', 'Dev', 'DTA',
                        'Gamma-Index', 'Dose Dev', 'Radiation Dev', 'Gamma Pass Criteria', 'Gamma Dose Criteria',
                        'Gamma Dist Criteria']
        self.identifiers = ['ScandiDos AB', 'Treatment Summary', 'Acceptance Limits', 'Daily corr',
                            'Selected Detectors', 'Parameter Definitions & Acceptance Criteria, Detectors']

        self.treatment_summary_columns = ['Beam', 'Gantry', 'Energy', 'Daily Corr', 'Norm Dose',
                                          'Dev', 'DTA', 'Gamma-Index', 'Dose Dev']
        self.data = {}
        self.index_start = {}
        self.index_end = {}
        self.text = None

    def process_data(self, text_data):
        self.text = text_data.split('\n')

        # Patient information
        if 'PRE-TREATMENT REPORT' in self.text[3]:
            self.data['patient_name'] = self.text[0]
            self.data['patient_id'] = self.text[1]
        elif 'Clinic' not in self.text[2]:
            self.data['patient_name'] = self.text[2]
            self.data['patient_id'] = self.text[3]
        else:
            if 'Treatment Summary' in self.text:
                tx_sum_index = self.text.index('Treatment Summary')
                self.data['patient_name'] = self.text[tx_sum_index-3]
                self.data['patient_id'] = self.text[tx_sum_index-2]
            else:
                self.data['patient_name'] = 'Not found'
                self.data['patient_id'] = 'Not found'

        # Beam
        self.index_start['Beam'] = self.get_index_of_next_text_block(self.get_string_index_in_text('°'))
        self.index_end['Beam'] = self.get_index_of_next_text_block(self.index_start['Beam']) - 1
        if self.text[self.index_start['Beam']] == 'Gantry':
            self.index_start['Beam'] = self.get_index_of_next_text_block(self.index_end['Beam'])
            self.index_end['Beam'] = self.get_index_of_next_text_block(self.index_start['Beam']) - 1
        self.data['Beam'] = self.get_data_block('Beam')
        if 'Fraction' in self.data['Beam'][0]:
            self.data['Beam'].pop(0)

        # Gantry
        self.index_start['Gantry'] = self.get_index_of_next_text_block(self.index_end['Beam'])
        self.index_end['Gantry'] = self.get_index_of_next_text_block(self.index_start['Gantry']) - 1
        self.data['Gantry'] = ['N/A'] + self.get_data_block('Gantry')
        if 'Fraction' in self.data['Gantry']:
            self.data['Gantry'].pop(self.data['Gantry'].index('Fraction'))
        energy_override = []  # sometimes the energy is on the same line as the gantry
        for i, row in enumerate(self.data['Gantry']):
            self.data['Gantry'][i] = row.replace('\xc2', '').replace('\xb0', '')
            energy_override.append(None)
            row_split = row.split(' ')
            if len(row_split) > 3:
                energy_override[-1] = ' '.join(row_split[-2:])
                self.data['Gantry'][i] = self.data['Gantry'][i].replace(energy_override[-1], '').strip()

        # Dose and analysis
        self.index_start['Analysis'] = self.get_string_index_in_text('Daily corr Norm') + 2
        self.index_end['Analysis'] = self.get_index_of_next_text_block(self.index_start['Analysis']) - 1
        analysis_data_block = self.text[self.index_start['Analysis']:self.index_end['Analysis']]
        analysis_data = []
        while analysis_data_block:
            row = analysis_data_block.pop(0)

            if 'cGy' not in row:
                row = "%s %s" % (analysis_data_block.pop(0), row)

            if '%' not in row:
                row = "%s %s" % (row, analysis_data_block.pop(0))

            if 'cGy' in row and '%' in row:
                row = row.split('%')
                data = [row[0].split('cGy')[0].strip(),
                        row[0].split('cGy')[1].strip()]
                data.extend(row[1:-1])
                analysis_data.append(data)

        self.data['Norm Dose'] = [row[0] for row in analysis_data]
        self.data['Dev'] = [row[1].strip() for row in analysis_data]
        self.data['DTA'] = [row[2].strip() for row in analysis_data]
        self.data['Gamma-Index'] = [row[3].strip() for row in analysis_data]
        self.data['Dose Dev'] = [row[4].strip() for row in analysis_data]

        # Daily Correction Factor
        self.index_start['Daily Corr'] = self.get_index_of_next_text_block(self.index_end['Analysis'])
        if 'Det within acceptance' in self.text[self.index_start['Daily Corr']]:
            self.index_start['Daily Corr'] = self.get_index_of_next_text_block(self.index_start['Daily Corr'])
            if 'index dose dev' in self.text[self.index_start['Daily Corr']]:
                self.index_start['Daily Corr'] = self.get_index_of_next_text_block(self.index_start['Daily Corr'])
                if 'factor' in self.text[self.index_start['Daily Corr']]:
                    self.index_start['Daily Corr'] = self.get_index_of_next_text_block(self.index_start['Daily Corr'])
        self.index_end['Daily Corr'] = self.get_index_of_next_text_block(self.index_start['Daily Corr']) - 1
        self.data['Daily Corr'] = ['N/A'] + self.get_data_block('Daily Corr')
        for i, row in enumerate(self.data['Daily Corr']):
            if not row.isdigit():
                self.data['Daily Corr'][i] = row[-5:]

        # Energy
        self.index_start['Energy'] = self.get_index_of_next_text_block(self.index_end['Daily Corr'])
        if 'dose dev' in self.text[self.index_start['Energy']]:
            self.index_start['Energy'] = self.get_index_of_next_text_block(self.index_start['Energy'])
        self.index_end['Energy'] = self.get_index_of_next_text_block(self.index_start['Energy']) - 1
        self.data['Energy'] = ['N/A'] + self.get_data_block('Energy')
        if any(energy_override):  # replace values with overrides found in Gantry code block
            for i, override in enumerate(energy_override):
                if override is not None:
                    if len(self.data['Energy']) > i:
                        self.data['Energy'][i] = override

        # Gamma Criteria
        self.index_start['Gamma Criteria'] = self.text.index('Parameter Definitions & Acceptance Criteria, Detectors')
        self.index_start['Acceptance Limits'] = self.text.index('Acceptance Limits')
        self.index_end['Gamma Criteria'] = self.index_start['Acceptance Limits'] - 1
        self.index_end['Acceptance Limits'] = self.get_index_of_next_text_block(self.index_start['Acceptance Limits']) - 1

        for row in self.get_data_block('Gamma Criteria'):
            if 'mm' in row:
                temp = row.split('mm')[0].strip()
                try:
                    float(temp)
                    self.data['gamma_dist'] = temp
                except:
                    pass
            elif '±' in row:
                self.data['gamma_dose'] = row.split('±')[1].replace('%', '')

        self.data['gamma_pass'] = self.get_data_block('Acceptance Limits')[-1].split('%')[0]

    @property
    def radiation_device(self):
        for row in self.text:
            if row.startswith('Radiation Device: '):
                return row.replace('Radiation Device: ', '')
        return None

    @property
    def measured_date(self):
        index_of_first_date = self.get_index_of_first_date()
        date_candidate_1 = self.text[index_of_first_date].split(' ')[0]
        date_candidate_2 = self.text[index_of_first_date+2].split(' ')[0]
        try:
            return str(date_parser(date_candidate_1)).split(' ')[0]
        except:
            try:
                return str(date_parser(date_candidate_2)).split(' ')[0]
            except:
                pass
        return None

    def get_index_of_first_date(self):
        for i, row in enumerate(self.text):
            if are_all_strings_in_text(row, ['/', ':', 'M']) or \
                    are_all_strings_in_text(row, ['.', ':', 'M']):
                try:
                    date_parser(row.split(' ')[0].strip())
                    return i
                except:
                    pass
        return None

    def get_string_index_in_text(self, string, start_index=0):
        for i, row in enumerate(self.text[start_index:]):
            if string in row:
                return i
        return None

    def get_index_of_next_text_block(self, start_index):
        for i, row in enumerate(self.text[start_index:]):
            if row.strip() == '':
                return i + start_index + 1
        return None

    def get_data_block(self, data_type):
        return self.text[self.index_start[data_type]:self.index_end[data_type]]

    @property
    def summary_data(self):
        return {'Patient Name': self.data['patient_name'],
                'Patient ID': self.data['patient_id'],
                'Plan Date': self.measured_date,
                'Energy': '/'.join(list(set([e for e in self.data['Energy'] if e != 'N/A']))),
                'Daily Corr': sum([float(f) for f in self.data['Daily Corr'] if f != 'N/A']) / (
                            len(self.data['Daily Corr']) - 1),
                'Norm Dose': float(self.data['Norm Dose'][0]),
                'Dev': float(self.data['Dev'][0]),
                'DTA': float(self.data['DTA'][0]),
                'Gamma-Index': float(self.data['Gamma-Index'][0]),
                'Dose Dev': float(self.data['Dose Dev'][0]),
                'Radiation Dev': self.radiation_device,
                'Gamma Pass Criteria': float(self.data['gamma_pass']),
                'Gamma Dose Criteria': float(self.data['gamma_dose']),
                'Gamma Dist Criteria': float(self.data['gamma_dist'])}

    @property
    def csv(self):
        return get_csv(self.summary_data, self.columns)
