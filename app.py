import requests
from flask import Flask, render_template, request, make_response
from twilio.rest import Client

SID = "AC652c51e939f97d17a00c3105769649d7"
KEY = "df7e3c41ef9a295051542cc50666c3ee"

app = Flask(__name__)
client = Client(SID, KEY)


@app.route('/send', methods=['POST'])
def send_msg():
    to = request.form['To']
    origin = request.form['From']
    response = requests.get('https://quota.glitch.me/random')
    text = response.json()['quoteText']
    message = client.messages.create(
        from_=origin,
        body=text,
        to=to
    )
    return str(message.error_message or 200)


@app.route('/reply', methods=['POST'])
def reply():
    to = request.form['To']
    origin = request.form['From']
    body = request.form['Body']
    resp = str(body)[::1]
    message = client.messages.create(
        from_=origin,
        body=resp,
        to=to
    )


if __name__ == "__main__":
    app.run(debug=True)
