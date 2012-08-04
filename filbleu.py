#!/usr/bin/env python # -*- coding: utf-8 -*-

import re
import sys
import mechanize
import cookielib
import argparse
import datetime
import BeautifulSoup
import unicodedata
import pyproj
import math
import copy
import difflib
import time
import datetime
import locale
import hashlib
import os

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
		return

	def write_text(self, text):
		self.inbuf += text.encode(self.codec, 'ignore')
		if not self.identified:
			self.try_identified()
		return

	def end_page(self, page):
		TextConverter.end_page(self, page)
		self.process()

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
			result.append({'number': self.line, 'end': p['end'], 'name': final})
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

	def process_dates(self):
		oldlocale = locale.getlocale()
		locale.setlocale(locale.LC_ALL, ('fr_FR', 'UTF-8'))
		for schedule in self.schedules:
			newInterval = []
			for interval in schedule['dates']:
				(begin, end) = interval
				arBegin = begin.split(" ")
				arEnd = end.split(" ")

				if len(arBegin) == 2:
					arBegin.append(arEnd[2])

				sBegin = " ".join(arBegin) + " 00:00:00"
				sEnd = " ".join(arEnd) + " 23:59:59"

				dBegin = datetime.datetime.strptime(sBegin, "%d %B %Y %H:%M:%S")
				dEnd = datetime.datetime.strptime(sEnd, "%d %B %Y %H:%M:%S")

				newInterval += [ [ dBegin, dEnd ] ]
			schedule['dates'] = newInterval
		locale.setlocale(locale.LC_ALL, oldlocale)

	def close(self):
		self.merge_lines()
		self.merge_notes()
		self.explode_notes()
		self.process_dates()
		return self.schedules

class JourneyPart:
	def __init__(self, type, mode, indication, time, duration):
		self.type = type
		self.mode = mode
		self.indic = indication
		self.time = time
		self.duration = duration

class Indication:
	def __init__(self, html):
		self.type = None
		self.line = None
		self.direction = None
		self.stop = None
		self.parse(html)

	def parse(self, html):
		take = re.compile(r"^Prendre").search(html.text)
		out = re.compile(r"^Descendre").search(html.text)
		bs = html.findAll('b')

		if take:
			self.type = "mount"
			self.line = bs[0].text
			self.direction = bs[1].text
			self.stop = bs[2].text

		if out:
			self.type = "umount"
			self.stop = bs[0].text

class BusStop:
	def __init__(self, name, linkbase):
		self.name = name
		self.linkbase = linkbase

	def parse_stopArea(self):
		search = re.compile(r"(.*)\|(.*)\|(.*)").search(self.stopArea)
		if search:
			self.id = search.group(1)
			self.stop_name = search.group(2)
			self.city = search.group(3)

	def set_stopArea(self, stopArea):
		self.stopArea = stopArea
		self.parse_stopArea()

class BusLine:
	def __init__(self, id, num):
		self.id = id
		self.number = num
		self.ends = []
		self.stops = []

	def add_stop(self, stop):
		self.stops.append(stop)

	def add_end(self, end):
		self.ends.append(end)
		if type(end) == list:
			for stop in end:
				self.add_stop(stop)
		else:
			self.add_stop(end)

class FilBleu:
	def __init__(self):
		self.browser = mechanize.Browser()
		self.cj = cookielib.LWPCookieJar()
		self.browser.set_cookiejar(self.cj)
		self.base    = "http://www.filbleu.fr/"
		self.baseurl = self.base + "page.php"
		self.url_raz = "&raz"
		self.periode = "&periode="
		self.current_id = ""
		self.etape = ""
		self.pdfs_dir = "pdfs"

		self.parser = argparse.ArgumentParser(description="FilBleu Scrapper")
		self.parser.add_argument("--list-lines", action="store_true", help="List lines")
		self.parser.add_argument("--list-stops", help="List stops of a line (format: n|M)")
		self.parser.add_argument("--list-stops-basic", action="store_true", help="When listing stops, just displaying without any filtering")
		self.parser.add_argument("--build-line", help="Build given line, using lines.txt and stops_coords.txt")
		self.parser.add_argument("--build-line-gpx", action="store_true", default=True, required=False, help="Build given line, output as GPX")
		self.parser.add_argument("--get-stop-coords", help="Get a stop GPS coordinates")
		self.parser.add_argument("--httpdebug", action="store_true", help="Show HTTP debug")
		journey = self.parser.add_argument_group("Journey")
		journey.add_argument("--journey", action="store_true", help="Compute journey")
		journey.add_argument("--stop-from", help="Departure station")
		journey.add_argument("--stop-to", help="Destination station")
		journey.add_argument("--way", type=int, help="Forward (1) or Backward (-1)")
		journey.add_argument("--date", help="Date")
		journey.add_argument("--hour", help="Hour")
		journey.add_argument("--min", help="Minute")
		journey.add_argument("--criteria", type=int, help="Criteria: (1) Fastest; (2) Min changes; (3) Min walking; (4) Min waiting")
		journey.add_argument("--bruteforce", action="store_true", help="Bruteforce find lines that goes between two specific stops. Needs --only-lines")
		journey.add_argument("--only-lines", help="When running --bruteforce only consider those lines (comma-separated: 09A,09B)")

		stopschedule = self.parser.add_argument_group("Stop schedule PDF Scrapping")
		stopschedule.add_argument("--stop-schedule", action="store_true", help="Process PDF stop schedule")
		stopschedule.add_argument("--line", help="Line")
		stopschedule.add_argument("--stop", help="Stop")

		self.args = self.parser.parse_args()

		self.browser.set_debug_http(self.args.httpdebug)

		self.__process__()

	def strip_accents(self, s):
		return ''.join((c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn'))

	# in navitia, lat is first (and east) and lon is second (and north)
	def lambert2c_to_deg(self, lat, lon):
		wgs84 = pyproj.Proj('+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs')
		# navitia lambert 2c: http://code.google.com/p/pyproj/source/browse/trunk/lib/pyproj/data/IGNF?spec=svn162&r=162#266
		lambert2c = pyproj.Proj('+proj=lcc +nadgrids=ntf_r93.gsb,null +towgs84=-168.0000,-60.0000,320.0000 +a=6378249.2000 +rf=293.4660210000000 +pm=2.337229167 +lat_0=46.800000000 +lon_0=0.000000000 +k_0=0.99987742 +lat_1=46.800000000 +x_0=600000.000 +y_0=2200000.000 +units=m +no_defs')
		newlon, newlat = pyproj.transform(lambert2c, wgs84,lat,lon)
		return (newlat, newlon)

	def html_br_strip(self, text):
		return "".join([l.strip() for l in text.split("\n")])

	def datespan(self, startDate, endDate, delta=datetime.timedelta(days=1)):
		currentDate = startDate
		while currentDate < endDate:
			yield currentDate
			currentDate += delta

	def lines_to_lineSpec(self, line_to_build):
		lineSpecs = []
		getLineNumber = re.compile(r"number=(.*); ")
		for line in open('lines.txt').readlines():
			if line.startswith("Line(id=" + line_to_build + ")"):
				line = line.replace("Line(id=" + line_to_build + "): ", "")
				subparts = line.split("|")
				for subpart in subparts:
					number = getLineNumber.search(subpart)
					names = subpart.split(";")[1].replace("name=", "").replace("'", "").replace("{", "").replace("}", "").split(",")
					if number:
						ends = []
						for name in names:
							ends.append(name.strip())
						spec = "all"
						if number.group(1).count("A"):
							spec = "A"
						if number.group(1).count("B"):
							spec = "B"
						lineSpecs.append({'number': number.group(1), 'ends': ends, 'spec': spec})
		return lineSpecs

	def extract_stopArea(self, source, id, searchName):
		depart = source.find('input', attrs = {'id': id})
		stopArea = ""
		if depart:
			# stop is recognized; get WGS84/Lambert2+ coords
			stopArea = depart["value"]
		else:
			depart = source.find('select', attrs = {'id': id})
			# ok, we have to find the first stop
			if depart:
				optgroup = depart.find('optgroup')
				if optgroup:
					options = optgroup.findAll('option')
					if options:
						bestSim = 0
						bestValue = ""
						for option in options:
							sim = difflib.SequenceMatcher(a=searchName, b=option.text).ratio()
							if (sim > bestSim):
								bestSim = sim
								bestValue = option["value"]
						stopArea = bestValue
		return stopArea

	def process_pdf_stop(self, fp, line, ends):
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
		device = FilBleuPDFStopExtractor(rsrcmgr, line, ends)
		# Create a PDF interpreter object.
		interpreter = PDFPageInterpreter(rsrcmgr, device)
		# Process each page contained in the document.
		for page in doc.get_pages():
		    interpreter.process_page(page)
		device.close()
		fp.close()
		return device.get_result()

	def process_pdf_schedule(self, fp):
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
		fp.close()
		return device.close()

	def download_pdf(self, url):
		retval = None
		md5 = hashlib.md5(url.encode('utf-8')).hexdigest()
		fname = md5 + ".pdf"
		sys.stderr.write("Filename is: '" + fname + "'\n")
		try:
			with open(self.pdfs_dir + os.path.sep + fname, 'r') as f:
				retval = f.read()
		except IOError as e:
			self.browser.open(url.encode('utf-8'))
			response = self.browser.response()
			if response.code == 200:
				infos = response.info()
				isPdf = False

				for e in infos.keys():
					isPdf = (e == 'content-type' and infos[e] == 'application/pdf')

				if isPdf:
					retval = response.read()
					with open(self.pdfs_dir + os.path.sep + fname, 'w') as f:
						f.write(retval)
				else:
					noSchedule = re.compile(r"Aucun horaire n'existe").search(str(response.read()))
					if noSchedule:
						sys.stderr.write("No schedule for this one, bypassing.\n")
					else:
						sys.stderr.write("Not a PDF !\n")
						sys.stderr.write("Code=" + str(response.code) + "\n")
						sys.stderr.write(str(infos) + "\n")
						sys.stderr.write(str(response.read()) + "\n")
		return retval


	def pdfurl_to_line(self, url, line, ends):
		res = None
		pdf = StringIO()
		content = self.download_pdf(url)
		if content is not None:
			pdf.write(content)
			res = self.process_pdf_stop(pdf, line, ends)
		pdf.close()
		return res

	def page_lines(self):
		self.current_id = "1-2"
		self.etape = ""

	def page_stops(self):
		self.current_id = "1-2"
		self.etape = "2"

	def page_journey(self):
		self.current_id = "1-1"
		self.etape = ""

	def list_stops(self):
		self.get_stops()
		self.founds = {}
		for lineid in self.stops:
			ends = []
			line = ""
			olineid = lineid
			lineid = lineid.replace("A", "").replace("B", "").encode('utf-8')
			linespecs = self.lines_to_lineSpec(lineid)
			for lspec in linespecs:
				line = lspec['number'].replace("A", "").replace("B", "")
				if lspec['spec'] != "all":
					ends += lspec['spec']
			if len(ends) > 0:
				current = 0
				total = len(self.stops[olineid])
				for stop in self.stops[olineid]:
					stop_clean = stop.split(":")[0]
					s = self.stops[olineid][stop]
					url = (self.base + s.linkbase + "StopArea=" + s.stopArea)
					msg = "[%(current)d/%(total)d:%(lineid)s] Found stop %(stopName)s, downloading PDF at %(pdfURL)s\n" % {'stopName': s.stop_name, 'pdfURL': url, 'current': current, 'total': total, 'lineid': lineid}
					msg = msg.encode('utf-8')
					sys.stderr.write(msg)

					res = self.pdfurl_to_line(url, line, ends)
					if res != None:
						for r in res:
							try:
								self.founds[stop_clean] = {'stop': s, 'ends': list(set(self.founds[stop_clean]['ends']+[lineid+r['end']]))}
							except KeyError as e:
								self.founds[stop_clean] = {'stop': s, 'ends': [lineid+r['end']]}
					current += 1
			else:
				for stop in self.stops[olineid]:
					stop_clean = stop.split(":")[0]
					s = self.stops[olineid][stop]
					self.founds[stop_clean] = {'stop': s, 'ends': [ lineid ]}

		for found in self.founds:
			ff = self.founds[found]
			for e in ff['ends']:
				line = "Stop: %(stop_name)s (%(stop_city)s) => %(stop_area)s [%(lineid)s]\n" % { 'lineid': e, 'stop_name': ff['stop'].stop_name, 'stop_city': ff['stop'].city, 'stop_area': ff['stop'].stopArea }
				line = line.encode('utf-8')
				sys.stdout.write(line)

	def list_stops_complex(self):
		self.get_stops()
		self.specs = {}
		if len(self.stops.keys()) >= 1:
			self.newstops = {}
			for lineid in self.stops:
				origlineid = lineid
				lineid = str(int(lineid.replace("A", "").replace("B", "")))
				linespecs = self.lines_to_lineSpec(lineid)
				self.specs[lineid] = linespecs
				if len(linespecs) >= 2:
					for lspec in linespecs:
						self.newstops[lineid + lspec["spec"]] = self.stops[origlineid]
						self.newstops[lineid + lspec["spec"]] = self.stops[origlineid]
			if len(self.newstops) > 0:
				self.stops = self.newstops

		self.service = {}

		for lineid in self.stops:
			pureid = str(int(lineid.replace("A", "").replace("B", "")))
			expected = []
			currentSpec = None
			for spec in self.specs[pureid]:
				expected.append(spec['number'])
				if spec['spec'] != "all":
					if lineid.find(spec['spec']) > 0:
						currentSpec = spec
				else:
					currentSpec = spec

			startCity = ""
			startStop = unicode(currentSpec['ends'][0].decode('utf-8'))
			if startStop.find(" par ") != -1 or startStop.find(" puis ") != -1:
				split_par = startStop.split(" par ")
				tmproot = [ ]
				for sp in split_par:
					split_puis = sp.split(" puis ")
					tmproot += split_puis
				startStop = tmproot[0]

			bestSim = 0
			bestStop = ""
			bestCity = ""
			for stop in self.stops[lineid]:
				stop = self.stops[lineid][stop]
				sim = difflib.SequenceMatcher(a=startStop, b=stop.stop_name).ratio()
				if (sim > bestSim):
					bestSim = sim
					bestStop = stop.stop_name
					bestCity = stop.city
			startStop = bestStop
			startCity = bestCity

			i = 0
			for stop in self.stops[lineid]:
				stop = self.stops[lineid][stop]
				i += 1
				line = ""
				if (not self.args.list_stops_basic) and len(expected) > 1:
					msg = "[%(current)d/%(total)d] Expected: %(expected)s. Running %(lineid)s. Checking stop: '%(citystop)s - %(stop)s' from: '%(city)s - %(from)s'\n" % {'expected': expected, 'stop': stop.stop_name, 'citystop': stop.city, 'city': startCity, 'from': startStop, 'lineid': lineid, 'current': i, 'total': len(self.stops[lineid])}
					msg = msg.encode('utf-8')
					sys.stderr.write(msg)

					service = []
					key = startCity + startStop + stop.name
					try:
						service = self.service[key]
					except KeyError as e:
						sys.stderr.write("Need to retrieve from da web\n")
						dep = startCity + " - " + startStop
						arr = stop.city + " - " + stop.name
						if dep != arr:
							self.args.only_lines = ",".join(expected)
							service = self.bruteforce_find_lines(dep, arr)
							if len(currentSpec['ends']) == 1:
								sys.stderr.write("Round line, asking reverse.\n")
								service += self.bruteforce_find_lines(arr, dep)
								service = list(set(service))
								service.sort()
								sys.stderr.write("Finally found: " + str(service) + "\n")
						else:
							service = expected
						self.service[key] = service

					if currentSpec['number'] in service:
						line = "Stop: %(stop_name)s (%(stop_city)s) => %(stop_area)s [%(lineid)s]\n" % { 'lineid': lineid, 'stop_name': stop.stop_name, 'stop_city': stop.city, 'stop_area': stop.stopArea }
					else:
						sys.stderr.write("No this time, bro. Next time, it will be good.\n")
				else:
					line = "Stop: %(stop_name)s (%(stop_city)s) => %(stop_area)s [%(lineid)s]\n" % { 'lineid': lineid, 'stop_name': stop.stop_name, 'stop_city': stop.city, 'stop_area': stop.stopArea }
				line = line.encode('utf-8')
				sys.stdout.write(line)

	def get_stops_sens(self, sens):
		self.page_stops()
		self.raz()
		self.browser.select_form(name="form1")
		self.browser["Sens"] = [ str(sens) ]
		self.browser.submit()
		return BeautifulSoup.BeautifulSoup(self.browser.response().read())

	def get_stops(self):
		self.current_id = "1-2"
		self.raz()
		self.stops = {}
		linkBase = ""
		soups = [ self.get_stops_sens(1), self.get_stops_sens(-1) ]
		for soup in soups:
			sensInput = soup.find("input", attrs = {'name': 'Sens'})
			searchLinkBase = re.compile(r"grille-horaires.*\.php").search(soup.text)
			if searchLinkBase:
				linkBase = searchLinkBase.group(0) + "?Sens=" + sensInput["value"] + "&"

			sens = soup.find("form")
			stops = sens.findAll("option")
			for fs in sens.findAll("fieldset"):
				fs.clear()
			for t in sens.findAll("table"):
				t.clear()
			lineid = self.args.list_stops
			multi = self.html_br_strip(sens.getText())
			if multi.count(" |") == 1:
				search = re.compile(r"(.*) \|(.*)").search(multi)
				if search:
					lineid = self.args.list_stops + "" + search.group(1)
			if not lineid in self.stops.keys():
				self.stops[lineid] = {}
			for stop in stops:
				if not stop["value"] == "":
					s = BusStop(stop.text, linkBase)
					s.set_stopArea(stop["value"])
					self.stops[lineid][s.id+':'+sensInput["value"]] = s

	def list_lines(self):
		self.get_lines()
		for line in self.lines:
			line = self.lines[line]
			out = "Line(id=%(line_id)s): " % { 'line_id': line.id }
			# circular lines
			if len(line.ends) == 1:
				out += "number=%(line_number)s; name='%(ends)s'" % { 'line_number': line.number, 'ends': line.ends[0] }
			else:
				# classic, one end on both 
				if type(line.ends[0]) == unicode and type(line.ends[1]) == unicode:
					if line.ends[0].startswith("A |") or line.ends[0].startswith("B |") or line.ends[1].startswith("A |") or line.ends[1].startswith("B |"):
						AorB_end_one = line.ends[0].split("|")[0].strip()
						AorB_end_two = line.ends[1].split("|")[0].strip()
						out += "number=%(line_number)s; name={'%(end_one)s'}" % { 'line_number': line.number + AorB_end_one, 'end_one': line.ends[0].split("|")[1].strip() }
						out += " | number=%(line_number)s; name={'%(end_two)s'}" % { 'line_number': line.number + AorB_end_two, 'end_two': line.ends[1].split("|")[1].strip() }
					else:
						out += "number=%(line_number)s; name={'%(end_one)s','%(end_two)s'}" % { 'line_number': line.number, 'end_one': line.ends[0], 'end_two': line.ends[1] }
				else:
					# one side is good
					if type(line.ends[0]) == unicode:
						AorB_end_one = line.ends[1][0].split("|")[0].strip()
						AorB_end_two = line.ends[1][1].split("|")[0].strip()
						out += "number=%(line_number)s; name={'%(end_one)s','%(end_two)s'}" % { 'line_number': line.number + AorB_end_one, 'end_one': line.ends[0], 'end_two': line.ends[1][0].split("|")[1].strip() }
						out += " | number=%(line_number)s; name={'%(end_one)s','%(end_two)s'}" % { 'line_number': line.number + AorB_end_two, 'end_one': line.ends[0], 'end_two': line.ends[1][1].split("|")[1].strip() }
					if type(line.ends[1]) == unicode:
						AorB_end_one = line.ends[0][0].split("|")[0].strip()
						AorB_end_two = line.ends[0][1].split("|")[0].strip()
						out += "number=%(line_number)s; name={'%(end_one)s','%(end_two)s'}" % { 'line_number': line.number + AorB_end_one, 'end_one': line.ends[0], 'end_two': line.ends[0][0].split("|")[1].strip() }
						out += " | number=%(line_number)s; name={'%(end_one)s','%(end_two)s'}" % { 'line_number': line.number + AorB_end_two, 'end_one': line.ends[0], 'end_two': line.ends[0][1].split("|")[1].strip() }

					if type(line.ends[0]) == list and type(line.ends[1]) == list:
						end_one_first = ""
						end_one_second = ""
						end_two_first = ""
						end_two_second = ""
						AorB_end_one_first = line.ends[0][0].split("|")[0].strip()
						AorB_end_two_first = line.ends[0][1].split("|")[0].strip()
						AorB_end_one_second = line.ends[1][0].split("|")[0].strip()
						AorB_end_two_second = line.ends[1][1].split("|")[0].strip()

						if AorB_end_one_first == 'A' and AorB_end_one_second == 'A':
							end_one_first = line.ends[0][0].split("|")[1].strip()
							end_two_first = line.ends[1][0].split("|")[1].strip()

						if AorB_end_two_first == 'B' and AorB_end_two_second == 'B':
							end_one_second = line.ends[0][1].split("|")[1].strip()
							end_two_second = line.ends[1][1].split("|")[1].strip()

						out += "number=%(line_number)s; name={'%(end_one)s','%(end_two)s'}" % { 'line_number': line.number + 'A', 'end_one': end_one_first, 'end_two': end_two_first }
						out += " | number=%(line_number)s; name={'%(end_one)s','%(end_two)s'}" % { 'line_number': line.number + 'B', 'end_one': end_one_second, 'end_two': end_two_second }

			out += "\n"
			out = out.encode('utf-8')
			sys.stdout.write(out)

	def get_lines(self):
		self.page_lines()
		self.raz()
		self.lines = {}
		soup = BeautifulSoup.BeautifulSoup(self.browser.response().read())
		for line in soup.findAll('a', attrs = { 'style': 'text-decoration:none' }):
			search = re.compile(r"Line=(.*)\|(.*)").search(line['href'])
			if search:
				lineid = search.group(1)
				linenb = search.group(2)

				if not self.lines.has_key(lineid):
					self.lines[lineid] = BusLine(id=lineid, num=linenb)

				divs = line.findAll('div')
				if divs:
					stops = []
					for div in divs:
						stop = self.html_br_strip(div.text)
						if len(divs) > 1:
							stops.append(stop)
						else:
							stops = stop
					self.lines[lineid].add_end(stops)
				else:
					stop = self.html_br_strip(line.text)
					if len(stop) > 0:
						self.lines[lineid].add_end(stop)

	def get_stop_coords(self):
		self.journeys = []
		self.page_journey()
		self.raz()
		self.browser.select_form(name="formulaire")
		self.browser["Departure"] = self.strip_accents(unicode(self.args.get_stop_coords, "UTF-8"))
		self.browser["Arrival"] = "Unknwonstop"
		self.browser["Sens"] = [ "1" ]
		self.browser["Date"] = "42/42/2042"
		self.browser["Hour"] = [ "13" ]
		self.browser["Minute"] = [ "35" ]
		self.browser["Criteria"] = [ "1" ]
		self.browser.submit()
		soup = BeautifulSoup.BeautifulSoup(self.browser.response().read())
		form = soup.find('form', attrs = {'name': 'formulaire'})
		if form:
			stopArea = self.extract_stopArea(form, 'Departure', self.strip_accents(unicode(self.args.get_stop_coords, "UTF-8")))
			values = stopArea.replace(",", ".").split("|")
			east = float(values[6])
			north = float(values[7])

			(degrees_e, degrees_n) = self.lambert2c_to_deg(east, north)

			l = "Found a stop matching stopArea: [%(stop_area)s]; Lambert2+: {E:%(lb2p_e)f, N:%(lb2p_n)f}; Degrees: {E:%(degrees_e)f, N:%(degrees_n)f}\n" % {'stop_area': stopArea, 'lb2p_e': east, 'lb2p_n': north, 'degrees_e': degrees_e, 'degrees_n': degrees_n}
			l = l.encode('utf-8')
			sys.stdout.write(l)
		else:
			print "No form result."

	def get_journeys(self):
		self.journeys = []
		self.page_journey()
		self.raz()
		self.browser.select_form(name="formulaire")
		self.browser["Departure"] = self.strip_accents(self.args.stop_from)
		self.browser["Arrival"] = self.strip_accents(self.args.stop_to)
		self.browser["Sens"] = [ str(self.args.way) ]
		self.browser["Date"] = str(self.args.date)
		self.browser["Hour"] = [ str(self.args.hour) ]
		self.browser["Minute"] = [ str(self.args.min) ]
		self.browser["Criteria"] = [ str(self.args.criteria) ]
		self.browser.submit()
		soup = BeautifulSoup.BeautifulSoup(self.browser.response().read())
		stopAreaDep = self.extract_stopArea(soup, 'Departure', self.strip_accents(self.args.stop_from))
		stopAreaArr = self.extract_stopArea(soup, 'Arrival', self.strip_accents(self.args.stop_to))
		if stopAreaDep != "" or stopAreaArr != "":
			self.page_journey()
			self.raz()
			self.browser.select_form(name="formulaire")
			self.browser["Departure"] = self.strip_accents(stopAreaDep)
			self.browser["Arrival"] = self.strip_accents(stopAreaArr)
			self.browser["Sens"] = [ str(self.args.way) ]
			self.browser["Date"] = str(self.args.date)
			self.browser["Hour"] = [ str(self.args.hour) ]
			self.browser["Minute"] = [ str(self.args.min) ]
			self.browser["Criteria"] = [ str(self.args.criteria) ]
			self.browser.submit()
		soup = BeautifulSoup.BeautifulSoup(self.browser.response().read())
		navig = soup.find('div', attrs = {'class': 'navig'})
		if navig:
			table = soup.find('table', attrs = {'summary': 'Propositions'})
			if table:
				trips = table.findAll('tr')
				if trips:
					for trip in trips[1:]:
						tds = trip.findAll('td')
						dates = self.html_br_strip(tds[0].text)
						link = tds[1].find('a')["href"]
						duration = tds[2].text
						connections = tds[3].text

						departure = None
						arrival = None
						sDate = re.compile(r"D.part :(.*)Arriv.e :(.*)").search(dates)
						if sDate:
							departure = sDate.group(1)
							arrival = sDate.group(2)

						# print "Departure:", departure, "Arrival:", arrival, "Duration:", duration, "Connections:", connections, "[", link, "]"
						self.journeys.append({'departure': departure, 'arrival': arrival, 'duration': duration, 'connections': connections, 'link': link})
			else:
				print "No table"
		else:
			print soup.html()
			print "No journey."

	def get_journey(self, journey):
		if journey['link']:
			self.browser.open(self.base + journey['link'])
			soup = BeautifulSoup.BeautifulSoup(self.browser.response().read())
			itin = soup.find('fieldset', attrs = {'class': 'itineraire'})
			if itin:
				table = itin.find('table')
				if table:
					lines = table.findAll('tr')
					if lines:
						fulljourney = []
						for line in lines[1:]:
							tds = line.findAll('td')
							type = None
							mode = None
							indic = None
							time = None
							duration = None

							if len(tds) == 3:
								if tds[0]['class'] == "indication":
									type = "indication"
									indic = Indication(tds[0])
									time = tds[1].text
								if tds[0]['class'] == "correspondance":
									type = "connection"
									duration = tds[1].text

							if len(tds) == 5:
								mode = tds[0].img['alt']
								if tds[1]['class'] == "indication":
									type = "indication"
									indic = Indication(tds[1])
									time = tds[2].text
									duration = tds[3].text

							fulljourney.append(JourneyPart(type, mode, indic, time, duration))
						return fulljourney
					else:
						print "No lines"
				else:
					print "No journey table"
			else:
				print "No journey description"

	def list_journeys(self):
		self.get_journeys()
		for j in self.journeys:
			jd = self.get_journey(j)
			print "Printing journey:"
			for journey_part in jd:
				if journey_part.indic != None:
					print "	Type:", journey_part.type, " Mode:", journey_part.mode, " Time:", journey_part.time, " Duration:", journey_part.duration, " Action:", journey_part.indic.type, " Stop:", journey_part.indic.stop, " Direction:", journey_part.indic.direction, " Line:", journey_part.indic.line
				else:
					print "	Type:", journey_part.type, " Mode:", journey_part.mode, " Time:", journey_part.time, " Duration:", journey_part.duration
			print ""

	def bruteforce_find_lines(self, depStop, arrStop):
		only_lines = self.args.only_lines.split(",")
		self.lines_found = {}
		lastTime = ""
		if type(depStop) == str:
			depStop = unicode(depStop)
		if type(arrStop) == str:
			arrStop = unicode(arrStop)

		self.args.criteria = 2
		self.args.way = 1
		self.args.stop_from = depStop
		self.args.stop_to = arrStop
		dates = ['04/06/2012', '03/06/2012']
		for date_extract in dates:
			self.args.date = date_extract
			jour = time.strptime(date_extract, "%d/%m/%Y")
			for timestamp in self.datespan(datetime.datetime(jour.tm_year, jour.tm_mon, jour.tm_mday, 5, 0), datetime.datetime(jour.tm_year, jour.tm_mon, jour.tm_mday, 20, 0), delta=datetime.timedelta(seconds=15*60)):
				if (lastTime != ""):
					last = time.strptime(date_extract + " " + lastTime, "%d/%m/%Y %Hh%M")
					nexttime = datetime.datetime.fromtimestamp(time.mktime(last))
					if (timestamp < nexttime):
						continue
				sys.stderr.write("Date: " + str(timestamp) + "\n")
				only_lines_sort = only_lines
				only_lines_sort.sort()
				keys_sort = self.lines_found.keys()
				keys_sort.sort()
				if len(keys_sort) > 0 and only_lines_sort == keys_sort:
					sys.stderr.write("Successfully matched: " + str(keys_sort) + " with " + str(only_lines_sort) + "\n")
					sys.stderr.write("Found lines:" + str(self.lines_found.keys()) + "\n")
					return self.lines_found.keys()
				self.args.hour = timestamp.hour
				self.args.min = timestamp.minute
				self.get_journeys()
				for j in self.journeys:
					if j['connections'] == "Aucune":
						jd = self.get_journey(j)
						if len(jd) == 2:
							for journey_part in jd:
								if journey_part.mode == "Bus":
									lastTime = journey_part.time
									if journey_part.indic.line in only_lines:
										line = str(journey_part.indic.line)
										try:
											self.lines_found[line] += 1
										except KeyError as e:
											self.lines_found[line] = 1

		sys.stderr.write("Found lines:" + str(self.lines_found.keys()) + "\n")
		return self.lines_found.keys()

	def scrap_pdf_stop_schedule(self):
		self.args.list_stops = self.args.line
		self.get_stops()
		perform = True
		for lineid in self.stops:
			current = 0
			total = len(self.stops[lineid])
			for stop in self.stops[lineid]:
				s = self.stops[lineid][stop]
				if self.args.stop:
					perform = (self.args.stop.encode('utf-8') == s.stop_name)

				if perform:
					stop_clean = stop.split(":")[0]
					url = (self.base + s.linkbase + "StopArea=" + s.stopArea)
					msg = "[%(current)d/%(total)d:%(lineid)s] Found stop %(stopName)s, downloading PDF at %(pdfURL)s\n" % {'stopName': s.stop_name, 'pdfURL': url, 'current': current, 'total': total, 'lineid': lineid}
					msg = msg.encode('utf-8')
					sys.stderr.write(msg)
					pdf = StringIO()
					content = self.download_pdf(url)
					if content is not None:
						pdf.write(content)
						res = self.process_pdf_schedule(pdf)
						print res
					pdf.close()
				current += 1

	def raz(self):
		if not self.current_id == "":
			url = self.baseurl + "?id=" + self.current_id
			if not self.etape == "":
				url += "&etape=" + self.etape
				if self.args.list_stops:
					linespecs = self.lines_to_lineSpec(self.args.list_stops)
					line = ""
					for lspec in linespecs:
						line = lspec['number'].replace("A", "").replace("B", "")
					url += "&Line=" + self.args.list_stops + "|" + line
			else:
				url += self.url_raz
				today = datetime.date.today()
				start_ete = datetime.date(today.year, 7, 2)
				stop_ete = datetime.date(today.year, 9, 1)
				p = "1"
				if today >= start_ete and today <= stop_ete:
					p = "2"
				url += self.periode + p

			self.browser.open(url)
	
	def distance(self, p1, p2):
		R = 6378000.0
		sourcelatitude = (math.pi * p2['lat']) / 180.0;
		sourcelongitude = (math.pi * p2['lon']) / 180.0;
		latitude = (math.pi * p1['lat']) / 180.0;
		longitude = (math.pi * p1['lon']) / 180.0;
		return R * (math.pi/2 - math.asin( math.sin(latitude) * math.sin(sourcelatitude) + math.cos(longitude - sourcelongitude) * math.cos(latitude) * math.cos(sourcelatitude)));
	
	def build_line(self):
		line_to_build = self.args.build_line
		stopAreas = {}
		lineStops = {}
		lineStops["all"] = {}
		lineStops["A"] = {}
		lineStops["B"] = {}
		lineSpecs = []

		stopArea = re.compile(r"Found a stop matching stopArea: \[StopArea\|(.*)\|(.*)\|(.*)\|\|\|.*\|.*\|.*\]; Lambert2\+: {E:.*, N:.*}; Degrees: {E:(.*), N:(.*)}")
		for line in open('stops_coords.txt','r').readlines():
			if line.startswith("Found"):
				results = stopArea.search(line)
				if results:
					stopId   = results.group(1)
					stopName = results.group(2)
					cityName = results.group(3)
					lat = float(results.group(4))
					lon = float(results.group(5))
					stopAreas[stopId] = {'name': stopName, 'city': cityName, 'lat': lat, 'lon': lon}

		lineStop = re.compile(r"Stop:.*=> (.*)\|(.*)\|(.*) \[(.*)\]")
		for line in open('stops.' + line_to_build + '.txt','r').readlines():
			results = lineStop.search(line)
			if results:
				stopId   = results.group(1)
				stopName = results.group(2)
				cityName = results.group(3)
				subLine  = results.group(4)
				spec = "all"
				if subLine.count("A"):
					spec = "A"
				if subLine.count("B"):
					spec = "B"
				lineStops[spec][stopId] = {'name': stopName, 'city': cityName }

		lineSpecs = self.lines_to_lineSpec(line_to_build)

		print lineStops
		lineResults = []
		for lineSpec in lineSpecs:
			print "Dealing with:", lineSpec['number'], " spec:", lineSpec['spec']

			stopsVisited = []
			spec = "all"
			if len(lineStops[lineSpec['spec']]) > 0:
				spec = lineSpec['spec']
			localLineStops = copy.deepcopy(lineStops[spec])
			root1 = None
			root2 = None
			if len(lineSpec['ends']) > 1:
				(root1, root2) = lineSpec['ends']
			else:
				print "ends:", lineSpec['ends']
				root2 = lineSpec['ends'][0]

			print "root1=", root1
			print "root2=", root2

			if root2.find(" par ") != -1 or root2.find(" puis ") != -1:
				split_par = root2.split(" par ")
				print "par::", split_par
				tmproot = [ ]
				for sp in split_par:
					split_puis = sp.split(" puis ")
					tmproot += split_puis
					print "puis::", split_puis
				print "tmproot::", tmproot
				root2 = tmproot

			if type(root1) == str:
				root1 = [ root1 ]

			if type(root2) == str:
				root2 = [ root2 ]

			# find the target
			bestTgtSim = 0
			bestTgtValue = None
			bestTgtKey = None
			for rooteval in root1:
				for stop in localLineStops.items():
					(key, value) = stop
					sim = difflib.SequenceMatcher(a=rooteval, b=value['name']).ratio()
					if (sim > bestTgtSim):
						bestTgtSim = sim
						bestTgtValue = stop
						bestTgtKey = key

			print "bestTgtSim=", bestTgtSim
			print "bestTgtValue=", bestTgtValue
			print "bestTgtKey=", bestTgtKey

			# find the root
			bestSim = 0
			bestValue = None
			bestKey = None
			for rooteval in root2:
				for stop in localLineStops.items():
					(key, value) = stop
					sim = difflib.SequenceMatcher(a=rooteval, b=value['name']).ratio()
					if (sim > bestSim):
						bestSim = sim
						bestValue = stop
						bestKey = key

			print "bestSim=", bestSim
			print "bestValue=", bestValue
			print "bestKey=", bestKey

			stopsVisited.append(bestValue)
			del localLineStops[bestKey]
			
			print "init:", stopsVisited

			# populate
			cont = True
			while (cont):
				minDist = 32768
				closeStop = None
				closeId = -1
				(lastId, lastStop) = stopsVisited[-1]
				for stop in localLineStops.items():
					(key, value) = stop
					d = self.distance({'lat': stopAreas[lastId]['lat'], 'lon': stopAreas[lastId]['lon']}, {'lat': stopAreas[key]['lat'], 'lon': stopAreas[key]['lon']})
					if d < minDist:
						minDist = d
						closeStop = stop
						closeId = key

				# print "last:", lastStop
				# print "closest:", closeStop

				stopsVisited.append(closeStop)
				del localLineStops[closeId]

				if len(localLineStops) == 0:
					cont = False
					break

				(key, value) = closeStop
				if value['name'] == root1:
					cont = False
					break

			print "visited:", stopsVisited
			lineResults.append({'number': lineSpec['number'], 'visited': stopsVisited})

		if self.args.build_line_gpx:
			for lineResult in lineResults:
				f = open('filbleu_route.' + lineResult['number'] + '.gpx', 'w')
				f.write('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><gpx version="1.1" creator="FilBleu Scrapper"><metadata>Filbleu ligne ' + lineSpec['number'] + '</metadata><trk><trkseg>')
				for (key, val) in lineResult['visited']:
					f.write('<trkpt lat="' + str(stopAreas[key]['lat']) + '" lon="' + str(stopAreas[key]['lon']) + '"><ele>0.0</ele><name>' + val['name'] + '</name><time>0</time></trkpt>')
				f.write('</trkseg></trk></gpx>')
				f.close()

	def __process__(self):
		if self.args.list_lines:
			self.list_lines()
		if self.args.list_stops:
			self.list_stops()
		if self.args.get_stop_coords:
			self.get_stop_coords()
		if self.args.journey:
			self.list_journeys()
		if self.args.bruteforce:
			self.bruteforce_find_lines(self.args.stop_from, self.args.stop_to)
		if self.args.build_line:
			self.build_line()
		if self.args.stop_schedule:
			self.scrap_pdf_stop_schedule()

if __name__ == '__main__':
	FilBleu()
