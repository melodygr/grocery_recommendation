from Flask import Flask

app = Flask(__name__)

@app.route('/')
def welcome():
    return 'This is my first Flask app! Yay!'


app.run()