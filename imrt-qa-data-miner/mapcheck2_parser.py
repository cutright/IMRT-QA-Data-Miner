#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Code to parse SNC Mapcheck2 measurement txt files
Created on Wed Jul 18 2018
@author: Dan Cutright, PhD
"""

from __future__ import print_function
import numpy as np
import os


def read_file(abs_file_path):
    with open(abs_file_path, 'r') as document:
        lines = [line.strip() for line in document]
    return lines


def is_file_snc_measurement(lines):
    if "WARNING! Editing this file can cause it to become unusable with the SNC Patient software" in lines[0]:
        if "Measured File" in lines[4]:
            if "Sun Nuclear Corporation" in lines[5]:
                return True
    return False


class MapCheckMeasurement:
    def __init__(self, abs_file_path):
        snc_file = read_file(abs_file_path)
        if is_file_snc_measurement(snc_file):

            for line in snc_file[8:42]:
                if ':' in line:
                    line = line.split(':')
                    variable = line[0].strip().lower().replace(' ', '_').replace('/', '_')
                    value = line[1].strip().replace("\t", ' ')
                    setattr(self, variable, value)
            self.measurement_date = self.date.replace('Time', '').strip()
            self.measurement_time = snc_file[18].split('Time:')[1].strip()
            self.snc_file = snc_file

            self.start_row = {'background': snc_file.index('Background'),
                              'cal_factors': snc_file.index('Calibration Factors'),
                              'offset': snc_file.index('Offset'),
                              'raw_counts': snc_file.index('Raw Counts'),
                              'corrected_counts': snc_file.index('Corrected Counts'),
                              'dose_counts': snc_file.index('Dose Counts'),
                              'data_flags': snc_file.index('Data Flags'),
                              'interpolated': snc_file.index('Interpolated'),
                              'dose_interpolated': snc_file.index('Dose Interpolated')}
            self.data = {}
            for key in self.start_row:
                key_data = {}
                for i in range(int(self.rows)):
                    key_data[i] = snc_file[self.start_row[key]+i+2].split('\t')
                raw = np.array([key_data[i] for i in range(int(self.rows))], dtype=np.float)
                col = np.array(snc_file[self.start_row[key]+int(self.rows)+2].split('\t')[1::], dtype=np.float)
                x = np.array(snc_file[self.start_row[key]+int(self.rows)+3].split('\t')[1::], dtype=np.float)
                self.data[key] = {'y': raw[:, 0],
                                  'row': raw[:, 1],
                                  'data': raw[:, 2:-1],
                                  'col': col,
                                  'x': x}
                self.data[key]['cax'] = self.data[key]['data'][self.data[key]['y'].tolist().index(0),
                                                               self.data[key]['x'].tolist().index(0)]
        else:
            print("This file is not a MapCheck Measurement: %s" % abs_file_path)


def measurement_data_miner(start_path):
    files = [f for f in os.listdir(start_path) if os.path.isfile(os.path.join(start_path, f))]
    data = []

    for i in range(len(files)):
        current = MapCheckMeasurement(os.path.join(start_path, files[i]))
        fn = files[i].lower()

        if 'ix' in fn:
            linac = '21ix'
        elif 'tb' in fn:
            linac = 'TrueBeam'
        elif 'truebeam' in fn:
            linac = 'TrueBeam'
        elif 'tril' in fn:
            linac = 'Trilogy'
        else:
            linac = 'Unknown'

        if 'arc' in fn:
            delivery = 'Arc'
        elif 'ap' in fn:
            delivery = 'AP'

        if '6x' in fn:
            energy = '6X'
        elif '10x' in fn:
            energy = '10X'
        elif '18x' in fn:
            energy = '18X'
        elif '23x' in fn:
            energy = '23X'
        else:
            energy = 'Unknown'

        data.append({'data': current,
                     'file': files[i],
                     'linac': linac,
                     'delivery': delivery,
                     'energy': energy})

    return data


def data_to_csv(start_path, output_file):
    mined_data = measurement_data_miner(start_path)
    with open(output_file, "w") as csv:
        columns = ['Linac',
                   'Energy',
                   'Delivery Type',
                   'Date',
                   'Time',
                   'File Name',
                   'Array Calibration File',
                   'Dose Calibration Factor',
                   'Dose Calibration Info',
                   'Temperature',
                   'Background',
                   'Offset',
                   'Raw Counts',
                   'Corrected Counts',
                   'Dose Counts',
                   'Data Flags',
                   'Interpolated',
                   'Dose Interpolated\n']
        csv.write(','.join(columns))

    for result in mined_data:
        with open(output_file, "a") as csv:
            row = [result['linac'],
                   result['energy'],
                   result['delivery'],
                   result['data'].measurement_date,
                   result['data'].measurement_time,
                   result['data'].filename,
                   result['data'].cal_file,
                   result['data'].dose_per_count,
                   result['data'].dose_info,
                   result['data'].temperature.split(',')[0],
                   str(result['data'].data['background']['cax']),
                   str(result['data'].data['offset']['cax']),
                   str(result['data'].data['raw_counts']['cax']),
                   str(result['data'].data['corrected_counts']['cax']),
                   str(result['data'].data['dose_counts']['cax']),
                   str(result['data'].data['data_flags']['cax']),
                   str(result['data'].data['interpolated']['cax']),
                   str(result['data'].data['dose_interpolated']['cax']) + '\n']
            csv.write(','.join(row))
