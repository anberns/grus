#pip install BeautifulSoup4
#pip install validators
#pip install selenium

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
#	**Can be used as both a queue and as a stack
# 	https://docs.python.org/2/library/queue.html

from urlparse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import Queue
import validators
import time


def startBrowser():
	chrome_options = Options()
	chrome_options.add_argument("--headless")
	browser = webdriver.Chrome(chrome_options=chrome_options, executable_path="./chromedriver")
	return browser

def parsePage(URL, browser):
	#fetches web page
	#by default request will keep waiting for a response forever - use timeout	
	browser.get(URL)

	#checks status code against code lookup object
	soup = BeautifulSoup(browser.page_source, 'lxml')
	return soup

def findPageTitle(soup):
	#finds the first title tag
	title = soup.title
	if title is not None:
		return title.get_text()


def addLinkstoQueue(base, soup, queue):
	#find_all looks for all links on the page
	for link in soup.find_all('a', href=True):
		url = link['href']

		#handles relative URLs - by looking for links lacking http and 
		#joining these to the base URL to form an absolute URL
		if not url.startswith('http'):
			url = urljoin(base, url)

		#verifies link found is valid url and not a duplicate
		if(validators.url(url)) and url not in list(queue.queue):
			queue.put(url)

def addLinkstoStack(base, soup, stack):
	#find_all looks for all links on the page
	for link in soup.find_all('a', href=True):
		url = link['href']

		#handles relative URLs - by looking for links lacking http and 
		#joining these to the base URL to form an absolute URL
		if not url.startswith('http'):
			url = urljoin(base, url)

		#verifies link found is valid url and not a duplicate
		if validators.url(url): #and url not in list(stack.queue):
			stack.put(url)
			

#testing functions 
def main():
	browser = startBrowser()

	#testing with hardcoded base url
	urls = ["http://www.google.com", "http://www.khanacademy.org", "http://www.github.com"]

	for url in urls:
		q = Queue.Queue()
		#start= time.time ()
		page = parsePage(url, browser)
		title = findPageTitle(page)

		#testing page's title
		print "Title of page being parsed: ", title

		addLinkstoQueue(url, page, q)

		#testing - prints the links in the queue and the total count
		count = 0
		for link in list(q.queue):
			print(link)
			count += 1
		print "Total Links in Queue: ", count
		#end = time.time()
		#print(end - start)

main()
