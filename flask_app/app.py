from flask import Flask, request, render_template

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def rootpage():
    name = ''
    if request.method == 'POST' and 'username' in request.form:
        name = request.form.get('username')
    return render_template('index.html',
                            name=name)

@app.route('/', methods=['GET', 'POST'])
def bmipage():
    bmi = ''
    if request.method == 'POST' and 'userheight' in request.form:
        height = float(request.form.get('userheight'))
        weight = float(request.form.get('userweight'))
        bmi = calc_bmi(weight, height)
    return render_template('bmi.html',
                            bmi=bmi)

def calc_bmi(weight, height):
    return round((weight/height/height)*703, 2)                            

app.run()