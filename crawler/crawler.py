#pip install BeautifulSoup4
#pip install validators
#pipenv install requests

# References:
#	https://www.digitalocean.com/community/tutorials/how-to-scrape-web-pages-with-beautiful-soup-and-python-3

#	REQUESTS: used to load the page
#   http://www.pythonforbeginners.com/requests/using-requests-in-python
#	http://docs.python-requests.org/en/master/user/quickstart/ 
#	BEAUTIFUL SOUP: used to parse the page for data (urls)
#	http://www.pythonforbeginners.com/beautifulsoup/beautifulsoup-4-python
#	https://beautiful-soup-4.readthedocs.io/en/latest/
#	VALIDATORS: used to validate the urls found
#	http://validators.readthedocs.io/en/latest/#

#	Queue module: Thinking ahead...states "especially useful in 
#	threaded programming when information must be exchanged safely between multiple threads"
#	**Can be used as both a queue and as a stack
# 	https://docs.python.org/2/library/queue.html

import Queue
from urlparse import urljoin
import requests
import validators
from bs4 import BeautifulSoup
import time


def parsePage(URL):
	#fetches web page
	#by default request will keep waiting for a response forever - use timeout
	response = requests.get(URL, timeout=5)

	#checks status code against code lookup object
	if (response.status_code == requests.codes.ok):
		myPage = response.content
		soup = BeautifulSoup(myPage, 'lxml')
		return soup

	else:
		print "Error loading page: ", response.status_code
		return None

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

	#testing with hardcoded base url
	urls = ["http://www.google.com", "http://www.khanacademy.org", "http://www.github.com"]
	for url in urls:
		q = Queue.Queue()
		start = time.time()
		page = parsePage(url)

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
		end = time.time()
		print(end - start)

main()
