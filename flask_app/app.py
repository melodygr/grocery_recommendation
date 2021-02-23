from flask import Flask, request, render_template

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def rootpage():
    name = ''
    if request.method == 'POST' and 'username' in request.form:
        name = request.form.get('username')
    return render_template('index.html',
                            name=name)

@app.route('/bmi', methods=['GET', 'POST'])
def bmipage():
    height = 0
    weight = 0
    bmi = 0
    if request.method == 'POST' and 'userheight' in request.form:
        height = request.form.get('userheight')
        weight = request.form.get('userweight')
        bmi = (weight/height/height)*703
    return render_template('bmi.html',
                            bmi=bmi)

app.run()