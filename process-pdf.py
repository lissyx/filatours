# -*- coding: utf-8 -*-

from pdfminer.pdfparser import PDFParser, PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice
from pdfminer.converter import PDFConverter, TextConverter, XMLConverter
from pdfminer.layout import LTContainer, LTPage, LTText, LTLine, LTRect, LTCurve
from pdfminer.layout import LTFigure, LTImage, LTChar, LTTextLine
from pdfminer.layout import LTTextBox, LTTextBoxVertical, LTTextGroup
from pdfminer.layout import LAParams
from pdfminer.utils import enc, bbox2str, create_bmp
from cStringIO import StringIO

import re
import sys
import pprint
import datetime
import locale

import filbleu

pp = pprint.PrettyPrinter(indent=1)

def process_pdf(fp, line, ends):
	laparams = LAParams()
	# Create a PDF parser object associated with the file object.
	parser = PDFParser(fp)
	# Create a PDF document object that stores the document structure.
	doc = PDFDocument()
	# Connect the parser and document objects.
	parser.set_document(doc)
	doc.set_parser(parser)
	# Create a PDF resource manager object that stores shared resources.
	rsrcmgr = PDFResourceManager()
	# Create a PDF device object.
	# device = FilBleuPDFStopExtractor(rsrcmgr, line, ends)
	device = filbleu.FilBleuPDFScheduleExtractor(rsrcmgr=rsrcmgr, laparams=laparams)
	# Create a PDF interpreter object.
	interpreter = PDFPageInterpreter(rsrcmgr, device)
	# Process each page contained in the document.
	for page in doc.get_pages():
	    interpreter.process_page(page)
	fp.close()
	return device.close()

	# return device.get_result()

docs = [
	{
		'file': "3-dujardin.pdf",
		'line': "03",
		'ends': ['A', 'B'],
	},
	{
		'file': "9-garevinci.pdf",
		'line': "09",
		'ends': ['A', 'B'],
	},
	{
		'file': "08-lenine.pdf",
		'line': "08",
		'ends': ['A', 'B'],
	},
	{
		'file': "30-taillerie.pdf",
		'line': "30",
		'ends': [],
	},
]

for doc in docs:
	fd = open(doc['file'], 'rb')
	pdf = StringIO()
	pdf.write(fd.read())
	res = process_pdf(pdf, doc['line'], doc['ends'])
	pp.pprint(res)
	fd.close()
	pdf.close()
