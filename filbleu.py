#!/usr/bin/python

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
	def __init__(self, name):
		self.name = name

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
		self.baseurl = "http://www.filbleu.fr/page.php"
		self.url_raz = "&raz"
		self.periode = "&periode="
		self.current_id = ""
		self.etape = ""

		self.parser = argparse.ArgumentParser(description="FilBleu Scrapper")
		self.parser.add_argument("--list-lines", action="store_true", help="List lines")
		self.parser.add_argument("--list-stops", help="List stops of a line (format: n|M)")
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

	def page_lines(self):
		self.current_id = "1-2"

	def page_stops(self):
		self.current_id = "1-2"
		self.etape = "2"

	def page_journey(self):
		self.current_id = "1-1"

	def list_stops(self):
		self.get_stops()
		for lineid in self.stops:
			for stop in self.stops[lineid]:
				stop = self.stops[lineid][stop]
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
		soups = [ self.get_stops_sens(1), self.get_stops_sens(-1) ]
		for soup in soups:
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
			self.stops[lineid] = {}
			for stop in stops:
				if not stop["value"] == "":
					s = BusStop(stop.text)
					s.set_stopArea(stop["value"])
					self.stops[lineid][s.id] = s

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
			depart = form.find('input', attrs = {'id': 'Departure'})
			stopArea = ""
			if depart:
				# stop is recognized; get WGS84/Lambert2+ coords
				stopArea = depart["value"]
			else:
				depart = form.find('select', attrs = {'id': 'Departure'})
				# ok, we have to find the first stop
				optgroup = form.find('optgroup')
				if optgroup:
					options = optgroup.findAll('option')
					if options:
						bestSim = 0
						bestValue = ""
						for option in options:
							sim = difflib.SequenceMatcher(a=self.strip_accents(unicode(self.args.get_stop_coords, "UTF-8")), b=option.text).ratio()
							if (sim > bestSim):
								bestSim = sim
								bestValue = option["value"]
						stopArea = bestValue
				else:
					print "No optgroup!"

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
		self.browser["Departure"] = str(self.args.stop_from)
		self.browser["Arrival"] = str(self.args.stop_to)
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
			self.browser.open(self.baseurl + journey['link'].replace('page.php', ''))
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
		success = False
		self.args.criteria = 2
		self.args.way = 1
		self.args.stop_from = depStop
		self.args.stop_to = arrStop
		self.args.date = "04/06/2012"
		jour = time.strptime("04/06/2012", "%d/%m/%Y")
		for timestamp in self.datespan(datetime.datetime(jour.tm_year, jour.tm_mon, jour.tm_mday, 5, 0), datetime.datetime(jour.tm_year, jour.tm_mon, jour.tm_mday, 20, 0), delta=datetime.timedelta(seconds=15*60)):
			print timestamp
			if only_lines == self.lines_found.keys():
				print "Successfully matched:", self.lines_found.keys()
				success = True
				break
			self.args.hour = timestamp.hour
			self.args.min = timestamp.minute
			self.get_journeys()
			for j in self.journeys:
				if j['connections'] == "Aucune":
					jd = self.get_journey(j)
					if len(jd) == 2:
						for journey_part in jd:
							if journey_part.mode == "Bus":
								if journey_part.indic.line in only_lines:
									line = str(journey_part.indic.line)
									try:
										self.lines_found[line] += 1
									except KeyError as e:
										self.lines_found[line] = 1
		print "Found lines: ", self.lines_found.keys()
		return self.lines_found.keys()

	def raz(self):
		if not self.current_id == "":
			url = self.baseurl + "?id=" + self.current_id
			if not self.etape == "":
				url += "&etape=" + self.etape
				if self.args.list_stops:
					url += "&Line=" + self.args.list_stops
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

if __name__ == '__main__':
	FilBleu()
