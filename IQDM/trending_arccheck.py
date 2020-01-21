#!/usr/bin/env python
# -*- coding: utf-8 -*-

# trending_arccheck.py
"""
Bokeh server script to analyze a delta4_results csv from IQDM
"""
# Copyright (c) 2019
# Dan Cutright, PhD
# Medical Physicist
# University of Chicago Medical Center
# This file is part of IMRT QA Data Miner, partial based on code from DVH Analytics

from bokeh.io import curdoc
from bokeh.plotting import figure
from bokeh.models import HoverTool, ColumnDataSource, Select, Div, TextInput, Legend, Spacer
from bokeh.layouts import column, row
from bokeh.models.widgets import DatePicker, CheckboxButtonGroup
import numpy as np
from IQDM.utilities import collapse_into_single_dates, moving_avg, get_control_limits, import_csv
import sys

FILE_PATH = sys.argv[1]
DAY_FIRST = day_first = {'true': True, 'false': False}[sys.argv[2]]


class Plot:
    def __init__(self, data):

        self.data = data
        self.source = {key: {'plot': ColumnDataSource(data=dict(x=[], y=[])),
                             'trend': ColumnDataSource(data=dict(x=[], y=[])),
                             'bound': ColumnDataSource(data=dict(x=[], y=[])),
                             'patch': ColumnDataSource(data=dict(x=[], y=[])),
                             'hist': ColumnDataSource(data=dict(x=[], y=[]))} for key in [1, 2]}

        self.ichart = None

        self.__set_x()
        self.__create_figure()
        self.__add_plot_data()
        self.__add_histogram_data()
        self.__add_hover()
        self.__add_legend()
        self.__set_plot_attr()

    def __create_figure(self):

        self.fig = figure(plot_width=1000, plot_height=375, x_axis_type='datetime')
        self.fig.xaxis.axis_label_text_font_size = "17pt"
        self.fig.yaxis.axis_label_text_font_size = "17pt"
        self.fig.xaxis.major_label_text_font_size = "15pt"
        self.fig.yaxis.major_label_text_font_size = "15pt"

    def __add_hover(self):
        self.fig.add_tools(HoverTool(tooltips=[("Plan Date", "@x{%F}"),
                                               ("Patient", "@id"),
                                               ("y", "@y"),
                                               ('Gamma Crit', "@gamma_crit"),
                                               ('Gamma Pass', '@gamma_index'),
                                               ('file', '@file_name')],
                                     formatters={'x': 'datetime'},
                                     renderers=[self.plot_data_1]))

    def __set_plot_attr(self):
        self.fig.title.align = 'center'

    def __set_x(self):
        self.x = self.data['date_time_obj']

    def __add_plot_data(self):
        self.plot_data_1 = self.fig.circle('x', 'y', source=self.source[1]['plot'], color='blue', size=8, alpha=0.4)
        self.plot_trend_1 = self.fig.line('x', 'y', source=self.source[1]['trend'], line_color='black', line_width=4)
        self.plot_avg_1 = self.fig.line('x', 'avg', source=self.source[1]['bound'], line_color='black')
        self.plot_patch_1 = self.fig.patch('x', 'y', source=self.source[1]['patch'], color='blue', alpha=0.2)

        # self.plot_data_2 = self.fig.circle('x', 'y', source=self.source[2]['plot'], color='red', size=4, alpha=0.3)
        # self.plot_trend_2 = self.fig.line('x', 'y', source=self.source[2]['trend'], line_color='black', line_width=4)
        # self.plot_avg_2 = self.fig.line('x', 'avg', source=self.source[2]['bound'], line_color='black')
        # self.plot_patch_2 = self.fig.patch('x', 'y', source=self.source[2]['patch'], color='red', alpha=0.2)

    def __add_legend(self):
        # Set the legend
        legend_plot = Legend(items=[("Data 1 ", [self.plot_data_1]),
                                    ("Avg 1 ", [self.plot_avg_1]),
                                    ("Rolling Avg 1 ", [self.plot_trend_1]),
                                    ("Percentile Region 1 ", [self.plot_patch_1])
                                    ],
                             orientation='horizontal')

        # Add the layout outside the plot, clicking legend item hides the line
        self.fig.add_layout(legend_plot, 'above')
        self.fig.legend.click_policy = "hide"

    def __add_histogram_data(self):
        self.histogram = figure(tools="", plot_width=1000, plot_height=275)
        # self.histogram.xaxis.axis_label_text_font_size = self.options.PLOT_AXIS_LABEL_FONT_SIZE
        # self.histogram.yaxis.axis_label_text_font_size = self.options.PLOT_AXIS_LABEL_FONT_SIZE
        # self.histogram.xaxis.major_label_text_font_size = self.options.PLOT_AXIS_MAJOR_LABEL_FONT_SIZE
        # self.histogram.yaxis.major_label_text_font_size = self.options.PLOT_AXIS_MAJOR_LABEL_FONT_SIZE
        # self.histogram.min_border_left = self.options.MIN_BORDER
        # self.histogram.min_border_bottom = self.options.MIN_BORDER
        self.vbar_1 = self.histogram.vbar(x='x', width='width', bottom=0, top='top', source=self.source[1]['hist'], alpha=0.5, color='blue')
        # self.vbar_2 = self.histogram.vbar(x='x', width='width', bottom=0, top='top', source=self.source[2]['hist'], alpha=0.5, color='red')

        self.histogram.xaxis.axis_label = ""
        self.histogram.yaxis.axis_label = "Frequency"

        self.histogram.xaxis.axis_label_text_font_size = "17pt"
        self.histogram.yaxis.axis_label_text_font_size = "17pt"
        self.histogram.xaxis.major_label_text_font_size = "15pt"
        self.histogram.yaxis.major_label_text_font_size = "15pt"

    def update_source(self, attr, old, new):
        for source_key in [1, 2]:
            new_data = {key: [] for key in ['x', 'y', 'id', 'gamma_crit', 'file_name', 'gamma_index']}
            active_gamma = [gamma_options[a] for a in checkbox_button_group.active]
            # if select_linac[source_key] != 'None':
            for i in range(len(self.x)):
                # if select_linac[source_key].value == 'All' or self.data['Radiation Dev'][i] == select_linac[source_key].value:
                if end_date_picker.value > self.x[i] > start_date_picker.value:
                    gamma_crit = "%s%%/%smm" % (self.data['Difference (%)'][i], self.data['Distance (mm)'][i])
                    if 'Any' in active_gamma or gamma_crit in active_gamma:
                        try:
                            new_data['y'].append(float(self.data[select_y.value][i]))
                        except ValueError:
                            continue

                        new_data['x'].append(self.x[i])
                        new_data['id'].append(self.data['Patient ID'][i])
                        new_data['gamma_crit'].append(gamma_crit)
                        new_data['file_name'].append(self.data['file_name'][i])
                        new_data['gamma_index'].append('%s%%' % self.data['% Passed'][i])
                        # new_data['daily_corr'].append(self.data['Daily Corr'][i])
                        # new_data['dta'].append('%s%%' % self.data['DTA'][i])

            try:
                y = new_data['y']
                text[source_key].text = "<b>Linac %s</b>: <b>Min</b>: %0.3f | <b>Low</b>: %0.3f | <b>Mean</b>: %0.3f | <b>Median</b>: %0.3f | <b>Upper</b>: %0.3f | <b>Max</b>: %0.3f" % \
                             (source_key, np.min(y), np.percentile(y, 25), np.sum(y)/len(y), np.percentile(y, 50), np.percentile(y, 75), np.max(y))
            except:
                text[source_key].text = "<b>Linac %s</b>" % source_key

            self.source[source_key]['plot'].data = new_data

            self.fig.yaxis.axis_label = select_y.value
            self.fig.xaxis.axis_label = 'Plan Date'

            self.update_histogram(source_key, bin_size=20)
            self.update_trend(source_key, int(float(avg_len_input.value)), float(percentile_input.value))
            self.ichart.update_plot()

    def update_histogram(self, source_key, bin_size=10):
        width_fraction = 0.9
        hist, bins = np.histogram(self.source[source_key]['plot'].data['y'], bins=bin_size)
        width = [width_fraction * (bins[1] - bins[0])] * bin_size
        center = (bins[:-1] + bins[1:]) / 2.
        self.source[source_key]['hist'].data = {'x': center, 'top': hist, 'width': width}

        self.histogram.xaxis.axis_label = select_y.value

    def update_trend(self, source_key, avg_len, percentile):
        x = self.source[source_key]['plot'].data['x']
        y = self.source[source_key]['plot'].data['y']
        if x and y:
            x_len = len(x)

            data_collapsed = collapse_into_single_dates(x, y)
            x_trend, y_trend = moving_avg(data_collapsed, avg_len)

            y_np = np.array(self.source[source_key]['plot'].data['y'])
            upper_bound = float(np.percentile(y_np, 50. + percentile / 2.))
            average = float(np.percentile(y_np, 50))
            lower_bound = float(np.percentile(y_np, 50. - percentile / 2.))

            self.source[source_key]['trend'].data = {'x': x_trend,
                                                     'y': y_trend,
                                                     'mrn': ['Avg'] * len(x_trend)}
            self.source[source_key]['bound'].data = {'x': [x[0], x[-1]],
                                                     'mrn': ['Series Avg'] * 2,
                                                     'upper': [upper_bound] * 2,
                                                     'avg': [average] * 2,
                                                     'lower': [lower_bound] * 2,
                                                     'y': [average] * 2}
            self.source[source_key]['patch'].data = {'x': [x[0], x[-1], x[-1], x[0]],
                                                     'y': [upper_bound, upper_bound, lower_bound, lower_bound]}
        else:
            self.source[source_key]['trend'].data = {'x': [],
                                                     'y': [],
                                                     'mrn': []}
            self.source[source_key]['bound'].data = {'x': [],
                                                     'mrn': [],
                                                     'upper': [],
                                                     'avg': [],
                                                     'lower': [],
                                                     'y': []}
            self.source[source_key]['patch'].data = {'x': [],
                                                     'y': []}


class PlotControlChart:
    """
    Generate plot for Control Chart frame
    """
    def __init__(self, main_plot):

        self.main_plot = main_plot

        self.y_axis_label = ''
        self.source = {'plot': ColumnDataSource(data=dict(x=[], y=[], mrn=[], color=[], alpha=[], dates=[],
                                                          gamma_index=[], daily_corr=[], gamma_crit=[], dta=[])),
                       'center_line': ColumnDataSource(data=dict(x=[], y=[], mrn=[])),
                       'ucl_line': ColumnDataSource(data=dict(x=[], y=[], mrn=[])),
                       'lcl_line': ColumnDataSource(data=dict(x=[], y=[], mrn=[])),
                       'bound': ColumnDataSource(data=dict(x=[], mrn=[], upper=[], avg=[], lower=[])),
                       'patch': ColumnDataSource(data=dict(x=[], y=[]))}

        self.figure = figure(plot_width=1000, plot_height=375)
        self.figure.xaxis.axis_label = "Study #"
        self.figure.xaxis.axis_label_text_font_size = "17pt"
        self.figure.yaxis.axis_label_text_font_size = "17pt"
        self.figure.xaxis.major_label_text_font_size = "15pt"
        self.figure.yaxis.major_label_text_font_size = "15pt"

        self.__add_plot_data()
        self.__add_hover()
        self.__create_divs()
        self.__add_legend()

    def __add_plot_data(self):
        self.plot_data = self.figure.circle('x', 'y', source=self.source['plot'],
                                            size=8, color='color', alpha='alpha')
        self.plot_data_line = self.figure.line('x', 'y', source=self.source['plot'], color='blue',
                                               line_dash='solid')
        self.plot_patch = self.figure.patch('x', 'y', color='blue', source=self.source['patch'], alpha=0.1)
        self.plot_center_line = self.figure.line('x', 'y', source=self.source['center_line'], alpha=1, color='black',
                                                 line_dash='solid')
        self.plot_lcl_line = self.figure.line('x', 'y', source=self.source['lcl_line'], alpha=1, color='red', line_dash='dashed')
        self.plot_ucl_line = self.figure.line('x', 'y', source=self.source['ucl_line'],  alpha=1, color='red', line_dash='dashed')

    def __add_hover(self):
        self.figure.add_tools(HoverTool(show_arrow=True,
                                        tooltips=[('ID', '@mrn'),
                                                  ('Date', '@dates{%F}'),
                                                  ('Study', '@x'),
                                                  ('Value', '@y{0.2f}'),
                                                  ("y", "@y"),
                                                  ('Gamma Crit', "@gamma_crit"),
                                                  ('Gamma Pass', '@gamma_index'),
                                                  ('file', '@file_name')
                                                  ],
                                        formatters={'dates': 'datetime'},
                                        renderers=[self.plot_data]))

    def __add_legend(self):
        # Set the legend
        legend_plot = Legend(items=[("Charting Variable   ", [self.plot_data]),
                                    ("Charting Variable Line  ", [self.plot_data_line]),
                                    ('Center Line   ', [self.plot_center_line]),
                                    ('UCL  ', [self.plot_ucl_line]),
                                    ('LCL  ', [self.plot_lcl_line])],
                             orientation='horizontal')

        # Add the layout outside the plot, clicking legend item hides the line
        self.figure.add_layout(legend_plot, 'above')
        self.figure.legend.click_policy = "hide"

    def __create_divs(self):
        self.div_center_line = Div(text='', width=175)
        self.div_ucl = Div(text='', width=175)
        self.div_lcl = Div(text='', width=175)

    def update_plot(self):

        self.y_axis_label = select_y.value
        self.figure.yaxis.axis_label = self.y_axis_label

        y = self.main_plot.source[1]['plot'].data['y']
        mrn = self.main_plot.source[1]['plot'].data['id']
        dates = self.main_plot.source[1]['plot'].data['x']
        gamma_crit = self.main_plot.source[1]['plot'].data['gamma_crit']
        gamma_index = self.main_plot.source[1]['plot'].data['gamma_index']
        # daily_corr = self.main_plot.source[1]['plot'].data['daily_corr']
        # dta = self.main_plot.source[1]['plot'].data['dta']
        file_name = self.main_plot.source[1]['plot'].data['file_name']
        x = list(range(len(dates)))

        center_line, ucl, lcl = get_control_limits(y)

        if select_y.value in ['% Passed', 'Gamma-Index', 'DTA'] and ucl > 100:
            ucl = 100

        colors = ['red', 'blue']
        alphas = [0.3, 0.4]
        color = [colors[ucl >= value >= lcl] for value in y]
        alpha = [alphas[ucl >= value >= lcl] for value in y]

        self.source['plot'].data = {'x': x, 'y': y, 'mrn': mrn, 'gamma_crit': gamma_crit, 'gamma_index': gamma_index,
                                    'color': color, 'alpha': alpha,
                                    'dates': dates, 'file_name': file_name}

        self.source['patch'].data = {'x': [x[0], x[-1], x[-1], x[0]],
                                     'y': [ucl, ucl, lcl, lcl]}
        self.source['center_line'].data = {'x': [min(x), max(x)],
                                           'y': [center_line] * 2,
                                           'mrn': ['center line'] * 2}

        self.source['lcl_line'].data = {'x': [min(x), max(x)],
                                        'y': [lcl] * 2,
                                        'mrn': ['center line'] * 2}
        self.source['ucl_line'].data = {'x': [min(x), max(x)],
                                        'y': [ucl] * 2,
                                        'mrn': ['center line'] * 2}

        self.div_center_line.text = "<b>Center line</b>: %0.3f" % center_line
        self.div_ucl.text = "<b>UCL</b>: %0.3f" % ucl
        self.div_lcl.text = "<b>LCL</b>: %0.3f" % lcl

    def clear_div(self):
        self.div_center_line.text = "<b>Center line</b>:"
        self.div_ucl.text = "<b>UCL</b>:"
        self.div_lcl.text = "<b>LCL</b>:"


data = import_csv(FILE_PATH, day_first=DAY_FIRST)
plot = Plot(data)
ichart = PlotControlChart(plot)
plot.ichart = ichart
ignored_y = ['Patient Last Name', 'Patient First Name', 'Patient ID', 'Plan Date', 'Dose Type', 'Radiation Dev',
             'Energy', 'file_name', 'Meas Uncertainty', 'Analysis Type', 'Notes']
y_options = [option for option in list(data) if option not in ignored_y]
select_y = Select(title='Y-variable:', value='% Passed', options=y_options)
select_y.on_change('value', plot.update_source)

# linacs = list(set(data['Radiation Dev']))
# linacs.sort()
# linacs.insert(0, 'All')
# linacs.append('None')
# select_linac = {key: Select(title='Linac %s:' % key, value='All', options=['All'], width=250) for key in [1, 2]}
# select_linac[2].value = 'None'
# select_linac[1].on_change('value', plot.update_source)
# select_linac[2].on_change('value', plot.update_source)

avg_len_input = TextInput(title='Avg. Len:', value='10', width=100)
avg_len_input.on_change('value', plot.update_source)

percentile_input = TextInput(title='Percentile:', value='90', width=100)
percentile_input.on_change('value', plot.update_source)


start_date_picker = DatePicker(title='Start Date:', value=plot.x[0])
end_date_picker = DatePicker(title='End Date:', value=plot.x[-1])
start_date_picker.on_change('value', plot.update_source)
end_date_picker.on_change('value', plot.update_source)

gamma_options = ['5.0%/3.0mm', '3.0%/3.0mm', '3.0%/2.0mm', 'Any']
checkbox_button_group = CheckboxButtonGroup(labels=gamma_options, active=[3])
checkbox_button_group.on_change('active', plot.update_source)

text = {key: Div() for key in [1, 2]}

plot.update_source(None, None, None)

layout = column(row(select_y, avg_len_input, percentile_input),
                row(start_date_picker, end_date_picker),
                row(Div(text='Gamma Criteria: '), checkbox_button_group),
                text[1],
                text[2],
                row(Spacer(width=10), plot.fig),
                Spacer(height=50),
                row(Spacer(width=10), plot.histogram),
                Spacer(height=50),
                row(Spacer(width=10), ichart.figure),
                row(ichart.div_center_line, ichart.div_ucl, ichart.div_lcl))


curdoc().add_root(layout)
curdoc().title = "ArcCheck Trending"
