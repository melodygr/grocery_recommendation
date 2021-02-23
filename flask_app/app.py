from flask import Flask, request

app = Flask(__name__)

@app.route('/')
def welcome():
    return 'This is my first Flask app! Yay!'

@app.route('/bob')
def bobpage():
    return 'Yo BOB!'

@app.route('/method', methods=['GET', 'POST'])
def method():
    if request.method == 'POST':
        return "You've used a POST request!"
    else:
        return "I reckon using a GET request!"    


app.run()