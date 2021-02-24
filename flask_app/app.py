from flask import Flask, request, render_template

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def rootpage():
    name = ''
    if request.method == 'POST' and 'username' in request.form:
        name = request.form.get('username')
    return render_template('index.html',
                            name=name)

def calc_bmi(weight, height):
    return round((weight/height/height)*703, 2)  

@app.route('/bmi', methods=['GET', 'POST'])
def bmipage():
    bmi = ''
    print('before the if statement')
    print(request.method)
    print('userheight' in request.form)
    print('height' in request.form)
    print(request.form.keys(), ' ', request.form.items())
    print(request.get_data())
    # if request.method == 'POST' and 'userheight' in request.form:
    if request.method == 'POST':
        print('I am in the if statement')
        height = float(request.form.get('userheight'))
        weight = float(request.form.get('userweight'))
        bmi = calc_bmi(weight, height)
    return render_template('bmi.html',
                            bmi=bmi)
                        

app.run()