#!/usr/bin/python

import re
import mechanize
import cookielib
import argparse
import BeautifulSoup

class BusStop:
	def __init__(self, name):
		self.name = name

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

	def __repr__(self):
		repr = "{'id': " + self.id + ", 'number': " + self.number + ", "
		repr += "'ends': " + str(self.ends) + ", "
		repr += "'stops': " + str(self.stops)
		return repr + "}"

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
		self.args = self.parser.parse_args()

		self.browser.set_debug_http(self.args.httpdebug)

		self.__process__()

	def page_lignes(self):
		self.current_id = "1-2"

	def page_arrets(self):
		self.current_id = "1-2"
		self.etape = "2"

	def list_stops(self):
		self.get_stops()
		for stop in self.stops:
			print self.stops[stop]

	def get_stops_sens(self, sens):
		self.page_arrets()
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
			print soup

	def list_lines(self):
		self.get_lines()
		for line in self.lines:
			print self.lines[line]

	def get_lines(self):
		self.page_lignes()
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
						stop = "".join([l.strip() for l in div.text.split("\n")])
						if len(divs) > 1:
							stops.append(stop)
						else:
							stops = stop
					self.lines[lineid].add_end(stops)
				else:
					stop = "".join([l.strip() for l in line.text.split("\n")])
					if len(stop) > 0:
						self.lines[lineid].add_end(stop)

	def page_itineraires(self):
		self.current_id = "1-1"

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

if __name__ == '__main__':
	FilBleu()
