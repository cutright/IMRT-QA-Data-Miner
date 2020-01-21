#!/usr/bin/env python
# -*- coding: utf-8 -*-

# trending_delta4.py
"""
Bokeh server script to analyze a delta4_results csv from IQDM
"""
# Copyright (c) 2019
# Dan Cutright, PhD
# Medical Physicist
# University of Chicago Medical Center
# This file is part of IMRT QA Data Miner, partial based on code from DVH Analytics

from bokeh.plotting import figure
from bokeh.models import HoverTool, ColumnDataSource, Select, Div, TextInput, Legend, Spacer
from bokeh.layouts import column, row
from bokeh.models.widgets import DatePicker, CheckboxButtonGroup
import numpy as np
from IQDM.utilities import collapse_into_single_dates, moving_avg, get_control_limits, import_csv

GROUPS = [1, 2]
COLORS = {1: 'blue', 2: 'red'}

# TODO: Generalize for different parsers
MAIN_PLOT_KEYS = ['x', 'y', 'id', 'gamma_crit', 'file_name', 'gamma_index', 'daily_corr', 'dta']


class TrendingDashboard:
    def __init__(self, file_path, day_first=False):

        self.data = import_csv(file_path, day_first=day_first)

        self.__create_sources()
        self.__set_x()
        self.__create_figures()
        self.__set_properties()
        self.__create_divs()
        self.__add_plot_data()
        self.__add_histogram_data()
        self.__add_ichart_data()
        self.__add_hover()
        self.__add_legend()

        self.__create_widgets()
        self.__bind_widgets()
        self.__do_layout()

        self.update()

    def __create_sources(self):
        self.source = {grp: {'plot': ColumnDataSource(data={key: [] for key in MAIN_PLOT_KEYS}),
                             'trend': ColumnDataSource(data=dict(x=[], y=[])),
                             'bound': ColumnDataSource(data=dict(x=[], y=[])),
                             'patch': ColumnDataSource(data=dict(x=[], y=[])),
                             'hist': ColumnDataSource(data=dict(x=[], y=[]))} for grp in GROUPS}

        self.ichart_source = {grp: {'plot': ColumnDataSource(data=dict(x=[], y=[], mrn=[], color=[], alpha=[], dates=[],
                                                                       gamma_index=[], daily_corr=[], gamma_crit=[],
                                                                       dta=[])),
                                    'center_line': ColumnDataSource(data=dict(x=[], y=[], mrn=[])),
                                    'ucl_line': ColumnDataSource(data=dict(x=[], y=[], mrn=[])),
                                    'lcl_line': ColumnDataSource(data=dict(x=[], y=[], mrn=[])),
                                    'bound': ColumnDataSource(data=dict(x=[], mrn=[], upper=[], avg=[], lower=[])),
                                    'patch': ColumnDataSource(data=dict(x=[], y=[]))} for grp in GROUPS}

    def __set_x(self):
        self.x = self.data['date_time_obj']

    def __create_figures(self):

        self.fig = figure(plot_width=1000, plot_height=375, x_axis_type='datetime')
        self.histogram = figure(tools="", plot_width=1000, plot_height=275)
        self.ichart = figure(plot_width=1000, plot_height=375)

    def __set_properties(self):
        self.fig.xaxis.axis_label_text_font_size = "17pt"
        self.fig.yaxis.axis_label_text_font_size = "17pt"
        self.fig.xaxis.major_label_text_font_size = "15pt"
        self.fig.yaxis.major_label_text_font_size = "15pt"

        self.histogram.xaxis.axis_label_text_font_size = "17pt"
        self.histogram.yaxis.axis_label_text_font_size = "17pt"
        self.histogram.xaxis.major_label_text_font_size = "15pt"
        self.histogram.yaxis.major_label_text_font_size = "15pt"

        self.ichart.xaxis.axis_label = "Study #"
        self.ichart.xaxis.axis_label_text_font_size = "17pt"
        self.ichart.yaxis.axis_label_text_font_size = "17pt"
        self.ichart.xaxis.major_label_text_font_size = "15pt"
        self.ichart.yaxis.major_label_text_font_size = "15pt"

    def __add_plot_data(self):
        self.plot_data = {grp: self.fig.circle('x', 'y', source=self.source[grp]['plot'],
                                               color=COLORS[grp], size=4, alpha=0.4) for grp in GROUPS}
        self.plot_trend = {grp: self.fig.line('x', 'y', source=self.source[grp]['trend'],
                                              line_color='black', line_width=4) for grp in GROUPS}
        self.plot_avg = {grp: self.fig.line('x', 'avg', source=self.source[grp]['bound'],
                                            line_color='black') for grp in GROUPS}
        self.plot_patch = {grp: self.fig.patch('x', 'y', source=self.source[grp]['patch'],
                                               color=COLORS[grp], alpha=0.2) for grp in GROUPS}

    def __add_histogram_data(self):
        self.vbar = {grp: self.histogram.vbar(x='x', width='width', bottom=0, top='top',
                                              source=self.source[grp]['hist'], alpha=0.5, color=COLORS[grp])
                     for grp in GROUPS}

        self.histogram.xaxis.axis_label = ""
        self.histogram.yaxis.axis_label = "Frequency"

    def __add_ichart_data(self):
        self.ichart_data = {grp: self.ichart.circle('x', 'y', source=self.ichart_source[grp]['plot'],
                                                    size=4, color='color', alpha='alpha') for grp in GROUPS}
        self.ichart_data_line = {grp: self.ichart.line('x', 'y', source=self.ichart_source[grp]['plot'],
                                                       color=COLORS[grp], line_dash='solid') for grp in GROUPS}
        self.ichart_patch = {grp: self.ichart.patch('x', 'y', color=COLORS[grp],
                                                    source=self.ichart_source[grp]['patch'],
                                                    alpha=0.1) for grp in GROUPS}
        self.ichart_center_line = {grp: self.ichart.line('x', 'y', source=self.ichart_source[grp]['center_line'],
                                                         alpha=1, color='black', line_dash='solid') for grp in GROUPS}
        self.ichart_lcl_line = {grp: self.ichart.line('x', 'y', source=self.ichart_source[grp]['lcl_line'], alpha=1,
                                                      color='red', line_dash='dashed') for grp in GROUPS}
        self.ichart_ucl_line = {grp: self.ichart.line('x', 'y', source=self.ichart_source[grp]['ucl_line'], alpha=1,
                                                      color='red', line_dash='dashed') for grp in GROUPS}

    def __add_legend(self):
        # Main TrendingDashboard
        group_items = {grp: [("Data %s " % grp, [self.plot_data[grp]]),
                             ("Avg %s " % grp, [self.plot_avg[grp]]),
                             ("Rolling Avg %s " % grp, [self.plot_trend[grp]]),
                             ("Percentile Region %s " % grp, [self.plot_patch[grp]])] for grp in GROUPS}
        items = group_items[GROUPS[0]]
        if len(GROUPS) > 1:
            for grp in GROUPS[1:]:
                items.extend(group_items[grp])
        legend_plot = Legend(items=items, orientation='horizontal')
        self.fig.add_layout(legend_plot, 'above')
        self.fig.legend.click_policy = "hide"

        # Control Chart
        group_items = {grp: [("Value %s  " % grp, [self.ichart_data[grp]]),
                             ("Line  %s" % grp, [self.ichart_data_line[grp]]),
                             ('Center  %s' % grp, [self.ichart_center_line[grp]]),
                             ('UCL  %s' % grp, [self.ichart_ucl_line[grp]]),
                             ('LCL  %s' % grp, [self.ichart_lcl_line[grp]]),
                             ('In Ctrl  %s' % grp, [self.ichart_patch[grp]])] for grp in GROUPS}
        items = group_items[GROUPS[0]]
        if len(GROUPS) > 1:
            for grp in GROUPS[1:]:
                items.extend(group_items[grp])
        legend_ichart = Legend(items=items,  orientation='horizontal')
        self.ichart.add_layout(legend_ichart, 'above')
        self.ichart.legend.click_policy = "hide"

    def __add_hover(self):
        self.fig.add_tools(HoverTool(tooltips=[("Plan Date", "@x{%F}"),
                                               ("Patient", "@id"),
                                               ("y", "@y"),
                                               ('Gamma Crit', "@gamma_crit"),
                                               ('Gamma Pass', '@gamma_index'),
                                               ('DTA', '@dta'),
                                               ('Daily Corr', '@daily_corr'),
                                               ('file', '@file_name')],
                                     formatters={'x': 'datetime'},
                                     renderers=[self.plot_data[grp] for grp in GROUPS]))

        self.histogram.add_tools(HoverTool(show_arrow=True, line_policy='next', mode='vline',
                                           tooltips=[("Bin Center", "@x"),
                                                     ('Frequency', '@top')],
                                           renderers=[self.vbar[grp] for grp in GROUPS]))

        self.ichart.add_tools(HoverTool(show_arrow=True,
                                        tooltips=[('ID', '@mrn'),
                                                  ('Date', '@dates{%F}'),
                                                  ('Study', '@x'),
                                                  ('Value', '@y{0.2f}'),
                                                  ("y", "@y"),
                                                  ('Gamma Crit', "@gamma_crit"),
                                                  ('Gamma Pass', '@gamma_index'),
                                                  ('DTA', '@dta'),
                                                  ('Daily Corr', '@daily_corr'),
                                                  ('file', '@file_name')
                                                  ],
                                        formatters={'dates': 'datetime'},
                                        renderers=[self.ichart_data[grp] for grp in GROUPS]))

    def __create_divs(self):
        self.div_summary = {grp: Div() for grp in GROUPS}
        self.div_center_line = {grp: Div(text='', width=175) for grp in GROUPS}
        self.div_ucl = {grp: Div(text='', width=175) for grp in GROUPS}
        self.div_lcl = {grp: Div(text='', width=175) for grp in GROUPS}

    def __create_widgets(self):
        ignored_y = ['Patient Name', 'Patient ID', 'Plan Date', 'Radiation Dev', 'Energy', 'file_name', 'date_time_obj']
        y_options = [option for option in list(self.data) if option not in ignored_y]
        self.select_y = Select(title='Y-variable:', value='Dose Dev', options=y_options)

        linacs = list(set(self.data['Radiation Dev']))
        linacs.sort()
        linacs.insert(0, 'All')
        linacs.append('None')
        self.select_linac = {grp: Select(title='Linac %s:' % grp, value='All', options=linacs, width=250)
                             for grp in GROUPS}
        self.select_linac[2].value = 'None'

        energies = list(set(self.data['Energy']))
        energies.sort()
        energies.insert(0, 'Any')
        self.select_energies = {grp: Select(title='Energy %s:' % grp, value='Any', options=energies, width=250)
                                for grp in GROUPS}

        self.avg_len_input = TextInput(title='Avg. Len:', value='10', width=100)

        self.percentile_input = TextInput(title='Percentile:', value='90', width=100)

        self.bins_input = TextInput(title='Bins:', value='20', width=100)

        self.start_date_picker = DatePicker(title='Start Date:', value=self.x[0])
        self.end_date_picker = DatePicker(title='End Date:', value=self.x[-1])

        self.gamma_options = ['5.0%/3.0mm', '3.0%/3.0mm', '3.0%/2.0mm', 'Any']
        self.checkbox_button_group = CheckboxButtonGroup(labels=self.gamma_options, active=[3])

    def __bind_widgets(self):

        self.select_y.on_change('value', self.update_source_ticker)
        for grp in GROUPS:
            self.select_linac[grp].on_change('value', self.update_source_ticker)
            self.select_energies[grp].on_change('value', self.update_source_ticker)
        self.avg_len_input.on_change('value', self.update_source_ticker)
        self.percentile_input.on_change('value', self.update_source_ticker)
        self.bins_input.on_change('value', self.update_source_ticker)
        self.start_date_picker.on_change('value', self.update_source_ticker)
        self.end_date_picker.on_change('value', self.update_source_ticker)
        self.checkbox_button_group.on_change('active', self.update_source_ticker)

    def __do_layout(self):
        # TODO: Generalize for 1 or 2 groups
        self.layout = column(row(self.select_y, self.select_linac[1], self.select_linac[2], self.avg_len_input,
                                 self.percentile_input, self.bins_input),
                             row(self.select_energies[1], self.select_energies[2]),
                             row(self.start_date_picker, self.end_date_picker),
                             row(Div(text='Gamma Criteria: '), self.checkbox_button_group),
                             self.div_summary[1],
                             self.div_summary[2],
                             row(Spacer(width=10), self.fig),
                             Spacer(height=50),
                             row(Spacer(width=10), self.histogram),
                             Spacer(height=50),
                             row(Spacer(width=10), self.ichart),
                             row(self.div_center_line[1], self.div_ucl[1], self.div_lcl[1]),
                             row(self.div_center_line[2], self.div_ucl[2], self.div_lcl[2]))

    def update_source_ticker(self, attr, old, new):
        self.update()

    def update(self):
        for grp in GROUPS:
            new_data = {key: [] for key in MAIN_PLOT_KEYS}
            active_gamma = [self.gamma_options[a] for a in self.checkbox_button_group.active]
            if self.select_linac[grp] != 'None':
                for i in range(len(self.x)):
                    if self.select_linac[grp].value == 'All' or \
                            self.data['Radiation Dev'][i] == self.select_linac[grp].value:
                        if self.end_date_picker.value > self.x[i] > self.start_date_picker.value:
                            gamma_crit = "%s%%/%smm" % (self.data['Gamma Dose Criteria'][i],
                                                        self.data['Gamma Dist Criteria'][i])
                            if 'Any' in active_gamma or gamma_crit in active_gamma:
                                if 'Any' == self.select_energies[grp].value or \
                                        self.data['Energy'][i] == self.select_energies[grp].value:

                                    try:
                                        new_data['y'].append(float(self.data[self.select_y.value][i]))
                                    except ValueError:
                                        continue
                                    new_data['x'].append(self.x[i])
                                    new_data['id'].append(self.data['Patient ID'][i])
                                    new_data['gamma_crit'].append(gamma_crit)
                                    new_data['file_name'].append(self.data['file_name'][i])
                                    new_data['gamma_index'].append('%s%%' % self.data['Gamma-Index'][i])
                                    new_data['daily_corr'].append(self.data['Daily Corr'][i])
                                    new_data['dta'].append('%s%%' % self.data['DTA'][i])

            try:
                y = new_data['y']
                self.div_summary[grp].text = "<b>Linac %s</b>: <b>Min</b>: %0.3f | <b>Low</b>: %0.3f | " \
                                             "<b>Mean</b>: %0.3f | <b>Median</b>: %0.3f | <b>Upper</b>: %0.3f | " \
                                             "<b>Max</b>: %0.3f" % \
                                             (grp, np.min(y), np.percentile(y, 25), np.sum(y)/len(y),
                                              np.percentile(y, 50), np.percentile(y, 75), np.max(y))
            except:
                self.div_summary[grp].text = "<b>Linac %s</b>" % grp

            self.source[grp]['plot'].data = new_data

            self.fig.yaxis.axis_label = self.select_y.value
            self.fig.xaxis.axis_label = 'Plan Date'

            self.update_histogram(grp)
            self.update_trend(grp, int(float(self.avg_len_input.value)), float(self.percentile_input.value))
            self.update_ichart()

    def update_histogram(self, group):
        width_fraction = 0.9
        try:
            bin_size = int(self.bins_input.value)
        except ValueError:
            bin_size = 20
            self.bins_input.value = str(bin_size)
        hist, bins = np.histogram(self.source[group]['plot'].data['y'], bins=bin_size)
        width = [width_fraction * (bins[1] - bins[0])] * bin_size
        center = (bins[:-1] + bins[1:]) / 2.
        if set(hist) != {0}:
            self.source[group]['hist'].data = {'x': center, 'top': hist, 'width': width}
        else:
            self.source[group]['hist'].data = {'x': [], 'top': [], 'width': []}

        self.histogram.xaxis.axis_label = self.select_y.value

    def update_trend(self, source_key, avg_len, percentile):
        x = self.source[source_key]['plot'].data['x']
        y = self.source[source_key]['plot'].data['y']
        if x and y:
            data_collapsed = collapse_into_single_dates(x, y)
            x_trend, y_trend = moving_avg(data_collapsed, avg_len)

            y_np = np.array(self.source[source_key]['plot'].data['y'])
            upper_bound = float(np.percentile(y_np, 50. + percentile / 2.))
            average = float(np.percentile(y_np, 50))
            lower_bound = float(np.percentile(y_np, 50. - percentile / 2.))

            self.source[source_key]['trend'].data = {'x': x_trend, 'y': y_trend, 'mrn': ['Avg'] * len(x_trend)}
            self.source[source_key]['bound'].data = {'x': [x[0], x[-1]],
                                                     'mrn': ['Series Avg'] * 2,
                                                     'upper': [upper_bound] * 2,
                                                     'avg': [average] * 2,
                                                     'lower': [lower_bound] * 2,
                                                     'y': [average] * 2}
            self.source[source_key]['patch'].data = {'x': [x[0], x[-1], x[-1], x[0]],
                                                     'y': [upper_bound, upper_bound, lower_bound, lower_bound]}
        else:
            self.source[source_key]['trend'].data = {'x': [], 'y': [], 'mrn': []}
            self.source[source_key]['bound'].data = {'x': [], 'mrn': [], 'upper': [], 'avg': [], 'lower': [], 'y': []}
            self.source[source_key]['patch'].data = {'x': [], 'y': []}

    def update_ichart(self):
        self.ichart.yaxis.axis_label = self.select_y.value

        for grp in GROUPS:
            y = self.source[grp]['plot'].data['y']
            mrn = self.source[grp]['plot'].data['id']
            dates = self.source[grp]['plot'].data['x']
            gamma_crit = self.source[grp]['plot'].data['gamma_crit']
            gamma_index = self.source[grp]['plot'].data['gamma_index']
            daily_corr = self.source[grp]['plot'].data['daily_corr']
            dta = self.source[grp]['plot'].data['dta']
            file_name = self.source[grp]['plot'].data['file_name']
            x = list(range(len(dates)))

            center_line, ucl, lcl = get_control_limits(y)

            if self.select_y.value in ['Gamma-Index', 'DTA'] and ucl > 100:
                ucl = 100

            colors = ['red', 'blue']
            alphas = [0.3, 0.4]
            color = [colors[ucl >= value >= lcl] for value in y]
            alpha = [alphas[ucl >= value >= lcl] for value in y]

            self.ichart_source[grp]['plot'].data = {'x': x, 'y': y, 'mrn': mrn, 'gamma_crit': gamma_crit,
                                                    'gamma_index': gamma_index, 'daily_corr': daily_corr, 'dta': dta,
                                                    'color': color, 'alpha': alpha, 'dates': dates,
                                                    'file_name': file_name}

            if len(x) > 1:
                self.ichart_source[grp]['patch'].data = {'x': [x[0], x[-1], x[-1], x[0]],
                                                         'y': [ucl, ucl, lcl, lcl]}
                self.ichart_source[grp]['center_line'].data = {'x': [min(x), max(x)],
                                                               'y': [center_line] * 2,
                                                               'mrn': ['center line'] * 2}

                self.ichart_source[grp]['lcl_line'].data = {'x': [min(x), max(x)],
                                                            'y': [lcl] * 2,
                                                            'mrn': ['center line'] * 2}
                self.ichart_source[grp]['ucl_line'].data = {'x': [min(x), max(x)],
                                                            'y': [ucl] * 2,
                                                            'mrn': ['center line'] * 2}

                self.div_center_line[grp].text = "<b>Center line</b>: %0.3f" % center_line
                self.div_ucl[grp].text = "<b>UCL</b>: %0.3f" % ucl
                self.div_lcl[grp].text = "<b>LCL</b>: %0.3f" % lcl
            else:
                self.ichart_source[grp]['patch'].data = {'x': [], 'y': []}
                self.ichart_source[grp]['center_line'].data = {'x': [], 'y': [], 'mrn': []}
                self.ichart_source[grp]['lcl_line'].data = {'x': [], 'y': [], 'mrn': []}
                self.ichart_source[grp]['ucl_line'].data = {'x': [], 'y': [], 'mrn': []}

                self.div_center_line[grp].text = "<b>Center line</b>:"
                self.div_ucl[grp].text = "<b>UCL</b>:"
                self.div_lcl[grp].text = "<b>LCL</b>:"
