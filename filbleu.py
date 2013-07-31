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
import urllib
import os
import pprint
pp = pprint.PrettyPrinter(indent=1)

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
		self.schedules = []
		self.raw = []
		## bbox in pdf is in points
		## x0,y0 is bottom left
		## x1,y1 is up right
		self.selected_layout = 'generic'
		self.current_is_night = False
		self.buckets = None
		self.layouts = {
			'generic': {
				'directions': {'x0':  14.0, 'y0': 755.0, 'x1': 480.0, 'y1': 835.0},
				'stopname':   {'x0': 485.0, 'y0': 760.0, 'x1': 580.0, 'y1': 835.0},
				'schedule1':  {'x0':  48.0, 'y0': 550.0, 'x1': 570.0, 'y1': 690.0},
				'schedule2':  {'x0':  48.0, 'y0': 395.0, 'x1': 570.0, 'y1': 495.0},
				'schedule3':  {'x0':  48.0, 'y0': 230.0, 'x1': 570.0, 'y1': 340.0},
				'schedule4':  {'x0':  48.0, 'y0': 130.0, 'x1': 570.0, 'y1': 172.0},
				'schedule1_hours': {'x0':  48.0, 'y0': 690.0, 'x1': 570.0, 'y1': 710.0},
				'schedule2_hours': {'x0':  48.0, 'y0': 495.0, 'x1': 570.0, 'y1': 515.0},
				'schedule3_hours': {'x0':  48.0, 'y0': 345.0, 'x1': 570.0, 'y1': 365.0},
				'schedule4_hours': {'x0':  48.0, 'y0': 170.0, 'x1': 570.0, 'y1': 195.0},
				'schedule1_lines': {'x0':  25.0, 'y0': 550.0, 'x1':  48.0, 'y1': 690.0},
				'schedule2_lines': {'x0':  25.0, 'y0': 395.0, 'x1':  48.0, 'y1': 495.0},
				'schedule3_lines': {'x0':  25.0, 'y0': 230.0, 'x1':  48.0, 'y1': 340.0},
				'schedule4_lines': {'x0':  25.0, 'y0': 128.0, 'x1':  48.0, 'y1': 170.0},
				'schedule1_desc':  {'x0':  25.0, 'y0': 710.0, 'x1': 570.0, 'y1': 730.0},
				'schedule2_desc':  {'x0':  25.0, 'y0': 515.0, 'x1': 570.0, 'y1': 535.0},
				'schedule3_desc':  {'x0':  25.0, 'y0': 360.0, 'x1': 570.0, 'y1': 380.0},
				'schedule4_desc':  {'x0':  25.0, 'y0': 190.0, 'x1': 570.0, 'y1': 210.0},
				'notes':      {'x0':  14.0, 'y0':   3.0, 'x1': 580.0, 'y1':  95.0},
			},
			'small': {
				'directions':	   {'x0':  14.0, 'y0': 335.0, 'x1': 480.0, 'y1': 400.0},
				'stopname':        {'x0': 485.0, 'y0': 330.0, 'x1': 580.0, 'y1': 400.0},
				'schedule1':       {'x0':  48.0, 'y0': 225.0, 'x1': 570.0, 'y1': 265.0},
				'schedule1_hours': {'x0':  48.0, 'y0': 265.0, 'x1': 570.0, 'y1': 285.0},
				'schedule1_desc':  {'x0':  14.0, 'y0': 285.0, 'x1': 570.0, 'y1': 305.0},
				'notes':           {'x0':  14.0, 'y0':  30.0, 'x1': 580.0, 'y1':  95.0},
			},
			'night': {
				'directions':	   {'x0':  14.0, 'y0': 340.0, 'x1': 480.0, 'y1': 410.0},
				'stopname':        {'x0': 485.0, 'y0': 340.0, 'x1': 580.0, 'y1': 410.0},
				'schedule1':       {'x0':  37.0, 'y0': 250.0, 'x1': 260.0, 'y1': 310.0},
				'schedule1_desc':  {'x0':  14.0, 'y0': 310.0, 'x1': 580.0, 'y1': 330.0},
				'notes':     	   {'x0': 280.0, 'y0': 250.0, 'x1': 580.0, 'y1': 310.0},
			},
		}
		self.content = {
			'directions': [],
			'stopname': [],
			'schedule1': [],
			'schedule2': [],
			'schedule3': [],
			'schedule4': [],
			'schedule1_hours': [],
			'schedule2_hours': [],
			'schedule3_hours': [],
			'schedule4_hours': [],
			'schedule1_lines': [],
			'schedule2_lines': [],
			'schedule3_lines': [],
			'schedule4_lines': [],
			'schedule1_desc': [],
			'schedule2_desc': [],
			'schedule3_desc': [],
			'schedule4_desc': [],
			'notes': [],
		}
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
				(x0, y0, x1, y1) = item.bbox
				height = y1 - y0
				if height == 841.89:
					# Default size
					pass
				else:
					if height == 420.94:
						self.selected_layout = 'small'
					else:
						raise NotImplementedError("Unable to handle this page size:" + str(height))
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

				(x0, y0, x1, y1) = item.bbox
				coords = {'x0': x0, 'y0': y0, 'x1': x1, 'y1': y1}

				self.raw += [ {'txt': txt, 'coords': coords } ]

				if txt.find("Nuit") >= 0:
					self.selected_layout = 'night'
					self.current_is_night = True
				return

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

	def get_bucket_name(self, coords):
		for bucket in self.buckets:
			## bbox in pdf is in points
			## x0,y0 is bottom left
			## x1,y1 is up right
			center_x = (coords['x0'] + coords['x1']) / 2.0
			center_y = (coords['y0'] + coords['y1']) / 2.0
			if  (center_x >= self.buckets[bucket]['x0'] and center_x <= self.buckets[bucket]['x1']) \
			and (center_y >= self.buckets[bucket]['y0'] and center_y <= self.buckets[bucket]['y1']):
				return bucket

	def extract_directions_from_bucket(self):
		directions = []
		for d in self.content['directions']:
			if d['txt'].find("Vers ") >= 0:
				directions += [ d['txt'].split("Vers ")[1].strip() ]

		return directions

	def extract_lines_from_bucket(self, name):
		lines = []
		for t in self.content[name]:
			if (t['coords']['x0'] >= 28) and (t['coords']['x1'] <= 44):
				lines += [ {'number': t['txt'], 'coords': t['coords']} ]
		if lines == []:
			for d in self.content['directions']:
				if d['txt'].find("Vers ") >= 0:
					number = d['txt'].split("Vers ")[0].strip()
					if number != "":
						lines += [ {'number': number, 'coords': None} ]
		if lines == []:
			for d in self.content['directions']:
				if d['txt'].find("Vers ") == -1:
					lines += [ {'number': d['txt'].split("Vers ")[0].strip(), 'coords': None} ]

		return lines

	def extract_dates_from_bucket(self, name):
		dates = []
		for t in self.content[name + "_desc"]:
			if t['txt'].find("horaires valables") >= 0:
				dates = self.extract_periods(t['txt'].replace("er", "").strip())
		# return self.process_dates(dates)
		return dates

	def extract_period_from_bucket(self, name):
		period = []
		for t in self.content[name + "_desc"]:
			if t['txt'].find("Lundi au Vendredi") >= 0 or t['txt'].find("Samedi") >= 0 or t['txt'].find("Dimanche") >= 0 or t['txt'].find("Nuit") >= 0 or t['txt'].find("Vacances scolaires") >= 0:
				period = t['txt'].strip()
		return period

	def extract_notes_from_bucket(self):
		notes = {}
		for note in self.content['notes']:
			start = re.compile(r"^([a-z] )").search(note['txt'])
			if start:
				key = start.group(1).strip()
				txt = re.sub(r"^[a-z] ", "", note['txt'])
				notes[key] = txt
		for note in self.content['notes']:
			start = re.compile(r"^([a-z] )").search(note['txt'])
			if not start:
				middle_y_note = (note['coords']['y0'] + note['coords']['y1']) / 2.0
				minDist = 32768
				matched = None
				for note_father in self.content['notes']:
					start = re.compile(r"^([a-z] )").search(note_father['txt'])
					if start:
						middle_y_father = (note_father['coords']['y0'] + note_father['coords']['y1']) / 2.0
						dist = middle_y_father - middle_y_note
						if dist >= 0 and dist <= minDist:
							minDist = dist
							matched = note_father

				if matched is not None:
					start = re.compile(r"^([a-z] )").search(matched['txt'])
					if start:
						notes[start.group(1).strip()] += " " + re.sub(r"^[a-z] ", "", note['txt'])
					else:
						raise NotImplementedError("Note continuation: " + str(note))
				else:
					raise NotImplementedError("Note continuation: " + str(note))
		return notes

	def extract_schedule_hours_from_bucket(self, name):
		hours = []
		for s in self.content[name]:
			hourRe = re.compile(r"^[0-9]+h").search(s['txt'])
			if hourRe:
				hours += [ {'hour': s['txt'].replace("h", ""), 'coords': s['coords']} ]

		if (not self.current_is_night) and (len(hours) != 17):
			raise NotImplementedError("Inconsistent number of hours: " + str(len(hours)) + ".\n" + str(hours))

		return hours

	def extract_schedule_minutes_from_bucket(self, name):
		minutes = []
		for s in self.content[name]:
			minuteRe = re.compile(r"^[0-9]+[a-z]*").search(s['txt'])
			hourRe = re.compile(r"^[0-9]+h").search(s['txt'])
			if minuteRe and not hourRe:
				notes = list(re.sub(r"[0-9]*", "", s['txt']))
				minute = re.sub(r"[a-z]*", "", s['txt'])
				minutes += [ {'minute': minute, 'coords': s['coords'], 'notes': notes, 'line': None} ]

		return minutes

	def assign_line_to_minutes_from_bucket(self, name, raw):
		minutes = []
		for minute in raw:
			minute['line'] = self.match_line_with_minute_from_bucket(name, minute)
			minutes += [ minute ]
		return minutes

	def match_line_with_minute_from_bucket(self, lines, minute):
		okValue = ""
		if len(lines) > 1:
			minDist = 32768
			for line in lines:
				if line['coords'] is not None:
					(ly0, ly1) = (line['coords']['y0'], line['coords']['y1'])
					(my0, my1) = (minute['coords']['y0'], minute['coords']['y1'])
					n = line['number']
					# print "(ly0, ly1) = (%(ly0)f, %(ly1)f) ; (my0, my1) = (%(my0)f, %(my1)f)" % {'ly0': ly0, 'ly1': ly1, 'my0': my0, 'my1': my1}
					middle_minutes = (my0 + my1) / 2.0
					middle_line = (ly0 + ly1) / 2.0
					dist = math.fabs(middle_minutes - middle_line)
					if (dist < minDist):
						minDist = dist
						okValue = n
		else:
			okValue = lines[0]['number']

		return okValue

	def assign_minutes_to_hours_from_bucket(self, hours, minutes):
		sched = {}
		for hour in hours:
			sched[hour['hour']] = [ ]
			minLeft  = hour['coords']['x0']
			maxRight = hour['coords']['x1']
			for minute in minutes:
				middle = (minute['coords']['x0'] + minute['coords']['x1']) / 2.0
				if middle >= minLeft and middle <= maxRight:
					sched[hour['hour']] += [ { 'minute': minute['minute'], 'line': minute['line'], 'notes': minute['notes'] } ]
		return sched

	def extract_schedule_from_bucket(self, name, lines):
		schedule = {}

		hours = self.extract_schedule_hours_from_bucket(name + "_hours")
		minutes_raw = self.extract_schedule_minutes_from_bucket(name)
		minutes = self.assign_line_to_minutes_from_bucket(lines, minutes_raw)
		schedule = self.assign_minutes_to_hours_from_bucket(hours, minutes)

		return schedule

	def extract_night_schedule_from_bucket(self, name, lines):
		schedule = {}

		line = ""
		if len(lines) == 1:
			line = lines[0]['number']
		else:
			raise NotImplementedError("Night schedule with more than one line:" + str(lines))

		for t in self.content[name]:
			isTime = re.compile(r"([0-9]{2})\.([0-9]{2})([a-z]*)").search(t['txt'])
			if isTime:
				(hour, minute) = (isTime.group(1), isTime.group(2))
				notes = list(re.sub(r"[0-9]*", "", isTime.group(3)))
				try:
					schedule[hour].append({ 'minute': minute, 'notes': notes, 'line': line })
				except KeyError as e:
					schedule[hour] = [ { 'minute': minute, 'notes': notes, 'line': line } ]

		return schedule

	def one_bucket_to_schedule(self, name):
		if len(self.content[name]) == 0:
			return None

		period = self.extract_period_from_bucket(name)
		dates = self.extract_dates_from_bucket(name)
		notes = self.extract_notes_from_bucket()
		direction = self.extract_directions_from_bucket()

		tlines = self.extract_lines_from_bucket(name + "_lines")
		if not self.current_is_night:
			schedule = self.extract_schedule_from_bucket(name, tlines)
		else:
			schedule = self.extract_night_schedule_from_bucket(name, tlines)

		lines = []
		for line in tlines:
			lines += [ line['number'] ]
		lines = list(set(lines))

		schedule = {
			'period': period,
			'dates': dates,
			'schedule': schedule,
			'lines': lines,
			'notes': notes,
			'direction': direction,
		}

		return schedule

	def bucket_to_schedule(self):
		sub = [ 'schedule1', 'schedule2', 'schedule3', 'schedule4' ]
		schedules = []
		for s in sub:
			r = self.one_bucket_to_schedule(s)
			if r is not None:
				schedules += [ r ]
		return schedules

	def assign_content(self):
		try:
			self.buckets = self.layouts[self.selected_layout]
		except KeyError as e:
			raise NotImplementedError("No bucket found: do you have the matching layout '" + self.selected_layout + "' ?")

		for raw_element in self.raw:
			bucket = self.get_bucket_name(raw_element['coords'])
			if bucket is not None:
				self.content[bucket] += [ raw_element ]

	def process_dates(self, dates):
		oldlocale = locale.getlocale()
		locale.setlocale(locale.LC_ALL, ('fr_FR', 'UTF-8'))
		newDates = []
		for interval in dates:
			(begin, end) = interval
			arBegin = begin.split(" ")
			arEnd = end.split(" ")

			if len(arBegin) == 2:
				arBegin.append(arEnd[2])

			sBegin = " ".join(arBegin) + " 00:00:00"
			sEnd = " ".join(arEnd) + " 23:59:59"

			dBegin = datetime.datetime.strptime(sBegin, "%d %B %Y %H:%M:%S")
			dEnd = datetime.datetime.strptime(sEnd, "%d %B %Y %H:%M:%S")

			newDates += [ [ dBegin, dEnd ] ]
		locale.setlocale(locale.LC_ALL, oldlocale)
		return newDates

	def close(self):
		self.assign_content()
		self.schedules = self.bucket_to_schedule()
		# self.check_schedule()
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
	def __init__(self, id, name, city):
		self.id = id
		self.name = name
		self.stop_name = name
		self.city = city
		self.linkbase = ""
		self.stopArea = self.id + "|" + self.stop_name.decode('utf-8') + "|" + self.city.decode('utf-8')

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
		self.browser.set_handle_equiv(True)
		self.browser.set_handle_redirect(True)
		self.browser.set_handle_referer(True)
		self.browser.set_handle_robots(False)

		self.base    = "http://www.filbleu.fr/"
		self.baseurl = self.base + "horaires-et-trajets/"
		self.dirs    = "index.php?option=com_infosvoyageurs&view=horairesarret&format=raw&task=horairesarret.getdirs"
		self.arrets  = "index.php?option=com_infosvoyageurs&view=horairesarret&format=raw&task=horairesarret.getarrets"
		self.url_raz = "&raz"
		self.periode = "&periode="
		self.etape = ""
		self.pdfs_dir = "pdfs"

		self.parser = argparse.ArgumentParser(description="FilBleu Scrapper")
		self.parser.add_argument("--list-lines", action="store_true", help="List lines")
		self.parser.add_argument("--list-stops", help="List stops of a line (format: n|M)")
		self.parser.add_argument("--list-stops-basic", action="store_true", help="When listing stops, just displaying without any filtering")
		self.parser.add_argument("--build-line", help="Build given line, using lines.txt and stops_coords.txt")
		self.parser.add_argument("--build-line-jvmalin", help="Build given line from JVMalin.fr")
		self.parser.add_argument("--build-line-from-schedules", help="Build given line, using schedules.*.txt (implies --offline)")
		self.parser.add_argument("--build-line-gpx", action="store_true", default=True, required=False, help="Build given line, output as GPX")
		self.parser.add_argument("--get-stop-coords", help="Get a stop GPS coordinates")
		self.parser.add_argument("--get-stop-coords-jvmalin", help="Get a stop GPS coordinates from JVMalin.fr")
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
		stopschedule.add_argument("--offline", action="store_true", default=False, help="Offline mode.")

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

	def lines_to_lineStop(self, line_to_build):
		lineStops = {}
		lineStop = re.compile(r"Stop:.*=> (.*)\|(.*)\|(.*) \[(.*)\]")
		for line in open('stops.' + line_to_build + '.txt','r').readlines():
			results = lineStop.search(line)
			if results:
				stopId   = results.group(1)
				stopName = results.group(2)
				cityName = results.group(3)
				subLine  = results.group(4)
				stopArea = str(stopId) + "|" + stopName + "|" + cityName
				spec = "all"
				if subLine.count("A"):
					spec = "A"
				if subLine.count("B"):
					spec = "B"
				h = {'name': stopName, 'city': cityName, 'stop': stopArea }
				try:
					lineStops[spec][stopId] = h
				except KeyError as e:
					lineStops[spec] = { stopId: h }
		return lineStops

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
		sys.stderr.write("Filename is: '" + fname + "'; ")
		try:
			with open(self.pdfs_dir + os.path.sep + fname, 'r') as f:
				retval = f.read()
				if (retval == "missing"):
					sys.stderr.write("No schedule exists for this one, bypassing.\n")
					retval = None
			sys.stderr.write("Cache hit.\n")
		except IOError as e:
			sys.stderr.write("Cache miss.\n")
			if self.args.offline:
				return None
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
						with open(self.pdfs_dir + os.path.sep + fname, 'w') as f:
							f.write("missing")
					else:
						sys.stderr.write("Not a PDF !\n")
						sys.stderr.write("Code=" + str(response.code) + "\n")
						sys.stderr.write(str(infos) + "\n")
						sys.stderr.write("Content:\n")
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
		self.baseurl += "horaires-par-arret/horaires-par-arret-bus-tram-sept-2013"
		self.etape = ""

	def page_stops(self):
		pass

	def page_journey(self):
		self.baseurl += "votre-itineraire-sur-mesure"
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
					url = (self.base + s.linkbase + "StopArea=" + s.stopArea + "&Line=" + lineid)
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
				line = "Stop: %(stop_name)s (%(stop_city)s) => %(stop_area)s [%(lineid)s]\n" % { 'lineid': e, 'stop_name': ff['stop'].stop_name, 'stop_city': ff['stop'].city, 'stop_area': ff['stop'].stopArea.encode('utf-8') }
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

	def get_stops_sens(self, sens, lineid):
		self.page_stops()
		self.browser.open(self.baseurl + self.arrets + "&id_ligne=" + str(lineid) + "&direction=" + str(sens))
		return BeautifulSoup.BeautifulSoup(self.browser.response().read(), convertEntities=BeautifulSoup.BeautifulSoup.HTML_ENTITIES)

	def get_stops(self):
		self.raz()
		self.stops = {}
		linkBase = ""
		lineid = self.args.list_stops
		soups = [ self.get_stops_sens(1, lineid), self.get_stops_sens(2, lineid) ]
		if not lineid in self.stops.keys():
			self.stops[lineid] = {}

		for soup in soups:
			for line in soup.find('select', attrs = { 'id': 'selectarrets' }).findAll('option'):
				if line["value"] == "0":
					continue
				s = BusStop(line["value"], line.text.encode('utf-8'), line.parent["label"].encode('utf-8'))
				self.stops[lineid][s.id] = s

	def get_stops_offline(self, lineid):
		self.args.list_stops = lineid
		self.stops = {}
		self.stops[lineid] = {}
		sensS = [ -1, 1 ]
		lineStops = self.lines_to_lineStop(lineid)
		for spec in lineStops:
			ls = lineStops[spec]
			for stop_id in ls:
				for sens in sensS:
					s = ls[stop_id]
					linkBase = "grille-horaires-v4.php?Sens=" + str(sens) + "&"
					stopArea = s['stop']
					st = BusStop(s['name'], linkBase)
					st.set_stopArea(s["stop"].decode('utf-8'))
					self.stops[lineid][str(stop_id)+':'+str(sens)] = st

	def list_lines(self):
		self.get_lines()
		for line in self.lines:
			line = self.lines[line]
			out = "Line(id=%(line_id)s): " % { 'line_id': line.id }

			if len(line.ends) == 1:
				end = line.ends[0].strip().decode('utf-8')
				out += "number=%(line_number)s; name={'%(end)s'}" % { 'line_number': line.number, 'end': end}

			# classic, one end on both
			if len(line.ends) == 2:
				if type(line.ends[0]) == str and type(line.ends[1]) == str:
					end_one = line.ends[0].strip().decode('utf-8')
					end_two = line.ends[1].strip().decode('utf-8')
					out += "number=%(line_number)s; name={'%(end_one)s','%(end_two)s'}" % { 'line_number': line.number, 'end_one': end_one, 'end_two': end_two}
				if len(line.ends[0]) == 2 and type(line.ends[1]) == str:
					Aend_one = line.ends[0][0].strip().decode('utf-8')
					Bend_one = line.ends[0][1].strip().decode('utf-8')
					end_two = line.ends[1].strip().decode('utf-8')
					out += "number=%(line_number)s; name={'%(end_one)s','%(end_two)s'}" % { 'line_number': line.number + 'A', 'end_one': Aend_one, 'end_two': end_two}
					out += " | number=%(line_number)s; name={'%(end_one)s','%(end_two)s'}" % { 'line_number': line.number + 'B', 'end_one': Bend_one, 'end_two': end_two}
				if type(line.ends[0]) == str and len(line.ends[1]) == 2:
					end_one = line.ends[0].strip().decode('utf-8')
					Aend_two = line.ends[1][0].strip().decode('utf-8')
					Bend_two = line.ends[1][1].strip().decode('utf-8')
					out += "number=%(line_number)s; name={'%(end_one)s','%(end_two)s'}" % { 'line_number': line.number + 'A', 'end_one': end_one, 'end_two': Aend_two}
					out += " | number=%(line_number)s; name={'%(end_one)s','%(end_two)s'}" % { 'line_number': line.number + 'B', 'end_one': end_one, 'end_two': Bend_two}
			out += "\n"
			out = out.encode('utf-8')
			sys.stdout.write(out)

	def get_lines(self):
		self.page_lines()
		self.raz()
		self.lines = {}
		soup = BeautifulSoup.BeautifulSoup(self.browser.response().read(), convertEntities=BeautifulSoup.BeautifulSoup.HTML_ENTITIES)
		for line in soup.find('select', attrs = { 'id': 'selectlignes' }).findAll('option'):
			lineid = line['value']
			linenb = line.text.split(' - ')[0]

			if lineid == '0':
				continue

			if not self.lines.has_key(lineid):
				self.lines[lineid] = BusLine(id=lineid, num=linenb)

			dirs = self.baseurl + self.dirs + "&id_ligne=" + lineid
			self.browser.open(dirs)
			soup = BeautifulSoup.BeautifulSoup(self.browser.response().read(), convertEntities=BeautifulSoup.BeautifulSoup.HTML_ENTITIES)
			for opt in soup.findAll('option'):
				if opt['value'] == '0':
					continue
				if opt.text.find(' - ') == -1:
					self.lines[lineid].add_end(opt.text.encode('utf-8'))
				else:
					stops = []
					for s in opt.text.split(' - '):
						stops.append(s.encode('utf-8'))
					self.lines[lineid].add_end(stops)


	def get_stop_coords(self):
		self.journeys = []
		self.page_journey()
		self.raz()
		self.browser.select_form(nr=0)
		self.browser["iform[Departure]"] = self.strip_accents(unicode(self.args.get_stop_coords, "UTF-8"))
		self.browser["iform[Arrival]"] = "Unknwonstop"
		self.browser["iform[Sens]"] = [ "1" ]
		self.browser["iform[Date]"] = "02/09/2013"
		self.browser["iform[Hour]"] = [ "13" ]
		self.browser["iform[Minute]"] = [ "35" ]
		self.browser["iform[Criteria]"] = [ "1" ]
		self.browser.submit()
		soup = BeautifulSoup.BeautifulSoup(self.browser.response().read())
		form = soup.find('form')
		if form:
			stopArea = self.extract_stopArea(form, 'DepJvmalin', self.strip_accents(unicode(self.args.get_stop_coords, "UTF-8")))
			type = stopArea.split('|')[0]
			if type != 'StopArea':
				print "Cannot find a match stopArea for: %(stop_name)s" % {'stop_name': self.args.get_stop_coords}
				return

			values = stopArea.replace(",", ".").split("|")
			east = float(values[6])
			north = float(values[7])

			(degrees_e, degrees_n) = self.lambert2c_to_deg(east, north)

			l = "Found a stop matching stopArea: [%(stop_area)s]; Lambert2+: {E:%(lb2p_e)f, N:%(lb2p_n)f}; Degrees: {E:%(degrees_e)f, N:%(degrees_n)f}\n" % {'stop_area': stopArea, 'lb2p_e': east, 'lb2p_n': north, 'degrees_e': degrees_e, 'degrees_n': degrees_n}
			l = l.encode('utf-8')
			sys.stdout.write(l)
		else:
			print "No form result."

	def get_stop_coords_jvmalin(self):
		stopName = urllib.urlencode({'Departure': self.args.get_stop_coords_jvmalin})
		stopDest = urllib.urlencode({'Destination': 'Jean Jaurès (Tours)'})
		url = "http://www.jvmalin.fr/Itineraires/Precision?" + stopName + "&edtDeparture=&oldDeparture=&oldEdtDeparture=&" + stopDest + "s&edtDestination=&oldDestination=&oldEdtDestination=&sens=1&hour=10&minute=35&dateFull=31%2F07%2F2013&Mode[]=car%2Bbus&criteria=1&submitSearch=Rechercher"
		self.browser.open(url)
		soup = BeautifulSoup.BeautifulSoup(self.browser.response().read(), convertEntities=BeautifulSoup.BeautifulSoup.HTML_ENTITIES)
		edtDepartureRappel = soup.find('input', attrs = {'id': 'edtDepartureRappel'})
		if not edtDepartureRappel:
			print "Unable to find a stop match"

		stopArea = edtDepartureRappel["value"]
		if len(stopArea) == 0:
			DepartureStopArea = soup.find('input', attrs = {'id': 'Departure-StopArea0'}) or soup.find('input', attrs = {'id': 'Departure-best1'})
			if not DepartureStopArea:
				print "Unable to find a stop proposal"
				return
			stopArea = self.html_br_strip(DepartureStopArea["value"]).split('=>')[1]

		type = stopArea.split('|')[0]
		if type != 'StopArea':
			print "Cannot find a match stopArea for: %(stop_name)s" % {'stop_name': self.args.get_stop_coords}
			return

		values = stopArea.replace(",", ".").split("|")
		east = float(values[6])
		north = float(values[7])

		(degrees_e, degrees_n) = self.lambert2c_to_deg(east, north)

		l = "Found a stop matching stopArea: [%(stop_area)s]; Lambert2+: {E:%(lb2p_e)f, N:%(lb2p_n)f}; Degrees: {E:%(degrees_e)f, N:%(degrees_n)f}\n" % {'stop_area': stopArea, 'lb2p_e': east, 'lb2p_n': north, 'degrees_e': degrees_e, 'degrees_n': degrees_n}
		l = l.encode('utf-8')
		sys.stdout.write(l)

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
		if self.args.offline:
			self.get_stops_offline(self.args.line)
		else:
			self.args.list_stops = self.args.line
			self.get_stops()
		perform = True
		for lineid in self.stops:
			current = 0
			total = len(self.stops[lineid])
			for stop in self.stops[lineid]:
				s = self.stops[lineid][stop]
				if self.args.stop:
					perform = (self.args.stop.decode('utf-8') == s.stop_name)

				if perform:
					stop_clean = stop.split(":")[0]
					stop_area = s.stopArea.replace(' ', '+')
					url = (self.base + s.linkbase + "StopArea=" + stop_area + "&Line=" + self.args.line)
					msg = "[%(current)d/%(total)d:%(lineid)s] Found stop %(stopName)s, downloading PDF at %(pdfURL)s\n" % {'stopName': s.stop_name, 'pdfURL': url, 'current': current, 'total': total, 'lineid': lineid}
					msg = msg.encode('utf-8')
					sys.stderr.write(msg)
					pdf = StringIO()
					content = self.download_pdf(url)
					if content is not None:
						pdf.write(content)
						res = self.process_pdf_schedule(pdf)
						print "Stop:", s.stop_name.encode('utf-8')
						pp.pprint(res)
					pdf.close()
				current += 1

	def raz(self):
		url = self.baseurl
		if not self.etape == "":
			url += "&etape=" + self.etape
			if self.args.list_stops:
				linespecs = self.lines_to_lineSpec(self.args.list_stops)
				line = ""
				for lspec in linespecs:
					line = lspec['number'].replace("A", "").replace("B", "")
				url += "&Line=" + self.args.list_stops + "|" + line
#		else:
#			today = datetime.date.today()
#			start_ete = datetime.date(today.year, 7, 2)
#			stop_ete = datetime.date(today.year, 9, 1)
#			p = "1"
#			if today >= start_ete and today <= stop_ete:
#				p = "2"
#			url += self.periode + p

		self.browser.open(url)
	
	def distance(self, p1, p2):
		R = 6378000.0
		sourcelatitude = (math.pi * p2['lat']) / 180.0;
		sourcelongitude = (math.pi * p2['lon']) / 180.0;
		latitude = (math.pi * p1['lat']) / 180.0;
		longitude = (math.pi * p1['lon']) / 180.0;
		return R * (math.pi/2 - math.asin( math.sin(latitude) * math.sin(sourcelatitude) + math.cos(longitude - sourcelongitude) * math.cos(latitude) * math.cos(sourcelatitude)));

	def build_line_from_schedules(self):
		line_to_build = self.args.build_line_from_schedules
		self.args.offline = True
		self.get_stops_offline(line_to_build)
		perform = True
		passages = {}
		relations = {}
		stops = {}
		for lineid in self.stops:
			total = len(self.stops[lineid])
			for stop in self.stops[lineid]:
				stop_clean = stop.split(":")[0]
				sens = stop.split(":")[1]
				s = self.stops[lineid][stop]
				stop_area = s.stopArea.replace(' ', '+')
				url = (self.base + s.linkbase + "StopArea=" + stop_area + "&Line=" + line_to_build)
				print url
				pdf = StringIO()
				content = self.download_pdf(url)
				if content is not None:
					pdf.write(content)
					res = self.process_pdf_schedule(pdf)
					stops[stop] = { 'name': s.stop_name, 'schedules': res }
				pdf.close()

		for stop in stops:
			sens = stop.split(":")[1]
			for sched in stops[stop]['schedules']:
				lowest = {}
				curtime = {}
				dirs = {}
				for line in sched['lines']:
					dt = sched['dates'][0][0]
					lowest[line] = datetime.datetime(year=dt.year, month=dt.month, day=dt.day, hour=23,minute=59,second=59)
					curtime[line] = None
					for hour in sched['schedule']:
						for m in sched['schedule'][hour]:
							if m['line'] == line:
								dirs[sched['period']]= { line: sched['direction'][sched['lines'].index(line)].decode('utf-8') }
								minute = m['minute']
								curtime[line] = datetime.datetime(year=dt.year, month=dt.month, day=dt.day, hour=int(hour),minute=int(minute),second=00)
								if curtime[line] < lowest[line]:
									lowest[line] = curtime[line]

					dt = sched['dates'][0][0]
					p = sched['period']
					s = stops[stop]['name']
					l = datetime.time(hour=lowest[line].hour, minute=lowest[line].minute)

					try:
						passages[dt][p][line][sens][s] = l
					except KeyError as e:
						try:
							passages[dt][p][line][sens] = { s: l }
						except KeyError as e:
							try:
								passages[dt][p][line] = { sens: { s: l } }
							except KeyError as e:
								try:
									passages[dt][p] = { line: { sens: { s: l } } }
								except KeyError as e:
									passages[dt] = { p: { line: { sens: { s: l } } } }

		relations = passages

		for date in relations:
			for period in relations[date]:
				for line in relations[date][period]:
					for dir in relations[date][period][line]:
						d = relations[date][period][line][dir]
						s = sorted(d, key=d.get)
						last = s[-1]
						tl = relations[date][period][line][dir][last]
						nd = datetime.datetime(year=date.year, month=date.month, day=date.day, hour=tl.hour, minute=tl.minute, second=00) + datetime.timedelta(minutes=2)
						termtime = datetime.time(hour=nd.hour, minute=nd.minute)

						# Forcing addition of terminus, since buggy website does not provide it
						# relations[date][period][line][dir] = termtime

						d = relations[date][period][line][dir]
						s = sorted(d, key=d.get)

						ar = []
						for st in s:
							time = relations[date][period][line][dir][st]
							ar += [ {'stop': st, 'time': time } ]
						relations[date][period][line][dir] = ar

		pprint.pprint( relations )

	def build_line_jvmalin(self):
		line_to_build = self.args.build_line
		urlbase = "http://www.jvmalin.fr/Horaires/Recherche?networkExternalCode=Filbleu"
		urlbase += "&lineExternalCode=FILNav" + line_to_build
		urlbase += "&hor-date=30%2F07%2F2013&method=lineComplete&method=lineComplete"

		print "digraph {"
		for sens in [-1, 1]:
			url = urlbase + "&sens=" + str(sens)
			self.browser.open(url)
			soup = BeautifulSoup.BeautifulSoup(self.browser.response().read(), convertEntities=BeautifulSoup.BeautifulSoup.HTML_ENTITIES)
			if not soup:
				print "No output :("
				continue

			table = soup.find('table')
			if not table or table["id"] != "LineArray":
				print "No valid table :("
				continue

			stopsByCol = {}
			for row in table.findAll('tr'):
				stopName = self.html_br_strip(row.find('a').text)
				i = 0
				for cell in row.findAll('td'):
					date = self.html_br_strip(cell.text)
					if not stopsByCol.has_key(i):
						stopsByCol[i] = []
					if not (date == "-"):
						stopsByCol[i] += [ stopName ]
					i += 1

			# check that list1 is a subset of list2
			def isStopsSubset(list1, list2):
				smallest = list1
				biggest = list2
				if len(list1) >= len(list2):
					smallest = list2
					biggest = list1

				try:
					firstMatchAt = biggest.index(smallest[0])
					return (smallest == biggest[firstMatchAt:])
				except ValueError as e:
					return False

			col1S = col2S = stopsByCol.keys()
			for col1 in col1S:
				for col2 in col2S:
					if col1 == col2:
						continue
					if not stopsByCol.has_key(col1) or not stopsByCol.has_key(col2):
						continue

					isSame = (stopsByCol[col1] == stopsByCol[col2])
					if (isSame):
						del stopsByCol[col2]
						continue

					isSubset = isStopsSubset(stopsByCol[col1], stopsByCol[col2])
					if (isSubset):
						del stopsByCol[col1]
						continue

			# print "Line:", line_to_build, "--","Sens:", sens
			# pprint.pprint(stopsByCol)

			for id in stopsByCol:
				for stop in stopsByCol[id]:
					cid = stopsByCol[id].index(stop);
					if ((cid + 1) < len(stopsByCol[id])):
						out = "\"%(deb)s\" -> \"%(fin)s\"" % {'deb': stopsByCol[id][cid], 'fin': stopsByCol[id][cid+1]}
						print out.encode('utf-8')

		print "}"


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

		lineStops = self.lines_to_lineStop(line_to_build)
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
		if self.args.get_stop_coords_jvmalin:
			self.get_stop_coords_jvmalin()
		if self.args.journey:
			self.list_journeys()
		if self.args.bruteforce:
			self.bruteforce_find_lines(self.args.stop_from, self.args.stop_to)
		if self.args.build_line:
			self.build_line()
		if self.args.build_line_jvmalin:
			self.build_line_jvmalin()
		if self.args.build_line_from_schedules:
			self.build_line_from_schedules()
		if self.args.stop_schedule:
			self.scrap_pdf_stop_schedule()

if __name__ == '__main__':
	FilBleu()
