#!/usr/bin/python

import re
import mechanize
import cookielib
import argparse
import BeautifulSoup

class FilBleu:
	def __init__(self):
		self.browser = mechanize.Browser()
		self.cj = cookielib.LWPCookieJar()
		self.browser.set_cookiejar(self.cj)
		self.baseurl = "http://www.filbleu.fr/page.php"
		self.url_raz = "&raz"
		self.current_id = ""

		self.parser = argparse.ArgumentParser(description="FilBleu Scrapper")
		self.parser.add_argument("--list-lines", action="store_true", help="List lines")
		self.parser.add_argument("--list-stops", type=int, help="List stops of a line")
		self.parser.add_argument("--httpdebug", action="store_true", help="Show HTTP debug")
		self.args = self.parser.parse_args()

		self.browser.set_debug_http(self.args.httpdebug)

		self.__process__()
	
	def page_arrets(self):
		self.current_id = "1-2"
	
	def list_lines(self):
		self.page_arrets()
		self.raz()
		self.lines = {}
		soup = BeautifulSoup.BeautifulSoup(self.browser.response().read())
		for line in soup.findAll('a', attrs = { 'style': 'text-decoration:none' }):
			search = re.compile(r"Line=(.*)\|(.*)").search(line['href'])
			if search:
				lineid = search.group(1)
				linenb = search.group(2)
				
				if not self.lines.has_key(lineid):
					self.lines[lineid] = {'id': lineid, 'number': linenb, 'ends': []}

				divs = line.findAll('div')
				if divs:
					stops = []
					for div in divs:
						stop = "".join([l.strip() for l in div.text.split("\n")])
						if len(divs) > 1:
							stops.append({'dest': stop})
						else:
							stops = {'dest': stop}
					self.lines[lineid]['ends'].append(stops)
				else:
					stop = "".join([l.strip() for l in line.text.split("\n")])
					if len(stop) > 0:
						self.lines[lineid]['ends'].append({'dest': stop})
		print self.lines['1']
		print self.lines['2']
		print self.lines['5']
		print self.lines['33']
	
	def page_itineraires(self):
		self.current_id = "1-1"
	
	def raz(self):
		if not self.current_id == "":
			url = self.baseurl + "?id=" + self.current_id + self.url_raz
			self.browser.open(url)
	
	def __process__(self):
		if self.args.list_lines:
			self.list_lines()

if __name__ == '__main__':
	FilBleu()
