#pip install BeautifulSoup4
#pip install validators
#pipenv install requests
#pip install lxml


# References:
#	https://www.digitalocean.com/community/tutorials/how-to-scrape-web-pages-with-beautiful-soup-and-python-3
#	BEAUTIFUL SOUP: used to parse the page for data (urls)
#	http://www.pythonforbeginners.com/beautifulsoup/beautifulsoup-4-python
#	https://beautiful-soup-4.readthedocs.io/en/latest/
#	VALIDATORS: used to validate the urls found
#	http://validators.readthedocs.io/en/latest/#

#	Queue module: Thinking ahead...states "especially useful in
#	threaded programming when information must be exchanged safely between multiple threads"


from urllib.parse import urljoin
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import requests
import random
from random import randrange
import validators
import json
import collections
import queue
import os
import re
import sys
import time
import urllib.robotparser

class Spider(object):
	
	def __init__(self, URL, limit, keyword=None):
		self.start = URL
		self.limit = limit
		if keyword:
			self.keyword = keyword
		else:
			self.keyword = None
		self.visited = collections.defaultdict(dict)
		self.rulesDict = {}
		self.noRules = []

	def checkRbTXT(self, URL):
		parsed_uri = urlparse(URL)
		base = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)

		if base in self.noRules:
			return True

		if base not in self.rulesDict:
			#print("Robots.txt link: ", rbtxt)
			rules = urllib.robotparser.RobotFileParser()
			rules.set_url(urljoin(base,'robots.txt'))	
	
			try:
				print("Fetching rules for:", base)
				rules.read()

			except:
				print("Cannot fetch rules from:", base)
				self.noRules.append(base)
				return True
			
			else:
				self.rulesDict[base] = rules
		
		if not self.rulesDict[base].can_fetch("*", URL):
			print (URL, "was NOT INCLUDED per robots.txt")
	
		return self.rulesDict[base].can_fetch("*", URL)
			

	def checkMedia(self, URL):
		#print("Checking for media...")
		toIgnore = ['mp4', 'mp3', 'mov', 'flv', 'wmv', 'avi', 'png', 'gif', 'jpg', 'bmp']
		for ending in toIgnore:
			if URL.endswith(ending):
				return False
		return True

	
	def parsePage(self, URL):
		try:  #attempts to load page first
			response = requests.get(URL, timeout=5)
			response.raise_for_status()

		#returns None upon any page loading error
		except requests.exceptions.HTTPError:
			print("Error in retrieving URL")
			return None
		except requests.exceptions.SSLError:
			print("Error in SSL certificate")
			return None
		except requests.exceptions.Timeout:
			print("Error in retrieving URL due to Timeout")
			return None
		except requests.exceptions.TooManyRedirects:
			print("Error in retrieving URL due to redirects")
			return None
		except requests.exceptions.RequestException:
			print("Error in retrieving URL")
			return None

		#or returns soup
		else:
			myPage = response.content
			soup = BeautifulSoup(myPage, 'lxml')
			#print("Getting Soup")
			return soup
			

		
	def findPageTitle(self, soup):
		#finds the first title tag
		title = soup.title
		if title is not None:
			return title.get_text()

	def printVisited(self):
		print("Visited List: ")
		print((json.dumps(self.visited, indent=4)))

	def getVisited(self):
		return self.visited



class BFS(Spider):

	def __init__ (self, URL, limit, keyword=None):
		self.URL_list = queue.Queue()
		#inherit Spider constructor
		super(BFS, self).__init__(URL, limit, keyword)

	def findConnections(self, base, soup):
		connections= []
		#find_all looks for all links on the page
		for link in soup.find_all('a', href=True):
			url = link['href']
			url.rstrip('/')

			#handles relative URLs - by looking for links lacking http and
			#joining these to the base URL to form an absolute URL
			if not url.startswith('http') and not url.startswith('#'):
				url = urljoin(base, url)

			#removes query params so as not to have repeated websites
			removeQuery = url.split('?')
			url = removeQuery[0]

			#verifies link found is valid url and not a duplicate
			if validators.url(url) and url not in connections:
				connections.append(url)

		return connections

	def search(self, ws):
		#holds url and depth for each parent in queue before being processed
		parentinfo = {
			'url': self.start,
			'depth':  0,
			'parent': None
		}
		depth = 0
		self.URL_list.put(parentinfo)

		#starting url
		keywordFound = False

		#while the depth of visited pages is less than the user-set limit
		while not keywordFound and not self.URL_list.empty():

			parent = self.URL_list.get()
			currentURL = parent.get('url')
			depth = parent.get('depth')
			myParent = parent.get('parent')
			currentURL.rstrip('/')

			if depth > self.limit:
				break

			if currentURL not in self.visited:
				#parse that page
				soup = self.parsePage(currentURL)

				if soup is not None:
					#saves information about that page
					link_info = {}
					link_info['url'] = currentURL
					link_info['title'] = self.findPageTitle(soup)
					link_info['links'] = self.findConnections(currentURL, soup)
					link_info['depth'] = depth
					link_info['parent'] = myParent
					link_info['found'] = False

					if (self.keyword != None) and soup.find_all(string=re.compile(r'\b%s\b' % self.keyword, re.IGNORECASE)):
							keywordFound = True
							link_info['found'] = True
							print("FOUND KEYWORD: ", self.keyword)

					self.visited[currentURL] = link_info

					# send info to visualizer
					ws.send(json.dumps(link_info))

					#all children must be put into the queue as URL_list for next iteration
					for link in link_info['links']:
						if self.checkMedia(link) and self.checkRbTXT(link):
							parentinfo = {}
							parentinfo['url'] = link
							parentinfo['depth'] = depth + 1
							parentinfo['parent'] = currentURL
							self.URL_list.put(parentinfo)


class DFS(Spider):

	def __init__ (self, URL, limit, keyword=None):
		self.URL_list = []
		super(DFS, self).__init__(URL, limit, keyword)

	def findConnections(self, base, soup):
		#find_all looks for all links on the page
		for link in soup.find_all('a', href=True):
			url = link['href']
			url.rstrip('/')


			#handles relative URLs - by looking for links lacking http and
			#joining these to the base URL to form an absolute URL
			if not url.startswith('http') and not url.startswith('#'):
				url = urljoin(base, url)

			#removes query params so as not to have repeated websites
			removeQuery = url.split('?')
			url = removeQuery[0]

			#verifies link found is valid url and not a duplicate
			if validators.url(url) and url not in self.URL_list and url not in self.visited:
				self.URL_list.append(url)

	def nextConnection(self):
		if self.URL_list:
			random = randrange(0, len(self.URL_list))
			#return self.URL_list[random]
			#returns random url from page to follow
			if self.checkRbTXT(self.URL_list[random]):
				#print("Returning next available site to crawl")
				return self.URL_list[random]
			else:
				return "Excluded"
		else:
			print("No more links to crawl")
			return None

	def removeLink(self, url):
		if url in self.URL_list:
			self.URL_list.remove(url)

	def search(self, ws):
		#while the number of visited pages is less than the user-set limit
		currentURL = self.start
		depth = 0
		myParent = None
		keywordFound = False

		#while limit has not been reached, keyword hasn't been found and still urls available to crawl
		while (len(self.visited) < self.limit+1) and not keywordFound and currentURL != None:

			if self.checkMedia(currentURL) and currentURL != "Excluded":
				currentURL.rstrip('/')

				#parse that page
				soup = self.parsePage(currentURL)

				if soup is not None:  #parsePage returns None if page returns bad response code
					#clears the URL_list for next page
					self.URL_list.clear()

					#enter information on page
					link_info = {}
					link_info['url'] = currentURL
					link_info['title'] = self.findPageTitle(soup)
					link_info['depth'] = depth
					self.findConnections(currentURL, soup)
					link_info['links'] = self.URL_list.copy()
					link_info['parent'] = myParent
					link_info['found'] = False


					#checks if keyword found to stop the search
					if (self.keyword != None) and soup.find_all(string=re.compile(r'\b%s\b' % self.keyword, re.IGNORECASE)):
						keywordFound = True
						link_info['found'] = True
						print("FOUND KEYWORD: ", self.keyword)
					
					nextLink = self.nextConnection()
					myParent = currentURL
					currentURL = nextLink
					depth += 1

					self.visited[currentURL] = link_info
					
					# send info to visualizer
					ws.send(json.dumps(link_info))
					
				else:	#finds another connection from the current list
					self.removeLink(nextLink)
					currentURL = self.nextConnection()

			else:
				self.removeLink(nextLink)
				currentURL = self.nextConnection()


#testing functions
def crawl(ws, url, limit, sType, keyword):

	'''
	chrome_bin = os.environ.get('GOOGLE_CHROME_SHIM', None)
	options = webdriver.ChromeOptions()
	options.binary_location = chrome_bin
	options.add_argument("--headless")
	options.add_argument("--no-sandbox")
	options.add_argument("--disable-gpu")
	browser = webdriver.Chrome(chrome_options=options, executable_path="./chromedriver")
	'''

	'''
	#LOCAL
	chrome_options = Options(Proxy = null)
	chrome_options.add_argument("--headless")
	browser = webdriver.Chrome(chrome_options=chrome_options, executable_path="../crawler/chromedriver")
	'''

	if sType == "dfs":
		random.seed(time.time())
		print("DFS on " + url)
		crawler = DFS(url, limit, keyword)
		try:
			crawler.search(ws)
			ws.close(1000, "Closing Connection Normally")
			crawler.printVisited()
		except:
			print(sys.exc_info()[0])
			ws.close(1000, "Closing Connection Due to Crawler Error")

	else:
		print("BFS on " + url)
		crawler = BFS(url, limit, keyword)
		try:
			crawler.search(ws)
			ws.close(1000, "Closing Connection Normally")
			crawler.printVisited()
		except:
			print(sys.exc_info()[0])
			ws.close(1000, "Closing Connection Due to Crawler Error")

	return crawler.getVisited()


#crawl("https://www.apple.com", 15, "dfs", None)

