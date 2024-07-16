from dotenv import load_dotenv
import os
import base64
from requests import post, get
import json
import youtube_dl
from pydub import AudioSegment

load_dotenv()

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

def get_token():
    auth_string = client_id + ":" + client_secret
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    result = post(url, headers=headers, data=data)
    json_result = json.loads(result.content)
    token = json_result["access_token"]
    return token


def get_auth_header(token):
    return {"Authorization": "Bearer " + token}


def get_user_playlists(token, user_id):
    url = f"https://api.spotify.com/v1/users/{user_id}/playlists"
    headers = get_auth_header(token)
    playlists = []
    params = {
        "limit": 50
    }
    while url:
        result = get(url, headers=headers, params=params)
        if result.status_code !=200:
            return None
        json_result = json.loads(result.content)
        playlists.extend(json_result["items"])
        url = json_result.get("next")
        if url:
            params = {}

    return playlists

def get_playlist_details(token, playlist_id):
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}"
    headers = get_auth_header(token)
    result = get(url, headers=headers)
    if result.status_code != 200:
        print(f"Error: {result.status_code}, {result.reason}")
        return None
    return json.loads(result.content)

def download_and_convert_to_mp3(track_name):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmp1':'%(title)s.%(ext)s'
    }
    
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([f"ytsearch:{track_name}"])
        except Exception as e:
            print(f"Failed to download {track_name}: {e}")

token = get_token()
user_id = input("What is your user id? ")
playlists = get_user_playlists(token, user_id)

if playlists is None:
    print ("No user found with this ID has been found.")
elif len(playlists) == 0:
    print("This user does not have any playlists.")
else:
    for idx, playlist in enumerate(playlists):
        print(f"{idx + 1}. {playlist['name']} - ({playlist['owner']['display_name']})")

    try:
        choice = int(input("Enter the number of the playlist you would like to view the details for: ")) - 1
        if 0 <= choice < len(playlists):
            selected_playlist = playlists[choice]
            playlist_id = selected_playlist["id"]
            playlist_details = get_playlist_details(token, playlist_id)
            if playlist_details:
                tracks = playlist_details['tracks']['items']
                for track in tracks:
                    track_name = track['track']['name']
                    print(f"Downloading {track_name}...")
                    download_and_convert_to_mp3(track_name)
                    print(f"Downloaded and converted {track_name} to MP3.")
        else:
            print("Invalid choice.")
    except ValueError:
        print ("Invalid input. Please enter a valid number:")