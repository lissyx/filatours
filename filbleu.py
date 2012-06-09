#!/usr/bin/python

import re
import mechanize
import cookielib
import argparse
import BeautifulSoup

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
		self.current_id = ""
		self.etape = ""

		self.parser = argparse.ArgumentParser(description="FilBleu Scrapper")
		self.parser.add_argument("--list-lines", action="store_true", help="List lines")
		self.parser.add_argument("--list-stops", help="List stops of a line (format: n|M)")
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
		self.args = self.parser.parse_args()

		self.browser.set_debug_http(self.args.httpdebug)

		self.__process__()

	def html_br_strip(self, text):
		return "".join([l.strip() for l in text.split("\n")])

	def page_lines(self):
		self.current_id = "1-2"

	def page_stops(self):
		self.current_id = "1-2"
		self.etape = "2"

	def page_journey(self):
		self.current_id = "1-1"

	def list_stops(self):
		self.get_stops()
		for stop in self.stops:
			stop = self.stops[stop]
			print "Stop:", stop.stop_name, "(", stop.city, ") => ", stop.stopArea

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
			for stop in stops:
				if not stop["value"] == "":
					s = BusStop(stop.text)
					s.set_stopArea(stop["value"])
					self.stops[s.id] = s

	def list_lines(self):
		self.get_lines()
		for line in self.lines:
			line = self.lines[line]
			print "Line:", line.number, "[", line.id, "]"

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

	def get_journey(self):
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
						print "Dates:", dates, "Duration:", duration, "Connections:", connections, "[", link, "]"
			else:
				print "No table"
		else:
			print "No journey."

	def raz(self):
		if not self.current_id == "":
			url = self.baseurl + "?id=" + self.current_id
			if not self.etape == "":
				url += "&etape=" + self.etape
				if self.args.list_stops:
					url += "&Line=" + self.args.list_stops
			else:
				url += self.url_raz
			self.browser.open(url)

	def __process__(self):
		if self.args.list_lines:
			self.list_lines()
		if self.args.list_stops:
			self.list_stops()
		if self.args.journey:
			self.get_journey()

if __name__ == '__main__':
	FilBleu()
