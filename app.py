import itertools
import os
import re

import redis
import requests
from flask import Flask, request, Response
from ibm_cloud_sdk_core.api_exception import ApiException
from ibm_watson import LanguageTranslatorV3
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

account_sid = 'AC303b7c28a90cf7c6f1ca8790153172ba'
auth_token = '6addf5d752a9b2049988dc3260045da2'
client = Client(account_sid, auth_token)

WATSON_KEY = "SWI2s_r2roYSV_1MontL6a7HxG7zDgodwHeZKs0vDTfF"
WATSON_URL = "https://gateway.watsonplatform.net/language-translator/api"
#db = redis.from_url(os.environ.get("REDIS_URL"))  # Heroku DB
db = redis.Redis(password="castro03") #Local DB
app = Flask(__name__)

language_translator = LanguageTranslatorV3(
    version='2018-05-01',
    iam_apikey=WATSON_KEY,
    url=WATSON_URL
)


def case_combinations(input_str):
    return map(''.join, itertools.product(*((c.upper(), c.lower()) for c in input_str)))


@app.route('/send', methods=['POST'])
def send_msg():
    origin = request.form["From"]
    to = request.form["To"]
    response = requests.get('https://quota.glitch.me/random')
    text = response.json()['quoteText']
    message = client.messages.create(
        from_=origin,
        body=text,
        to=to,
    )
    return message.error_message or 200


def set_mode(text, origin, to):
    translate = case_combinations("translate")
    chatbot = case_combinations("chatbot")
    if text in translate:
        db.set("{}:mode".format(origin), "translate")
        resp = str(ask(to, origin, mode="translate_model", question="Pick a translation model: \nFormat: (en-es)"))
    elif text in chatbot:
        db.set("{}:mode".format(origin), "chatbot")
        resp = "You are in Chatbot Mode"
    else:
        resp = "Mode is not supported\nSupported Modes are: 1. translate\n2. chatbot"
    return resp


def set_model(text, origin):
    if text and text in list_models():
        db.set("{}:dialect".format(origin), text)
        resp = "You are in translate mode"
    elif text not in list_models():
        resp = "Unsupported Language Model"
    else:
        resp = "Error. try again with the Format: (en-es)"
    return resp


def translate(body, origin):
    if body is None:
        resp = ""
    model = db.get("{}:dialect".format(origin)).decode("utf-8") or "en-es"
    try:
        translation = language_translator.translate(
            text=body,
            model_id=model).get_result()
        resp = translation["translations"][0]["translation"]
    except ApiException as e:
        resp = e.message
    return resp


def chat():
    resp = "You are in chatbot mode"
    return resp


@app.route('/reply', methods=['POST'])
def reply():
    to = request.form['To']
    origin = request.form['From']
    body = str(request.form['Body'])
    resp = ""
    change_mode = re.search(r'^mode: ', body, re.IGNORECASE)
    choose_model = re.search(r'\(.*?\)', body, re.IGNORECASE)
    if change_mode:
        word = change_mode.group()
        text = body.replace(word, "").strip()
        resp = set_mode(text, origin, to)
    elif choose_model:
        text = choose_model.group()[1:-1]
        resp = set_model(text, origin)
    elif body.lower() == "list models" or body.lower() == "lm":
        resp = str(list_models())
    else:
        # Default response
        mode = db.get("{}:mode".format(origin)).decode("utf-8")
        if mode in "translate" or mode in " translate":
            resp = translate(body, origin)
        elif mode == "chatbot":
            resp = chat()
        else:
            resp = "Please set mode again."
    response = MessagingResponse()
    response.message(resp)
    return str(response)
    """
    message = client.messages.create(
        from_=to,
        body=resp,
        to=origin
    )
    return message.error_message or resp
    """


@app.errorhandler(400)
def client_error(error):
    return str(error)


@app.errorhandler(500)
def internal_error(error):
    return str(error)


@app.errorhandler(404)
def not_found_error(error):
    return str(error)


def list_models():
    models = language_translator.list_models().get_result()["models"]
    model_list = []
    for model in models:
        model_list.append(model["model_id"])
    return model_list


def ask(to, origin, mode, question="None"):
    msg = question
    if mode == "translate_model":
        models = list_models()
        for dialect in models:
            msg += "\n({})".format(dialect)
    return msg


if __name__ == "__main__":
    app.run(debug=True)
