import uuid
import json
import sys
import crawler
from socket import error as SocketError
import errno
from flask import Flask, request, render_template, make_response
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://heroku_zlgnt8hx:8qj45t037p6on1oj0r472epmhq@ds233551.mlab.com:33551/heroku_zlgnt8hx"
mongo = PyMongo(app)

# index page with form
@app.route('/')
def index():
	userId = request.cookies.get('userId')

	if userId:
		# get stored data
		test = mongo.db.test  # access test collection
		storedCrawls = test.find({'userId': userId})
		return render_template('index.html', crawls=storedCrawls)
	else:
		userId = str(uuid.uuid4())
		resp = make_response(render_template('index.html'))
		resp.set_cookie('userId', userId)
		return resp



# to be used to call webcrawler with posted data
@app.route('/submit', methods=['POST'])
def crawl():

	userId = request.cookies.get('userId')
	url = "https://" + request.form['url']
	limit = request.form['limit']
	sType = request.form['type']
	keyword = request.form['keyword']

	#webcrawler call goes here
	crawlData = json.dumps(crawler.crawl(url, int(limit), sType, keyword))

	#store search in database
	test = mongo.db.test #access test collection
	postid = test.insert({'userId' : userId, 'url': url, 'limit': limit, 'sType' : sType, 'keyword' : keyword, 'path' : crawlData})

	# get data from id
	queryData = test.find_one({'_id': postid})
	print(queryData)

	return render_template('show_data.html', data=queryData['path'], url=queryData['url'], type=queryData['sType'])

@app.route('/previous', methods=['POST'])
def getPreviousCrawl():

	#clicked _id from previous crawls list
	docId = request.form['prev']

	test = mongo.db.test #access test collection

	#get data from id
	queryData = test.find_one({'_id' : ObjectId(docId)})

	return render_template('show_data.html', data=queryData['path'], url=queryData['url'], type=queryData['sType'])


if __name__ == "__main__":
	app.run()
