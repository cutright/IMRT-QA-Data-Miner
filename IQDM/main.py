# -*- coding: utf-8 -*-
"""
main program for IMRT QA PDF report parser
Created on Thu May 30 2019
@author: Dan Cutright, PhD
"""

from __future__ import print_function
import sys
from utilities import process_files
from os.path import isdir


def main():

    if len(sys.argv) > 2:
        print("Too many arguments provided.")
        return

    if len(sys.argv) < 2:
        print("Please include an initial directory for scanning when calling.")
        return

    init_directory = sys.argv[1]
    if not isdir(init_directory):
        print("%s is not a valid path" % init_directory)
        return

    process_files(init_directory)


if __name__ == '__main__':
    main()
