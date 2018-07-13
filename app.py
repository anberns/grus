from flask import Flask, request, render_template
from flask_pymongo import PyMongo
app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://heroku_zlgnt8hx:8qj45t037p6on1oj0r472epmhq@ds233551.mlab.com:33551/heroku_zlgnt8hx"
mongo = PyMongo(app)

#index page with form
@app.route('/')
def index():
	return render_template('index.html')

#to be used to call webcrawler with posted data
@app.route('/submit', methods=['POST'])
def crawl():

	url = request.form['url']
	limit = request.form['limit']
	sType = request.form['type']
	keyword = request.form['keyword']

	#webcrawler call goes here
	#crawlData = callCrawler(url, limit, sType, keyword)

	crawlData = {"path" : {"start" : request.form['url'], "1" : "www.test1.com", "2" : "www.test2.com", "3" : "www.test3.com", "4" : "www.test4.com"}, "found" : 'false' }

	#temporary template to show posted data
	#return render_template('show_data.html', data=crawlData)

	#store search in database
	test = mongo.db.test #access test collection
	postid = test.insert({'url': url, 'limit': limit, 'sType' : sType, 'keyword' : keyword, 'path' : crawlData.get('path'), 'found' : crawlData.get('found')}) 

	#get data from id
	queryData = test.find_one({'_id' : postid})

	return render_template('show_result.html', docId=postid, qData=queryData)


if __name__ == "__main__":
	app.run()

