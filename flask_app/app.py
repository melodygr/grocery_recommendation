from flask import Flask, request, render_template

app = Flask(__name__)

@app.route('/')
def rootpage():
    name = ''
    if request.method == 'POST' and 'username' in request.form:
        name = request.form.get('username')
    return render_template('index.html',
                            name=name)

app.run()