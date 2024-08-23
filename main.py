from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Home route
@app.route('/')
def home():
    return render_template('main.html')

@app.route('/register',methods=['GET', 'POST'])
def register():
    # Insert your code to handle the entrance button click here
    return render_template('Register.html')
@app.route('/OTP', methods=['POST'])
def dialog_opened():

    return render_template()

    # Return a response that will be used in the client-side code
if __name__ == '__main__':
    app.run(debug=True)
