from pdf_to_text import convert_pdf_to_txt


class MapcheckResult:
    def __init__(self, abs_file_path):

        try:
            text = convert_pdf_to_txt(abs_file_path)
        except:
            return False
        text = text.split('\n')
        self.text = text

        if not self.is_file_snc_mapcheck():
            return False

        self.date, self.hospital = [], []
        for row in text:
            if row.find('Date: ') > -1:
                self.date = row.strip('Date: ')
            if row.find('Hospital: ') > -1:
                self.hospital = row.strip('Hospital: ')

            if self.date and self.hospital:
                break

        self.qa_file_parameter = self.get_data_indicies('QA File Parameter')

        try:
            text.index('Absolute Dose Comparison')
            self.dose_comparison_type = 'Absolute Dose Comparison'
        except ValueError:
            self.dose_comparison_type = 'Relative Comparison'
        self.dose_comparison = self.get_data_indicies(self.dose_comparison_type)

        try:
            text.index('Summary (Gamma Analysis)')
            self.analysis_type = 'Gamma'
        except ValueError:
            self.analysis_type = 'DTA'
        self.summary = self.get_data_indicies('Summary (%s Analysis)' % self.analysis_type)

        if self.qa_file_parameter['Patient Name'] == 'Set1':
            print abs_file_path

    def get_data_indicies(self, data_group):
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
               self.qa_file_parameter['Patient ID'],
               self.qa_file_parameter['Plan Date'],
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

    def is_file_snc_mapcheck(self):

        find_these = {'QA File Parameter': False,
                      'Threshold (%)': False,
                      'Notes': False,
                      'Reviewed By :': False}

        for row in self.text:
            if row in list(find_these):
                find_these[row] = True

        answer = True
        for i in list(find_these):
            answer = answer * find_these[i]

        return answer

