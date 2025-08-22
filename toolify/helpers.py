import requests
from datetime import datetime, timedelta
from flask import session, redirect, flash

import config

def refresh_token():
    if "expiry" in session and datetime.now() > session["expiry"]:
        headers = {
            "content-type": "application/x-www-form-urlencoded",
            "Authorization": "Basic " + config.ENCODED_STRING
        }
        parameters = {
            "grant_type": "refresh_token",
            "refresh_token": session["refresh_token"],
            "client_id": config.CLIENT_ID
        }

        response = requests.post(config.TOKEN_URL, headers=headers, params=parameters)
        result = response.json()

        if "access_token" in result:
            session["access_token"] = result["access_token"]
            if "refresh_token" in result:
                session["refresh_token"] = result["refresh_token"]
            session["expiry"] = datetime.now() + timedelta(seconds=3600)
            return
        else:
            session.clear()
            flash("Authorization failed. Please login again.", "authorization_failed")
            return redirect("/")
        
def ms_to_min(ms):
    if not ms:
        return ""
    
    sec = ms // 1000
    minutes = sec // 60
    seconds = sec % 60
    return f"{minutes:02d}:{seconds:02d}"

def get_server_token():
    if "server_access_token" not in session or datetime.now() > session["server_expiry"]:
        headers = {
            "content-type": "application/x-www-form-urlencoded",
            "Authorization": "Basic " + config.ENCODED_STRING
        }
        parameters = {
            "grant_type": "client_credentials",
        }

        response = requests.post(config.TOKEN_URL, headers=headers, params=parameters)
        result=response.json()

        if not response.status_code == 200:
            return redirect("/error")
        
        session["server_access_token"] = result["access_token"]
        session["server_expiry"] = datetime.now() + timedelta(seconds=3600)
        return