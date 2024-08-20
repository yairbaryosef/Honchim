from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Home route
@app.route('/')
def home():
    return render_template('main.html')



if __name__ == '__main__':
    app.run(debug=True)
