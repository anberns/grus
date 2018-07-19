#pip install BeautifulSoup4
#pip install validators
#pip install selenium
#pip install lxml


# References:
#	https://www.digitalocean.com/community/tutorials/how-to-scrape-web-pages-with-beautiful-soup-and-python-3

#	SELENIUM: changed from requests because it wasn't handling pages made with React
#	https://medium.com/@pyzzled/running-headless-chrome-with-selenium-in-python-3f42d1f5ff1d
#	BEAUTIFUL SOUP: used to parse the page for data (urls)
#	http://www.pythonforbeginners.com/beautifulsoup/beautifulsoup-4-python
#	https://beautiful-soup-4.readthedocs.io/en/latest/
#	VALIDATORS: used to validate the urls found
#	http://validators.readthedocs.io/en/latest/#

#	Queue module: Thinking ahead...states "especially useful in 
#	threaded programming when information must be exchanged safely between multiple threads"


from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from random import randrange
import validators
import json
import collections
import queue
import os

#import time

#class Logger:

class Spider(object):
	def __init__(self, browser, URL, limit, keyword=None):
		self.browser = browser
		self.start = URL\
		self.limit = limit
		if keyword is not None:
			self.keyword = keyword
		self.visited = collections.defaultdict(dict)

	def parsePage(self, URL):
		#fetches web page
		self.browser.get(URL)

		#checks status code against code lookup object
		soup = BeautifulSoup(self.browser.page_source, 'lxml')
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

	def validateURL(self, url):
		if not validators.url(url): #not valid
			return False
		else if url in self.URL_list: #already in the list
			return False
		else: 
			return True




class BFS(Spider):

	def __init__ (self, browser, URL, limit, keyword=None):
		self.URL_list = queue.Queue()
		#inherit Spider constructor
		super(BFS, self).__init__(browser, URL, limit, keyword=None)

	def findConnections(self, base, soup):
		URL_list= []
		#find_all looks for all links on the page
		for link in soup.find_all('a', href=True):
			url = link['href']
			url = url.rstrip('/')

			#handles relative URLs - by looking for links lacking http and 
			#joining these to the base URL to form an absolute URL
			if not url.startswith('http'):
				url = urljoin(base, url)

			#verifies link found is valid url and not a duplicate
			if self.validateURL(url):
				URL_list.append(url)

		return URL_list

	def search(self):
		#holds url and depth for each parent in queue before being processed
		parentinfo = {}

		#starting url
		currentURL = self.start		
		depth = 0
		myParent = "None"
		keywordFound = False

		#while the depth of visited pages is less than the user-set limit
		while (depth < self.limit + 1) && !keywordFound:

			if currentURL not in self.visited:
				#parse that page
				soup = self.parsePage(currentURL)

				#saves information about that page
				link_info = {}
				link_info['url'] = currentURL
				link_info['title'] = self.findPageTitle(soup)
				link_info['links'] = self.findConnections(currentURL, soup)
				link_info['depth'] = depth
				link_info['parent'] = myParent
				self.visited[currentURL] = link_info

				#all children must be put into the queue as URL_list for next iteration
				for link in link_info['links']:
					parentinfo = {}
					parentinfo['url'] = link
					parentinfo['depth'] = depth + 1
					parentinfo['parent'] = currentURL
					self.URL_list.put(parentinfo)

				if (keyword!=None) && (soup.find_all(string=keyword)):
					keywordFound = True

			#gets next parent url and depth from queue
			parent = self.URL_list.get()
			currentURL = parent.get('url')
			depth = parent.get('depth')	
			myParent = parent.get('parent')
			currentURL.rstrip('/')


class DFS(Spider):

	def __init__ (self, browser, URL, limit, keyword=None):
		self.URL_list = []
		super(DFS, self).__init__(browser, URL, limit, keyword=None)

	def findConnections(self, base, soup):
		#find_all looks for all links on the page
		for link in soup.find_all('a', href=True):
			url = link['href']

			#handles relative URLs - by looking for links lacking http and 
			#joining these to the base URL to form an absolute URL
			if not url.startswith('http'):
				url = urljoin(base, url)

			#verifies link found is valid url
			if self.validateURL(url):
				self.URL_list.append(url)

		#print ("DFS Connections found: ")
		#print(len(self.URL_list))


	def nextConnection(self):		
		random = randrange(0, len(self.URL_list))

		#looks at random url chosen to see if already visited
		while (self.URL_list[random] in self.visited):
			random = randrange(0, len(self.URL_list))

		#returns random url from page to follow
		return self.URL_list[random]


	def search(self):
		#while the number of visited pages is less than the user-set limit
		currentURL = self.start
		depth = 0
		myParent = "None"
		keywordFound = False

		while (len(self.visited) < self.limit+1) && !keywordFound:
			#get the first/last url in the list (LIFO or FIFO), depending on search type
			currentURL.rstrip('/')

			#parse that page
			soup = self.parsePage(currentURL)

			#enter information on page
			link_info = {}
			link_info['url'] = currentURL
			link_info['title'] = self.findPageTitle(soup)
			link_info['depth'] = depth
			self.findConnections(currentURL, soup)
			link_info['links'] = self.URL_list.copy()
			link_info['parent'] = myParent

			#copies info into visited lsit
			self.visited[currentURL] = link_info

			#checks if keyword found to stop the search
			if (keyword!=None) && (soup.find_all(string=keyword)):
					keywordFound = True

			else: #sets up for next iteration
			#gets random next link from list of children
			nextLink = self.nextConnection()
			myParent = currentURL 

			#clears the URL_list for next page
			self.URL_list.clear()
			currentURL = nextLink
			depth += 1


#testing functions 
def crawl(url, limit, sType, keyword):

	chrome_bin = os.environ.get('GOOGLE_CHROME_SHIM', None)
	options = webdriver.ChromeOptions()
	options.binary_location = chrome_bin
	options.add_argument("--headless")
	options.add_argument("--no-sandbox")
	options.add_argument("--disable-gpu")
	browser = webdriver.Chrome(chrome_options=options, executable_path="./chromedriver")
	
	if sType == "dfs":
		print("DFS on " + url) 
		crawler = DFS(browser, url, limit, keyword)
		crawler.search()
		#crawler.printVisited()
	
	else:
		print("BFS on " + url)
		crawler = BFS(browser, url, limit, keyword)
		crawler.search()
		#crawler.printVisited()

	browser.quit()
	
	return crawler.getVisited()

#main()
