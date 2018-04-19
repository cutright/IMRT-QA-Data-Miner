from __future__ import print_function
from qa_parser import pdf_to_qa_result
import os
import sys
from datetime import datetime


def process_data(init_directory, results_file):

    with open(results_file, "w") as csv:
        columns = ['Patient Name',
                   'Patient ID',
                   'Plan Date',
                   'Dose Type',
                   'Difference (%)',
                   'Distance(mm)',
                   'Threshold (%)',
                   'Meas Uncertainty',
                   'Analysis Type',
                   'Total Points',
                   'Passed',
                   'Failed',
                   '% Passed\n']
        csv.write(','.join(columns))

    # Set the directory you want to start from
    for dirName, subdirList, fileList in os.walk(init_directory):
        for fname in fileList:
            if fname.find('.pdf') > -1:
                try:
                    row = pdf_to_qa_result(os.path.join(dirName, fname))
                    if row:
                        with open(results_file, "a") as csv:
                            csv.write(row + '\n')
                        print("Processed: %s" % os.path.join(dirName, fname))
                    else:
                        print("Non-compatible PDF detected: %s" % os.path.join(dirName, fname))
                except:
                    print("Non-compatible PDF detected: %s" % os.path.join(dirName, fname))


def main():

    if len(sys.argv) < 2:
        print("Please enter an initial directory for scanning.")
        return

    if not os.path.isdir(sys.argv[1]):
        print("Invalid directory: %s" % sys.argv[1])
        return

    init_directory = sys.argv[1]

    if len(sys.argv) == 3:
        output_file = sys.argv[2]
    else:
        output_file = "results_%s.txt" % str(datetime.now()).replace(':', '-').replace('.', '-')

    process_data(init_directory, output_file)


if __name__ == '__main__':
    main()
