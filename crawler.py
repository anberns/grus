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

# change path to chrome binary for heroku
#comment out for local instances
ChromeOptions options = new ChromeOptions()
options.setBinary("/app/.apt/usr/bin/google-chrome")
ChromeDriver driver = new ChromeDriver(options)

#import time

#class Logger:

class Spider(object):
	def __init__(self, browser, URL, limit, keyword=None):
		self.browser = browser
		self.start = URL
		self.keyword = keyword
		self.limit = limit
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




class BFS(Spider):

	def __init__ (self, browser, URL, limit, keyword=None):
		self.parents = queue.Queue()
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
			if validators.url(url)and url not in URL_list:
				URL_list.append(url)

		#print("BFS Connections Found:") 
		#print(len(URL_list))

		return URL_list

	def search(self):
		#holds url and depth for each parent in queue before being processed
		parentinfo = {}

		#starting url
		parentURL = self.start		
		depth = 0

		#while the depth of visited pages is less than the user-set limit
		while (depth < self.limit + 1):

			if parentURL not in self.visited:
				#parse that page
				soup = self.parsePage(parentURL)

				#saves information about that page
				link_info = {}
				link_info['url'] = parentURL
				link_info['title'] = self.findPageTitle(soup)
				link_info['links'] = self.findConnections(parentURL, soup)
				link_info['depth'] = depth
				self.visited[parentURL] = link_info

			#all children must be put into the queue as parents for next iteration
			for link in link_info['links']:
				parentinfo = {}
				parentinfo['url'] = link
				parentinfo['depth'] = depth + 1
				self.parents.put(parentinfo)

			#gets next parent url and depth from queue
			parent = self.parents.get()
			parentURL = parent.get('url')
			depth = parent.get('depth')	
			parentURL.rstrip('/')



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
			if validators.url(url) and url not in self.URL_list: 
				url = url.rstrip('/')
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
		url = self.start
		depth = 0

		while (len(self.visited) < self.limit):
			#get the first/last url in the list (LIFO or FIFO), depending on search type
			url.rstrip('/')

			if url not in self.visited:

				#parse that page
				soup = self.parsePage(url)

				#enter information on page
				link_info = {}
				link_info['url'] = url
				link_info['title'] = self.findPageTitle(soup)
				link_info['depth'] = depth
				self.findConnections(url, soup)
				link_info['links'] = self.URL_list.copy()

				#copies info into visited lsit
				self.visited[url] = link_info

				#gets random next link from list of children
				nextLink = self.nextConnection()

				#clears the URL_list for next page
				self.URL_list.clear()

			url = nextLink
			depth += 1


#testing functions 
def crawl(url, limit, sType, keyword):
	chrome_options = Options()
	chrome_options.add_argument("--headless")
	browser = webdriver.Chrome(chrome_options=chrome_options, executable_path="./chromedriver")

	#limit = 2
	#keyword = None

	#testing with hardcoded base url with test pages structure
	#test_url = "http://www.bomanbo.com/"
	
	if sType == "dfs":
		print("DFS on " + url) 
		crawler = DFS(browser, url, limit, keyword)
		crawler.search()
		crawler.printVisited()
		#crawler.printConnections()
	
	else:
		print("BFS on " + url)
		crawler = BFS(browser, url, limit, keyword)
		crawler.search()
		crawler.printVisited()
		#crawler.printConnections()

	browser.quit()
	
	return crawler.getVisited()

#main()
