import os
import time
import uuid
import json
import sys
import crawler
from socket import error as SocketError
import errno
from flask import Flask, request, render_template, make_response, redirect, session
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from flask_sockets import Sockets

app = Flask(__name__)
app.secret_key = os.urandom(24)

app.config["MONGO_URI"] = "mongodb://heroku_l49w3pqw:corelnjkhviq52q7gsmalc504c@ds139331.mlab.com:39331/heroku_l49w3pqw"
mongo = PyMongo(app)
sockets = Sockets(app)

global userId, url, limit, sType, keyword
userId = None
url = None
limit = None
sType = None
keyword = None

# index page with form
@app.route('/')
def index():
	global userId
	userId = request.cookies.get('userId')

	if userId:
		# get stored data
		test = mongo.db.test  # access test collection
		storedCrawls = test.find({'userId': userId})
		return render_template('index.html', crawls=storedCrawls)
	else:
		userId = str(uuid.uuid4())
		response = make_response(render_template('index.html'))
		response.set_cookie('userId', userId)
		return response



# to be used to call webcrawler with posted data
@app.route('/submit', methods=['POST'])
def launch():
	global userId, url, limit, sType, keyword
	userId = request.cookies.get('userId')
	url = "https://" + request.form['url']
	limit = request.form['limit']
	sType = request.form['type']
	keyword = request.form['keyword']

	session['userId']= userId
	session['url'] = url
	session['limit'] = limit
	session['sType'] = sType
	session['keyword'] = keyword

	#adding tracing statement
	print("Value Before Fork: userID=", userId, " url=", url, " limit=", limit, " sType=", sType, "keyword=", keyword)

	time.sleep(1)
	return render_template('show_data.html', data=None, url=url, keyword=keyword, type=sType)


@sockets.route('/crawl')
def startCrawl(ws):
	global userId, url, limit, sType, keyword
	userId = session['userId']
	url = session['url'] 
	limit = session['limit'] 
	sType = session['sType'] 
	keyword = session['keyword'] 

	#adding tracing statement
	print("Value before crawl: userID=", userId, " url=", url, " limit=", limit, " sType=", 
		  sType, "keyword=", keyword)

	crawlData = json.dumps(crawler.crawl(ws, url, int(limit), sType, keyword))

	#store search in database
	mongo = PyMongo(app)
	test = mongo.db.test #access test collection
	postid = test.insert({'userId' : userId, 'url': url, 'limit': limit, 'sType' : sType, 'keyword' : keyword, 'path' : crawlData})


@app.route('/previous', methods=['POST'])
def getPreviousCrawl():

	#clicked _id from previous crawls list
	docId = request.form['prev']

	test = mongo.db.test #access test collection

	#get data from id
	queryData = test.find_one({'_id' : ObjectId(docId)})

	return render_template('show_data.html', data=queryData['path'], url=queryData['url'], type=queryData['sType'], keyword=queryData['keyword'])


if __name__ == "__main__":
	app.run()
