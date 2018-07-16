import uuid
import json
import sys
import crawler
from flask import Flask, request, render_template, make_response 
from flask_pymongo import PyMongo
app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://heroku_l49w3pqw:corelnjkhviq52q7gsmalc504c@ds139331.mlab.com:39331/heroku_l49w3pqw"
mongo = PyMongo(app)

#index page with form
@app.route('/')
def index():
	userId = request.cookies.get('userId')

	if userId:
		#get stored data
		test = mongo.db.test #access test collection
		storedCrawls = test.find({'userId' : userId})
		return render_template('index.html', crawls=storedCrawls)
	else:
		userId = str(uuid.uuid4())
		resp = make_response(render_template('index.html'))
		resp.set_cookie('userId', userId)
		return resp

#to be used to call webcrawler with posted data
@app.route('/submit', methods=['POST'])
def crawl():

	userId = request.cookies.get('userId')
	url = "https://" + request.form['url']
	limit = request.form['limit']
	sType = request.form['type']
	keyword = request.form['keyword']

	#webcrawler call goes here
	crawlData = json.dumps(crawler.crawl(url, int(limit), sType, keyword))

	#crawlData = {"path" : {"start" : request.form['url'], "1" : "www.test1.com", "2" : "www.test2.com", "3" : "www.test3.com", "4" : "www.test4.com"}, "found" : 'false' }

	#temporary template to show posted data
	#return render_template('show_data.html', data=crawlData)

	#store search in database
	test = mongo.db.test #access test collection
	postid = test.insert({'userId' : userId, 'url': url, 'limit': limit, 'sType' : sType, 'keyword' : keyword, 'path' : crawlData}) 

	#get data from id
	queryData = test.find_one({'_id' : postid})

	return render_template('show_result.html', docId=postid, qData=queryData)


if __name__ == "__main__":
	app.run()

