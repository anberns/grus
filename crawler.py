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

#	Queue module: states "especially useful in threaded programming when information must 
#	be exchanged safely between multiple threads"


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
	
	#Constructor
	def __init__(self, URL, limit, keyword=None):
		if not URL.endswith('/'):
			URL = URL + '/'
		self.start = URL
		self.limit = limit
		if keyword:
			self.keyword = keyword
		else:
			self.keyword = None
		self.visited = collections.defaultdict(dict)
		self.rulesDict = collections.defaultdict(dict)
		self.noRules = []
		self.neverCrawl = []
		self.total = 0

	#Checks the robots.txt to see if crawls are allowed
	def checkRbTXT(self, URL):
		#parses the url to find the base url
		parsed_uri = urlparse(URL)
		base = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)

		if URL == self.start:
			return True

 		#checks if rules were already checked and found missing/unreadable
		if base in self.noRules:
			return True

		if base not in self.rulesDict:
			#create a robotparser and set the url
			rules = urllib.robotparser.RobotFileParser()
			rules.set_url(urljoin(base,'robots.txt'))	
	
			try:
				rules.read()

			except:
				#print("Cannot fetch rules from:", base)
				self.noRules.append(base)
				return True
			
			else:
				#add to dictionary of robots
				self.rulesDict[base] = rules
		
		if not self.rulesDict[base].can_fetch("*", URL):
			#print (URL, "was NOT INCLUDED per robots.txt")
			self.neverCrawl.append(URL)
	
		#return whether the site allows crawls for that URL
		return self.rulesDict[base].can_fetch("*", URL)
			

	def checkMedia(self, URL):
		#print("Checking for media...")
		if URL.endswith('/'):
			URL = URL[:-1]

		toIgnore = ['mp4', 'mp3', 'mov', 'flv', 'wmv', 'avi', 'png', 'gif', 'jpg', 'bmp']
		for ending in toIgnore:
			if URL.endswith(ending):
				return False
		return True

	
	def parsePage(self, URL):

		if URL in self.neverCrawl:
			return None

		if not self.checkRbTXT(URL):
			return None

		else:	
			try:  #attempts to load page first
				response = requests.get(URL, timeout=2)
				response.raise_for_status()

			#returns None upon any page loading error
			except requests.exceptions.HTTPError:
				#print("Error in retrieving URL HTTP Error: " + URL)
				self.neverCrawl.append(URL)
				return None
			except requests.exceptions.SSLError:
				#print("Error in SSL certificate")
				self.neverCrawl.append(URL)
				return None
			except requests.exceptions.Timeout:
				#print("Error in retrieving URL due to Timeout: " + URL)
				self.neverCrawl.append(URL)
				return None
			except requests.exceptions.TooManyRedirects:
				#print("Error in retrieving URL due to redirects")
				self.neverCrawl.append(URL)
				return None
			except requests.exceptions.RequestException:
				self.neverCrawl.append(URL)
				#print("Error in retrieving URL due to other error: " + URL)
				return None

			#or returns soup
			else:
				myPage = response.content
				soup = BeautifulSoup(myPage, 'lxml')
				#print("Getting Soup")
				return soup
		
	#formats the url to avoid repeated links and to create absolute urls	
	def formatURL(self, base, url):
		#handles relative URLs - by looking for links lacking http and
		#joining these to the base URL to form an absolute URL
		if not url.startswith('http') and not url.startswith('#'):
			url = urljoin(base, url)

		#removes query params so as not to have repeated websites
		removeQuery = url.split('?')
		url = removeQuery[0]
		
		if not url.endswith('/'):
			url = url + '/'

		return url

	def findPageTitle(self, soup):
		#finds the first title tag
		title = soup.title
		if title is not None:
			return title.get_text()

class BFS(Spider):
	#constructor - inherits from Spider
	def __init__ (self, URL, limit, keyword=None):
		self.URL_list = queue.Queue()
		#inherit Spider constructor
		super(BFS, self).__init__(URL, limit, keyword)

	#finds and returns links on page
	def findConnections(self, base, parent, soup):
		connections= []
		#find_all looks for all links on the page
		for link in soup.find_all('a', href=True):
			url = link['href']

			#formats the url
			url = self.formatURL(base, url)

			#verifies link found is valid url and not a duplicate and not the same as the parent url
			if validators.url(url) and url not in connections and url != parent:
				self.total += 1
				connections.append(url)

		return connections

	#completes the breadth first search
	def search(self, ws, postid, database):
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
		while not keywordFound and not self.URL_list.empty() and self.total < 35000:
			#saves off data to send
			parent = self.URL_list.get()
			currentURL = parent.get('url')
			depth = parent.get('depth')
			myParent = parent.get('parent')
			
			#checks if limit has been reached
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
					link_info['links'] = self.findConnections(currentURL, myParent, soup)
					link_info['depth'] = depth
					link_info['parent'] = myParent
					link_info['found'] = False

					#checks for keyword if one was entered
					if (self.keyword != None) and soup.find_all(string=re.compile(r'\b%s\b' % self.keyword, re.IGNORECASE)):
							keywordFound = True
							link_info['found'] = True
							print("FOUND KEYWORD: ", self.keyword)
							try: 
								database.update_one(
									{'_id': postid},
									{ 
										'$set': { 'found': True}
									}
								)
							except Exception as e:
								print(str(e))

					#adds to visited list
					self.visited[currentURL] = True

					# send info to visualizer
					ws.send(json.dumps(link_info))

					#store in database
					try: 
						database.update_one(
							{'_id': postid},
							{ 
								'$push': { 'path': json.dumps(link_info)}
							}
						)
					except Exception as e:
						print(str(e))

					#all children must be put into the queue as URL_list for next iteration
					for link in link_info['links']:
						if self.checkMedia(link) and link not in self.visited:
							parentinfo = {}
							parentinfo['url'] = link
							parentinfo['depth'] = depth + 1 #update depth
							parentinfo['parent'] = currentURL
							self.URL_list.put(parentinfo)


class DFS(Spider):

	#constructor
	def __init__ (self, URL, limit, keyword=None):
		self.URL_list = []
		super(DFS, self).__init__(URL, limit, keyword)

	#finds links on parent page
	def findConnections(self, base, parent, soup):
		#find_all looks for all links on the page
		for link in soup.find_all('a', href=True):
			url = link['href']

			#formats URL
			url = self.formatURL(base, url)
			
			#verifies link found is valid url and not a duplicate
			if validators.url(url) and url not in self.URL_list and url not in self.visited and url != parent and self.total < 35000:
				self.total += 1
				self.URL_list.append(url)

	#finds and returns a random link from the list
	def nextConnection(self):
		if self.URL_list:
			random = randrange(0, len(self.URL_list))
			return self.URL_list[random]
		else:
			print("No more links to crawl")
			return None

	#removes invalid links from the list to avoid repeated attempts to crawl
	def removeLink(self, url):
		if url in self.URL_list:
			self.URL_list.remove(url)

	#performs the depth first search
	def search(self, ws, postid, database):
		#saves off information
		currentURL = self.start
		depth = 0
		myParent = None
		keywordFound = False

		#while limit has not been reached, keyword hasn't been found and still urls available to crawl
		while (len(self.visited) < self.limit+1) and not keywordFound and currentURL != None:

			if self.checkMedia(currentURL):

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
					self.findConnections(currentURL, myParent, soup)
					link_info['links'] = self.URL_list.copy()
					link_info['parent'] = myParent
					link_info['found'] = False


					#checks if keyword found to stop the search
					if (self.keyword != None) and soup.find_all(string=re.compile(r'\b%s\b' % self.keyword, re.IGNORECASE)):
						keywordFound = True
						link_info['found'] = True
						print("FOUND KEYWORD: ", self.keyword)
						try: 
							database.update_one(
								{'_id': postid},
								{ 
									'$set': { 'found': True}
								}
							)
						except Exception as e:
							print(str(e))
					
					nextLink = self.nextConnection()
					myParent = currentURL
					currentURL = nextLink
					depth += 1				#update the current depth

					self.visited[currentURL] = True
					
					# send info to visualizer
					ws.send(json.dumps(link_info))

					#store in database
					try: 
						database.update_one(
							{'_id': postid},
							{ 
								'$push': { 'path': json.dumps(link_info)}
							}
						)
					except Exception as e:
						print(str(e))

				else:	#finds another connection from the current list
					self.removeLink(nextLink)
					currentURL = self.nextConnection()

			else:
				self.removeLink(nextLink)
				currentURL = self.nextConnection()


#testing functions
def crawl(ws, url, limit, sType, keyword, postid, database):

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
			crawler.search(ws, postid, database)
			ws.close(1000, "Closing Connection Normally")
		except:
			print(sys.exc_info())
			ws.close(1000, "Closing Connection Due to Crawler Error")

	else:
		print("BFS on " + url)
		crawler = BFS(url, limit, keyword)
		try:
			crawler.search(ws, postid, database)
			ws.close(1000, "Closing Connection Normally")
		except:
			print(sys.exc_info())
			ws.close(1000, "Closing Connection Due to Crawler Error")


