from flask import *
app = Flask(__name__)

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/submit', methods=['POST'])
def crawl():
	#function to route data to webcrawler
	return 1

if __name__ == "__main__":
	app.run()

