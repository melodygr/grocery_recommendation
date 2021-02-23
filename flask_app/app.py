from flask import Flask, request, render_template

app = Flask(__name__)

@app.route('/')
def welcome():
    return render_template('index.html')

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