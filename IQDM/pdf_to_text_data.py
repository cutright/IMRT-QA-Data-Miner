# -*- coding: utf-8 -*-
"""
Code adapted from Mark Amery's answer at:
https://stackoverflow.com/questions/22898145/how-to-extract-text-and-text-coordinates-from-a-pdf-file
Accessed August 8, 2019
"""

from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfpage import PDFTextExtractionNotAllowed
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice
from pdfminer.layout import LAParams
from pdfminer.converter import PDFPageAggregator
import pdfminer


class CustomPDFParser:
    def __init__(self, file_path, verbose=False):
        self.page = []
        self.file_path = file_path
        self.convert_pdf_to_text(verbose=verbose)
        self.data = []

    def print(self):
        for p, page in enumerate(self.page):
            print("Page %s" % (p+1))
            page.print()

    def print_block(self, page, index):
        self.page[page].print_block(index)

    def get_block_data(self, page, index):
        return self.page[page].get_block_data(index)

    def get_block_data_with_y(self, page, y):
        return self.page[page].get_block_data_with_y(y)

    def convert_pdf_to_text(self, verbose=False):

        # Open a PDF file.
        fp = open(self.file_path, 'rb')

        # Create a PDF parser object associated with the file object.
        parser = PDFParser(fp)

        # Create a PDF document object that stores the document structure.
        # Password for initialization as 2nd parameter
        document = PDFDocument(parser)

        # Check if the document allows text extraction. If not, abort.
        if not document.is_extractable:
            raise PDFTextExtractionNotAllowed

        # Create a PDF resource manager object that stores shared resources.
        rsrcmgr = PDFResourceManager()

        # Create a PDF device object.
        device = PDFDevice(rsrcmgr)

        # BEGIN LAYOUT ANALYSIS
        # Set parameters for analysis.
        laparams = LAParams()

        # Create a PDF page aggregator object.
        device = PDFPageAggregator(rsrcmgr, laparams=laparams)

        # Create a PDF interpreter object.
        interpreter = PDFPageInterpreter(rsrcmgr, device)

        # loop over all pages in the document
        for p, page in enumerate(PDFPage.create_pages(document)):
            # read the page into a layout object
            interpreter.process_page(page)
            layout = device.get_result()

            # extract text from this object
            page_data = {'x': [], 'y': [], 'text': []}
            self.page.append(PDFPageParser(layout._objs, page_data, verbose=verbose))


class PDFPageParser:
    def __init__(self, lt_objs, page_data, verbose=False):
        self.lt_objs = lt_objs
        self.data = page_data
        self.verbose = verbose

        self.parse_obj(lt_objs)
        self.sort_all_data_by_y()
        self.sub_sort_all_data_by_x()

    def parse_obj(self, lt_objs):
        # loop over the object list
        for obj in lt_objs:
            # if it's a textbox, print text and location
            if isinstance(obj, pdfminer.layout.LTTextBoxHorizontal):
                if self.verbose:
                    print("%6d, %6d, %s" % (obj.bbox[0], obj.bbox[1], obj.get_text().replace('\n', '_')))
                self.data['x'].append(round(obj.bbox[0], 2))
                self.data['y'].append(round(obj.bbox[1], 2))
                # self.data['text'].append(obj.get_text().replace('\n', '_'))
                self.data['text'].append(obj.get_text())
            # if it's a container, recurse
            elif isinstance(obj, pdfminer.layout.LTFigure):
                self.parse_obj(obj._objs)

    def sort_all_data_by_y(self):
        self.sort_all_data('y', reverse=True)

    def sub_sort_all_data_by_x(self):
        for y in set(self.data['y']):
            # for a given y, collect all indices, y, and text values with given y
            indices, x, text = [], [], []
            for i, y_ in enumerate(self.data['y']):
                if y_ == y:
                    indices.append(i)
                    x.append(self.data['x'][i])
                    text.append(self.data['text'][i])

            for sort_index, data_index in enumerate(self.get_sorted_indices(x)):
                self.data['x'][indices[sort_index]] = x[data_index]
                self.data['text'][indices[sort_index]] = text[data_index]

    def sort_all_data(self, sort_key, reverse=False):
        sorted_indices = self.get_sorted_indices(self.data[sort_key], reverse=reverse)

        for key in list(self.data):
            self.data[key] = [self.data[key][i] for i in sorted_indices]

    @staticmethod
    def get_sorted_indices(some_list, reverse=False):
        return [i[0] for i in sorted(enumerate(some_list), key=lambda x: x[1], reverse=reverse)]

    def get_coordinates(self, index):
        return [self.data[key][index] for key in ['x', 'y']]

    def print(self):
        for index, text in enumerate(self.data['text']):
            coord = self.get_coordinates(index)
            print("x:%s\ty:%s\n%s" % (coord[0], coord[1], text))

    def print_block(self, index):
        coord = self.get_coordinates(index)
        print("x:%s\ty:%s\n%s" % (coord[0], coord[1], (self.data['text'][index])))

    def get_block_data(self, index):
        coord = self.get_coordinates(index)
        return coord[0], coord[1], self.data['text'][index]

    def get_block_data_with_y(self, y, exact=False):
        tolerance = 20
        block_data = []
        for i, data in enumerate(self.data['text']):
            if exact:
                if int(self.data['y'][i]) == y:
                    block_data.append(data)
            else:
                if y + tolerance > int(self.data['y'][i]) > y - tolerance:
                    block_data.append(data)
        return block_data
