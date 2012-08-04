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

pp = pprint.PrettyPrinter(indent=1)

class FilBleuPDFStopExtractor(TextConverter):
	def __init__(self, rsrcmgr, line, ends, codec='utf-8', pageno=1, laparams=None, showpageno=False):
		PDFConverter.__init__(self, rsrcmgr, None, codec=codec, pageno=pageno, laparams=laparams)
		self.showpageno = showpageno
		self.line = line
		self.ends = ends
		self.inbuf = ""
		self.foundline = False
		self.foundends = not(len(self.ends) > 0)
		self.currentLine = ""
		self.identified = False
		self.identifier = ""
		self.result = None
		self.periods = {}
		return

	def try_foundline(self):
		if self.inbuf.find(self.line) == 0:
			self.foundline = True
			self.currentLine = self.inbuf
			self.inbuf = ""
		return

	def try_foundends(self):
		for end in self.ends:
			if self.inbuf.find(end) == 0:
				self.foundends = True
				self.inbuf = ""
		return

	def try_identified(self):
		if self.inbuf.find("ARRÊT") > 0:
			self.identifier = self.inbuf.replace("ARRÊT", "")
			self.identified = True
			self.inbuf = ""
		return

	def specs_to_periods(self, specs):
		# print "specs=", specs
		full_periods = []
		for multi in specs.split(" et du "):
			speriod = []
			for submulti in multi.strip().split(" au "):
				speriod += [ submulti.replace("du ", "").strip() ]
			full_periods += [ speriod ]
		return full_periods
	
	def extract_periods(self, data):
		for component in data:
			periods = component.split("horaires valables")[1:]
			for period in periods:
				(specs, horaires) = period[:period.find("5h")], period[period.find("5h"):]
				full_periods = self.specs_to_periods(specs)
				print "full_periods=", full_periods
				print "horaires=", horaires
	
	def try_period(self):
		data = self.inbuf
		data_lundi = re.sub(r"Dimanche et jours fériés.*", "", data).split("Lundi au Samedi ")[1:]
		data_dimanche = re.sub(r".*Dimanche et jours fériés", "Dimanche et jours fériés", data).split("Dimanche et jours fériés")[1:]

		# print "lundi:", data_lundi
		# print "dimanche:", data_dimanche
		
		self.extract_periods(data_lundi)
		self.extract_periods(data_dimanche)

		return

	def write_text(self, text):
		self.inbuf += text.encode(self.codec, 'ignore')
		if not self.foundline:
			self.try_foundline()
		else:
			if not self.identified:
				self.try_identified()
		# self.try_period()
		return

	def end_page(self, page):
		TextConverter.end_page(self, page)
		self.process()
		self.try_period()

	def process(self):
		ident = self.identifier
		poslist = []
		result = []

		if len(self.ends) == 0:
			self.ends = [""]

		for end in self.ends:
			pos = ident.find(end + "Vers ")
			if pos >= 0:
				poslist.append({'end': end, 'pos': pos})

		poslist.reverse()
		for p in poslist:
			key = p['end'] + "Vers "
			str = ident[p['pos']:]
			ident = ident.replace(str, "")
			final = str.replace(key, "")
			result.append({'number': self.currentLine, 'end': p['end'], 'name': final})
		self.result = result

	def get_result(self):
		return self.result

class FilBleuPDFScheduleExtractor(PDFConverter):

	def __init__(self, rsrcmgr, codec='utf-8', pageno=1, laparams=None, showpageno=False):
		PDFConverter.__init__(self, rsrcmgr, None, codec=codec, pageno=pageno, laparams=laparams)
		self.outfp = sys.stdout
		self.current_schedule_hours_buckets = []
		self.current_schedule = 0
		self.schedules = []
		self.needMerge = False
		return
	
	def bbox_intersect_schedule(self, hour, minute):
		middle = (minute['x0'] + minute['x1']) / 2.0
		return (middle >= hour['x0'] and middle <= hour['x1'])

	def specs_to_periods(self, specs):
		# print "specs=", specs
		full_periods = []
		for multi in specs.split(" et du "):
			speriod = []
			for submulti in multi.strip().split(" au "):
				speriod += [ submulti.replace("du ", "").strip() ]
			full_periods += [ speriod ]
		return full_periods
	
	def extract_periods(self, data):
		full_periods = []
		periods = data.split("horaires valables")[1:]
		for period in periods:
			full_periods = self.specs_to_periods(period)
		return full_periods

	def write_header(self):
		self.outfp.write('<?xml version="1.0" encoding="%s" ?>\n' % self.codec)
		self.outfp.write('<pages>\n')
		return

	def write_footer(self):
		self.outfp.write('</pages>\n')
		return
	
	def write_text(self, text):
		self.outfp.write(enc(text, self.codec))
		return

	def receive_layout(self, ltpage):
		def show_group(item):
			if isinstance(item, LTTextBox):
				pass
				# self.outfp.write('<textbox id="%d" bbox="%s" />\n' % (item.index, bbox2str(item.bbox)))
			elif isinstance(item, LTTextGroup):
				#self.outfp.write('<textgroup bbox="%s">\n' % bbox2str(item.bbox))
				for child in item:
					show_group(child)
				#self.outfp.write('</textgroup>\n')
			return
		def render(item):
			if isinstance(item, LTPage):
				# self.outfp.write('<page id="%s" bbox="%s" rotate="%d">\n' % (item.pageid, bbox2str(item.bbox), item.rotate))
				for child in item:
					render(child)
				if item.groups is not None:
					#self.outfp.write('<layout>\n')
					for group in item.groups:
						show_group(group)
					#self.outfp.write('</layout>\n')
				# self.outfp.write('</page>\n')
			elif isinstance(item, LTLine):
				pass
				#self.outfp.write('<line linewidth="%d" bbox="%s" />\n' % (item.linewidth, bbox2str(item.bbox)))
			elif isinstance(item, LTRect):
				pass
				#self.outfp.write('<rect linewidth="%d" bbox="%s" />\n' % (item.linewidth, bbox2str(item.bbox)))
			elif isinstance(item, LTCurve):
				pass
				#self.outfp.write('<curve linewidth="%d" bbox="%s" pts="%s"/>\n' % (item.linewidth, bbox2str(item.bbox), item.get_pts()))
			elif isinstance(item, LTFigure):
				pass
				#self.outfp.write('<figure name="%s" bbox="%s">\n' % (item.name, bbox2str(item.bbox)))
				#for child in item:
				#	render(child)
				#self.outfp.write('</figure>\n')
			elif isinstance(item, LTTextLine):
				#self.outfp.write('<textline bbox="%s">' % bbox2str(item.bbox))
				txt = ""
				for child in item:
					if isinstance(child, LTChar):
						txt += enc(child.get_text(), self.codec)
				
				# print txt

				if txt.find("Vers ") >= 0:
					self.current_line_number = txt.split("Vers ")[0]
					return
				
				if txt.find("Lundi au Samedi") >= 0 or txt.find("Dimanche et jours fériés") >= 0:
					self.current_schedule = len(self.schedules)
					self.schedules.append({
						'period': "",
						'dates': [],
						'schedule': {},
						'lines': [ {'coords': None, 'number': self.current_line_number} ],
						'notes': {},
					})
					self.schedules[self.current_schedule]['period'] = txt.strip()
				else:
					try:
						if self.schedules[self.current_schedule]:
							pass
					except IndexError as e:
						return

					if txt.find("horaires valables") >= 0:
						self.schedules[self.current_schedule]['dates'] = self.extract_periods(txt.replace("er", "").strip())
						self.current_schedule_hours_buckets = []
					else:
						if len(self.schedules[self.current_schedule]['period']) > 0 and len(self.schedules[self.current_schedule]['dates']) > 0:
							(x0, y0, x1, y1) = item.bbox
							coords = {'x0': x0, 'y0': y0, 'x1': x1, 'y1': y1}

							# lines numbers are x0=29.09 and x1=43.762
							if (x0 >= 28 and x1 <= 44):
								if len(self.schedules[self.current_schedule]['lines']) == 1:
									if self.schedules[self.current_schedule]['lines'][0]['coords'] == None:
										self.schedules[self.current_schedule]['lines'] = [ {'number': txt, 'coords': coords} ]
									else:
										self.schedules[self.current_schedule]['lines'].append({'number': txt, 'coords': coords})
								else:
									self.schedules[self.current_schedule]['lines'].append({'number': txt, 'coords': coords})
							else:
								# notes are y0=81.491 y1=89.583
								if coords['y0'] > 85 and coords['y1'] > 95:
									if txt.find("h") > 0:
										txt = txt.replace("h", "")
										self.current_schedule_hours_buckets.append({'hour': txt, 'coords': coords})
										self.schedules[self.current_schedule]['schedule'][txt] = []
									else:
										for hbucket in self.current_schedule_hours_buckets:
											if self.bbox_intersect_schedule(minute=coords, hour=hbucket['coords']):
												self.schedules[self.current_schedule]['schedule'][hbucket['hour']].append({ 'minute': txt, 'coords': coords })
								else:
									start = re.compile(r"^([a-z] )").search(txt)
									if start:
										self.last_note_key = start.group(1).strip()
										txt = txt.replace(start.group(1), "")
										self.schedules[self.current_schedule]['notes'][self.last_note_key] = txt
									else:
										self.schedules[self.current_schedule]['notes'][self.last_note_key] += " " + txt
					
				#self.outfp.write('</textline>\n')
			elif isinstance(item, LTTextBox):
				wmode = ''
				if isinstance(item, LTTextBoxVertical):
					wmode = ' wmode="vertical"'
				#self.outfp.write('<textbox id="%d" bbox="%s"%s>\n' % (item.index, bbox2str(item.bbox), wmode))
				for child in item:
					render(child)
				#self.outfp.write('</textbox>\n')
			elif isinstance(item, LTChar):
				pass
				#self.outfp.write('<text font="%s" bbox="%s" size="%.3f">' % (enc(item.fontname), bbox2str(item.bbox), item.size))
				#self.write_text(item.get_text())
				#self.outfp.write('</text>\n')
			elif isinstance(item, LTText):
				pass
				#self.outfp.write('<text>%s</text>\n' % item.get_text())
			elif isinstance(item, LTImage):
				pass
##				if self.outdir:
##					name = self.write_image(item)
##					self.outfp.write('<image src="%s" width="%d" height="%d" />\n' %
##									 (enc(name), item.width, item.height))
##				else:
##					self.outfp.write('<image width="%d" height="%d" />\n' %
##									 (item.width, item.height))
			else:
				assert 0, item
			return
		render(ltpage)
		return
	
	def get_matching_line_number(self, schedule, minute):
		if len(schedule['lines']) > 1:
			for line in schedule['lines']:
				if line['coords'] is not None:
					(ly0, ly1) = (line['coords']['y0'], line['coords']['y1'])
					(my0, my1) = (minute['coords']['y0'], minute['coords']['y1'])
					n = line['number']
					# print "(ly0, ly1) = (%(ly0)f, %(ly1)f) ; (my0, my1) = (%(my0)f, %(my1)f)" % {'ly0': ly0, 'ly1': ly1, 'my0': my0, 'my1': my1}
					if (my0 >= ly0 and my1 <= ly1):
						return n
		else:
			return schedule['lines'][0]['number']
	
	def merge_lines(self):
		for schedule in self.schedules:
			for h in schedule['schedule']:
				hour = schedule['schedule'][h]
				for minute in hour:
					minute['line'] = self.get_matching_line_number(schedule, minute)
					del minute['coords']

	def merge_notes(self):
		newNotes = {}
		for schedule in self.schedules:
			if len(schedule['notes']) > 0:
				newNotes = schedule['notes']

		if len(newNotes) > 0:
			for schedule in self.schedules:
				schedule['notes'] = newNotes

	def explode_notes(self):
		for schedule in self.schedules:
			for h in schedule['schedule']:
				hour = schedule['schedule'][h]
				for minute in hour:
					minute['notes'] = list(re.sub(r"[0-9]*", "", minute['minute']))
					minute['minute'] = re.sub(r"[a-z]*", "", minute['minute'])


	def close(self):
		self.merge_lines()
		self.merge_notes()
		self.explode_notes()
		pp.pprint(self.schedules)
		return

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
	device = FilBleuPDFScheduleExtractor(rsrcmgr=rsrcmgr, laparams=laparams)
	# Create a PDF interpreter object.
	interpreter = PDFPageInterpreter(rsrcmgr, device)
	# Process each page contained in the document.
	for page in doc.get_pages():
	    interpreter.process_page(page)
	device.close()
	fp.close()

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
	print res
	fd.close()
	pdf.close()
