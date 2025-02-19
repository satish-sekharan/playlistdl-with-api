from flask import Flask, send_from_directory, jsonify, request, Response
import subprocess
import os
import zipfile
import uuid
import shutil
import threading
import time
import re  # Pour capturer le nom de l'album ou de la playlist

app = Flask(__name__, static_folder='web')
BASE_DOWNLOAD_FOLDER = '/app/downloads'
AUDIO_DOWNLOAD_PATH = os.getenv('AUDIO_DOWNLOAD_PATH', BASE_DOWNLOAD_FOLDER)
# Les variables d'authentification ne sont plus utilisées
# ADMIN_USERNAME = os.getenv('ADMIN_USERNAME')
# ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')

# On ne gère plus de sessions login, on simule toujours l'utilisateur connecté (admin)
sessions = {}

os.makedirs(BASE_DOWNLOAD_FOLDER, exist_ok=True)

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

@app.route('/download')
def download_media():
    spotify_link = request.args.get('spotify_link')
    if not spotify_link:
        return jsonify({"status": "error", "output": "No link provided"}), 400


    download_folder = os.path.join(AUDIO_DOWNLOAD_PATH)
    os.makedirs(AUDIO_DOWNLOAD_PATH, exist_ok=True)

    # Définir la commande en fonction du type de lien
    if "spotify" in spotify_link:
        command = [
            'spotdl',
            '--output', f"{download_folder}/{{track-number}} - {{artist}} - {{title}}.{{output-ext}}",
            spotify_link
        ]
    else:
        command = [
            'yt-dlp', '-x', '--audio-format', 'mp3',
            '-o', f"{download_folder}/%(track_number)s - %(uploader)s - %(title)s.%(ext)s",
            spotify_link
        ]

    # Toujours admin, donc is_admin est True
    is_admin = True
    return Response(generate(is_admin, command, download_folder), mimetype='text/event-stream')

def generate(is_admin, command, download_folder):
    album_name = None  # Pour récupérer le nom de l'album ou de la playlist
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        for line in process.stdout:
            yield f"data: {line.strip()}\n\n"

            # Recherche du nom d'album/playlist dans la sortie de spotdl
            match = re.search(r'Found \d+ songs in (.+?) \(', line)
            if match:
                album_name = match.group(1).strip()
            
        process.stdout.close()
        process.wait()

        if process.returncode == 0:
            downloaded_files = os.listdir(download_folder)

            # Pour admin, on ne fait pas de zip, ni de suppression automatique
            yield "data: Download completed. Files saved to server directory.\n\n"
        else:
            yield f"data: Error: Download exited with code {process.returncode}.\n\n"

    except Exception as e:
        yield f"data: Error: {str(e)}\n\n"

@app.route('/downloads/<session_id>/<filename>')
def serve_download(session_id, filename):
    session_download_folder = os.path.join(BASE_DOWNLOAD_FOLDER, session_id)
    return send_from_directory(session_download_folder, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)