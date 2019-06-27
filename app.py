import requests

import re
from flask import Flask, render_template, request, make_response
from twilio.rest import Client
from ibm_watson import LanguageTranslatorV3

TWILIO_SID = "AC652c51e939f97d17a00c3105769649d7"
TWILIO_KEY = "df7e3c41ef9a295051542cc50666c3ee"
WATSON_KEY = "SWI2s_r2roYSV_1MontL6a7HxG7zDgodwHeZKs0vDTfF"
WATSON_URL = "https://gateway.watsonplatform.net/language-translator/api"

app = Flask(__name__)
client = Client(TWILIO_SID, TWILIO_KEY)
language_translator = LanguageTranslatorV3(
    version='2018-05-01',
    iam_apikey=WATSON_KEY,
    url=WATSON_URL
)


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
    body = str(request.form['Body'])
    resp = ""
    check = re.search('^translate:\s', body, re.IGNORECASE)
    if check:
        word = check.group()
        body = body.replace(word, '')
        model = re.search('\(.*?\)', body).group()
        text = body.replace(model, '').strip()
        diagnostic = "Body: {0}, Model: {1}".format(text,model)
        translation = language_translator.translate(
            text=text,
            model_id=model[1:-1]).get_result()
        resp = str(translation)

    else:
        resp = str(body)[::-1]
    """
    message = client.messages.create(
        from_=to,
        body=resp,
        to=origin
    )
    """
    return resp


if __name__ == "__main__":
    app.run(debug=True)
