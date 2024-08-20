from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Home route
@app.route('/')
def home():
    return "hello world yair"



if __name__ == '__main__':
    app.run(debug=True)
