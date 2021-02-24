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
    bmi = ''
    print('before the if statement')
    print(request.method)
    print('userweight' in request.form)
    # if request.method == 'POST' and 'userheight' in request.form:
    if request.method == 'POST':
        print('I am in the if statement')
        height = float(request.form.get('userheight'))
        weight = float(request.form.get('userweight'))
        bmi = calc_bmi(weight, height)
    return render_template('bmi.html',
                            bmi=bmi)

def calc_bmi(weight, height):
    return round((weight/height/height)*703, 2)                            

app.run()