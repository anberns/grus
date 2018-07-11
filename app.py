from flask import *
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

	#webcrawler call goes here

	#temporary template to show posted data
	return render_template('show_data.html', url=request.form['url'], limit=request.form['limit'])

#temp route to test db
@app.route('/testdb', methods=['GET', 'POST'])
def testdb():

	if request.method == 'POST':
		test = mongo.db.test #access test collection
		url = request.form['testurl']
		limit = request.form['testlimit']
		postid = test.insert({'url': url, 'limit': limit}) #store result
		return render_template('show_result.html', result=postid)

	else:
		return render_template('testdb.html')



if __name__ == "__main__":
	app.run()

