#pip install BeautifulSoup4
#pip install validators
#pipenv install requests
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
from bs4 import BeautifulSoup
import requests
from random import randrange
import validators
import json
import collections
import queue
import os
import re


class Spider(object):
	name = "findLinks"

	'''def __init__(self, *args, **kwargs):
		super(Spider, self).__init__(*args, **kwargs)

		self.start_urls = [kwargs.get('url')]
		#self.limit = kwargs.get('limit')
		#self.keyword = kwargs.get('keyword')

	'''
	def __init__(self, URL, limit, keyword=None):
		self.start = URL
		self.limit = limit
		if keyword:
			self.keyword = keyword
		else:
			self.keyword = None
		self.visited = collections.defaultdict(dict)

	def parsePage(self, URL):
		#fetches web page
		response = requests.get(URL, timeout=5)

		#checks status code against code lookup object
		if (response.status_code == requests.codes.ok):
			myPage = response.content
			soup = BeautifulSoup(myPage, 'lxml')
			return soup

		else:
			print("Error loading page: ", response.status_code)
			return None

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
			if validators.url(url):
				URL_list.append(url)

		return URL_list

	def search(self):
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
		while (depth < self.limit + 1) and not keywordFound and not self.URL_list.empty():

			parent = self.URL_list.get()
			currentURL = parent.get('url')
			depth = parent.get('depth')	
			myParent = parent.get('parent')
			currentURL.rstrip('/')

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

			if (self.keyword != None) and soup.find_all(string=re.compile('.*(%s).*'%self.keyword)):
					keywordFound = True
					print("FOUND KEYWORD: ", self.keyword)

			


class DFS(Spider):

	def __init__ (self, URL, limit, keyword=None):
		self.URL_list = []
		super(DFS, self).__init__(URL, limit, keyword)

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
				self.URL_list.append(url)


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
		myParent = None
		keywordFound = False

		while (len(self.visited) < self.limit+1) and not keywordFound:
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
			if (self.keyword != None) and soup.find_all(string=re.compile('.*(%s).*'%self.keyword)):
					keywordFound = True
					print("FOUND KEYWORD: ", self.keyword)

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
		print("DFS on " + url) 
		crawler = DFS(url, limit, keyword)
		try:
			crawler.search()
			crawler.printVisited()
		except:
			print("Error in Crawl")
	
	else:
		print("BFS on " + url)
		crawler = BFS(url, limit, keyword)
		try:
			crawler.search()
			crawler.printVisited()
		except:
			print("Error in Crawl")

	return crawler.getVisited()


#crawl("https://www.google.com", 5, "dfs", "ab8ght")

