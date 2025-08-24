import csv
import requests
import urllib.parse
from datetime import datetime, timedelta
from io import StringIO
from math import ceil
from re import search
from werkzeug.exceptions import RequestEntityTooLarge
from flask import Flask, flash, get_flashed_messages, redirect, render_template, request, Response, session, url_for
from flask_session import Session

from helpers import refresh_token, ms_to_min, get_server_token, download_playlist
import config


app = Flask(__name__)
app.config["SECRET_KEY"] = config.SECRET_KEY
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024
Session(app)


@app.route("/")
def index():
    message = get_flashed_messages(category_filter="authorization_failed")
    message = message[0] if message else ""
    return render_template("index.html", message=message)


@app.errorhandler(404)
def not_found(e):
    return redirect("/not-found")


@app.route("/not-found")
def page_not_found():
    return render_template("404.html")


@app.route("/error")
def unexpected_error():
    return render_template("error.html")


@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(e):
    flash("File too large. Make sure .csv file is less than 8MBs", "restore_error")
    return redirect("/restore")


@app.route("/login", methods=["GET"])
def login():
    parameters = {
        "client_id": config.CLIENT_ID,
        "response_type": "code",
        "redirect_uri": config.REDIRECT_URI,
        "state": config.STATE,
        "scope": "playlist-read-private playlist-read-collaborative playlist-modify-private playlist-modify-public user-top-read user-read-recently-played user-library-modify user-library-read user-read-email user-read-private",
        "show_dialog": "true",
    }

    AUTH_URL = "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode(parameters)
    return redirect(AUTH_URL)


@app.route("/callback")
def callback():
    if "code" in request.args and request.args["state"] == config.STATE:
        headers = {
            "content-type": "application/x-www-form-urlencoded",
            "Authorization": "Basic " + config.ENCODED_STRING
        }
        parameters = {
            "grant_type": "authorization_code",
            "code": request.args["code"],
            "redirect_uri": config.REDIRECT_URI
        }

        response = requests.post(config.TOKEN_URL, headers=headers, params=parameters)
        if response.status_code != 200:
            session.clear()
            return redirect("/error")
        
        result = response.json()

        if "access_token" in result:
            session["access_token"] = result["access_token"]
            session["refresh_token"] = result["refresh_token"]
            session["expiry"] = datetime.now() + timedelta(seconds=3600)
            return redirect("/")
        else:
            flash("Authorization failed. Please login again.", "authorization_failed")
            return redirect("/")

    
    if "error" in request.args or request.args["state"] != config.STATE:
        flash("Authorization failed. Please login again.", "authorization_failed")
        return redirect("/")
    
    return redirect("/")


@app.route("/backup")
def backup():
    if "access_token" not in session:
        return render_template("backup.html", heading="To Backup your Playlists")
    
    refresh_token()
    page_number = request.args.get("page", 1, type=int)
    per_page = 50

    parameters = {
        "limit": per_page,
        "offset": (page_number - 1) * per_page
    }
    headers = {
        "Authorization": f"Bearer {session["access_token"]}"
    }
    response = requests.get(config.USER_PLAYLISTS, params=parameters, headers=headers)
    if response.status_code != 200:
        session.clear()
        return redirect("/error")
    
    response = response.json()

    total_pages = ceil(response["total"] / per_page)
    if page_number > total_pages:
        return redirect("/not-found")
    
    if page_number == 1:
        params = {
            "limit": 1,
        }
        saved_songs = requests.get(config.SAVED_SONGS, params=params, headers=headers)
        if saved_songs.status_code != 200:
                session.clear()
                return redirect("/error")
        
        saved_songs = saved_songs.json()
        return render_template("backup.html", response=response, page_number=page_number, total_pages=total_pages, saved_songs=saved_songs)


    return render_template("backup.html", response=response, page_number=page_number, total_pages=total_pages)
    

@app.route("/download")
def download():
    playlist_id = request.args.get("playlist")

    if not playlist_id:
        return redirect("/not-found")
    
    refresh_token()

    result = []
    
    parameters = {
        "market": "US",
        "limit": 50,
        "offset": 0
    }
    headers = {
        "Authorization": f"Bearer {session["access_token"]}"
    }

    if playlist_id == "saved":
        response = requests.get(config.SAVED_SONGS, params=parameters, headers=headers)
    else:
        response = requests.get(f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks", params=parameters, headers=headers)

    if response.status_code != 200:
            session.clear()
            return redirect("/error")
    
    response = response.json()
    
    result.extend(response.get("items", []))

    while (response["next"]):
        response = requests.get(response["next"], headers=headers)
        if response.status_code != 200:
            session.clear()
            return redirect("/error")
    
        response = response.json()
        result.extend(response.get("items", []))

    return download_playlist(result)
    

@app.route("/restore", methods=["GET", "POST"])
def restore():
    if request.method == "GET":
        message = get_flashed_messages(category_filter=["restore_error", "restore_success"])
        message = message[0] if message else ""
        return render_template("restore.html", heading="To restore Playlist from Backup", message=message)
    
    if "file" not in request.files:
        flash("Please provide a .csv file", "restore_error")
        return redirect("/restore")

    file = request.files["file"]

    if file.filename == '': 
        flash("No selected file", "restore_error")
        return redirect("/restore")
    
    if not file.filename.lower().endswith(".csv"):
        flash("Invalid file", "restore_error")
        return redirect("/restore")
    
    if file.mimetype not in ["text/csv", "application/vnd.ms-excel"]:
        flash("Uploaded file is not a valid CSV", "restore_error")
        return redirect("/restore")
    
    try:
        stream = StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_data = csv.DictReader(stream)
    except Exception:
        flash("Failed to read CSV file. Please make sure it's properly formatted.", "restore_error")
        return redirect("/restore")
    
    fieldnames = csv_data.fieldnames
    tracks = []
    expression = r"(?:track[/:])([A-Za-z0-9]{22})"

    if "url" in fieldnames:
        for row in csv_data:
            track_id = search(expression, row.get("url"))
            if not track_id:
                continue
            tracks.append(track_id.group(1))
    elif "spotify_id" in fieldnames:
        for row in csv_data:
            track_id = search(expression, row.get("spotify_id"))
            if not track_id:
                continue
            tracks.append(track_id.group(1))
    else:
        flash("Error. Make sure csv contains 'url' or 'spotify_id' column.", "restore_error")
        return redirect("/restore")
    
    MAX_ROWS = 1000
    if len(tracks) > MAX_ROWS:
        flash(f"CSV contains more than {MAX_ROWS} tracks. Please upload a smaller list.", "restore_error")
        return redirect("/restore")
    if not tracks:
        flash(f"CSV is empty.", "restore_error")
        return redirect("/restore") 
    
    refresh_token()

    data = {
        "name": f"Restored Playlist {datetime.now().strftime('%Y-%m-%d')}"
    }
    headers = {
        "Authorization": f"Bearer {session["access_token"]}",
        "Content-Type": "application/json"
    }

    response = requests.get("https://api.spotify.com/v1/me", headers=headers)
    if response.status_code != 200:
            session.clear()
            return redirect("/error")
    response = response.json()
    user_id = response.get("id")

    create_playlist = requests.post(f"https://api.spotify.com/v1/users/{user_id}/playlists", headers=headers, json=data)
    if create_playlist.status_code not in [200, 201]:
        session.clear()
        return redirect("/error")
    
    create_playlist = create_playlist.json()
    playlist_id = create_playlist.get("id")

    for i in range(0, len(tracks), 100):
        chunk = tracks[i:i + 100]
        uris = [f"spotify:track:{track_id}" for track_id in chunk]
        track_uris = {
            "uris": uris,
        }
        add_to_playlist = requests.post(f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks", headers=headers, json=track_uris)
        if add_to_playlist.status_code not in [200, 201]:
            flash(f"Failed to restore playlist. Please try again.", "restore_error")
            return redirect("/restore")
    
    flash(f"Playlist Restored", "restore_success")
    return redirect("/restore")


@app.route("/download-csv", methods=["GET", "POST"])
def download_csv():
    if request.method == "GET":
        message = get_flashed_messages(category_filter="download_error")
        message = message[0] if message else ""
        return render_template("download-csv.html", message=message)
    
    link = request.form.get("playlist")

    if not link:
        flash("Please Provide a Spotify Playlist link.", "download_error")
        return redirect("/download-csv")

    expression = r"(?:playlist[/:])([A-Za-z0-9]{22})"

    playlist_id = search(expression, link)

    if not playlist_id:
        flash("Invalid Spotify Playlist URL", "download_error")
        return redirect("/download-csv")
    
    playlist_id = playlist_id.group(1)

    get_server_token()

    songs = []    
    parameters = {
        "market": "US",
        "limit": 50,
        "offset": 0
    }
    headers = {
        "Authorization": f"Bearer {session['server_access_token']}"
    }

    response = requests.get(f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks", params=parameters, headers=headers)
    if response.status_code in [401, 403, 404]:
        flash("Unable to access Playlist", "download_error")
        return redirect("/download-csv")
    elif response.status_code != 200:
        flash("Invalid Spotify Playlist URL", "download_error")
        return redirect("/download-csv")
    
    response = response.json()

    songs.extend(response.get("items", []))
    while (response["next"]):
        response = requests.get(response["next"], headers=headers)
        if response.status_code != 200:
            flash("Something went wrong. Please try again.", "download_error")
            return redirect("/download-csv")
    
        response = response.json()
        songs.extend(response.get("items", []))

    return download_playlist(songs)


@app.route("/analyze-playlist")
def analyze_playlist():
    message = get_flashed_messages(category_filter="analyze_error")
    message = message[0] if message else ""

    if "access_token" not in session:   
        return render_template("analyze.html", message=message)
    
    refresh_token()

    result = []
    parameters = {
        "limit": 50,
        "offset": 0
    }
    headers = {
        "Authorization": f"Bearer {session["access_token"]}"
    }
    response = requests.get(config.USER_PLAYLISTS, params=parameters, headers=headers)
    if response.status_code != 200:
            session.clear()
            return redirect("/error")
    
    response = response.json()
    result.extend(response.get("items", []))

    while (response["next"]):
        response = requests.get(response["next"], headers=headers)
        if response.status_code != 200:
            session.clear()
            return redirect("/error")
    
        response = response.json()
        result.extend(response.get("items", []))
    
    return render_template("analyze.html", playlists=result, message=message)


@app.route("/analyzed")
def analyzed():

    link = request.args.get("playlist")

    if not link:
         return redirect("/analyze-playlist")

    expression = r"(?:playlist[/:])([A-Za-z0-9]{22})"

    playlist_id = search(expression, link)

    if not playlist_id:
        flash("Invalid Spotify Playlist URL", "analyze_error")
        return redirect("/analyze-playlist")
    
    playlist_id = playlist_id.group(1)

    get_server_token()

    songs = []    
    parameters = {
        "market": "US",
        "limit": 50,
        "offset": 0
    }
    headers = {
        "Authorization": f"Bearer {session['server_access_token']}"
    }

    playlist_details = requests.get(f"https://api.spotify.com/v1/playlists/{playlist_id}", params={"market": "US"}, headers=headers)
    if playlist_details.status_code in [401, 403, 404]:
        flash("Unable to access Playlist", "analyze_error")
        return redirect("/analyze-playlist")
    if playlist_details.status_code != 200:
        flash("Invalid Spotify Playlist URL", "analyze_error")
        return redirect("/analyze-playlist")
    
    playlist_details = playlist_details.json()
    playlist_cover = playlist_details["images"][0].get("url")
    playlist_title = playlist_details.get("name")

    response = requests.get(f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks", params=parameters, headers=headers)

    if response.status_code in [401, 403, 404]:
        flash("Unable to access Playlist", "analyze_error")
        return redirect("/analyze-playlist")
    elif response.status_code != 200:
        flash("Invalid Spotify Playlist URL", "analyze_error")
        return redirect("/analyze-playlist")
    
    response = response.json()

    total_songs = response["total"]
    if total_songs < 10:
        flash("Playlist too short. Consider adding more songs.", "analyze_error")
        return redirect("/analyze-playlist")
    elif total_songs > 1000:
        flash("Maximum length of Playlist allowed is 1000 tracks", "analyze_error")
        return redirect("/analyze-playlist")
    
    songs.extend(response.get("items", []))

    while (response["next"]):
        response = requests.get(response["next"], headers=headers)
        if response.status_code != 200:
            flash("Something went wrong. Please try again.", "analyze_error")
            return redirect("/analyze-playlist")
    
        response = response.json()
        songs.extend(response.get("items", []))

    year_rex = r"([0-9]{4})"
    decades = {}
    artists = {}
    popularity = []
    
    for song in songs:
        year = search(year_rex, song["track"]["album"].get("release_date"))
        if year:
            year = year.group(1)
            decade = year[:3] + "0s"
            if decade not in decades:
                decades[decade] = 1
            else:
                decades[decade] += 1
        
        artist = song["track"].get("artists")
        if artist:
            artist = artist[0]["id"]
            if artist not in artists:
                artists[artist] = 1
            else:
                artists[artist] += 1

        track_popularity = song["track"].get("popularity")
        if track_popularity is not None:
            popularity.append(track_popularity)


    decades = sorted(decades.items(), key=lambda x: x[1], reverse=True)
    if len(decades) > 5:
        decades = decades[:5]

    top_artists = sorted(artists.items(), key=lambda x: x[1], reverse=True)
    if len(top_artists) > 5:
        top_artists = top_artists[:5]

    artist_ids = [i[0] for i in top_artists]
    artist_ids = ",".join(artist_ids)

    artist_data = requests.get(f"https://api.spotify.com/v1/artists?ids={artist_ids}", headers=headers)
    if artist_data.status_code != 200:
            session.clear()
            return redirect("/error")
    artist_data = artist_data.json()
    artist_data = artist_data.get("artists", [])

    popularity = round(sum(popularity) / len(popularity))

    return render_template("analyzed.html", playlist_cover=playlist_cover, playlist_title=playlist_title, artist_data=artist_data, decades=decades, popularity=popularity)