import os
import requests
import urllib.parse
from flask import Flask, render_template, redirect, request, session
from flask_session import Session

import helpers

from dotenv import load_dotenv
load_dotenv()

redirect_uri = os.getenv("REDIRECT_URI")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False 
Session(app)


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET"])
def login():
    parameters = {
        "client_id": os.getenv("CLIENT_ID"),
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "state": os.getenv("SPOTIFY_STATE"),
        "show_dialog": "true",
    }

    authorization_url = "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode(parameters)
    return redirect(authorization_url)

@app.route("/callback")
def callback():
    render_template("index.html", message="Login successful! You can now use Toolify with your Spotify account.")