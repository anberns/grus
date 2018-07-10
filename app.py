from flask import *
app = Flask(__name__)

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/submit', methods=['POST'])
def crawl():

	#webcrawler call goes here

	#temporary template to show posted data
	return render_template('show_data.html', url=request.form['url'], limit=request.form['limit'])

if __name__ == "__main__":
	app.run()

