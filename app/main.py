from flask import Flask, send_from_directory, jsonify, request, Response
import subprocess
import os
import zipfile
import io
import uuid
import shutil
import threading
import time

app = Flask(__name__, static_folder='web')
BASE_DOWNLOAD_FOLDER = '/app/downloads'

# Ensure the base downloads directory exists
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

    # Generate a unique folder for this session using UUID
    session_id = str(uuid.uuid4())
    session_download_folder = os.path.join(BASE_DOWNLOAD_FOLDER, session_id)
    os.makedirs(session_download_folder, exist_ok=True)

    # Determine downloader based on link
    if "spotify" in spotify_link:
        command = ['spotdl', spotify_link, '--output', session_download_folder]
    elif "youtube" in spotify_link or "youtu.be" in spotify_link:
        command = ['yt-dlp', '-x', '--audio-format', 'mp3', '-o', f"{session_download_folder}/%(title)s.%(ext)s", spotify_link]
    else:
        return jsonify({"status": "error", "output": "Invalid link type. Only Spotify and YouTube links are supported."}), 400

    def generate():
        try:
            # Run the selected downloader with real-time output
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )

            # Stream each line of output to the client
            for line in process.stdout:
                yield f"data: {line.strip()}\n\n"

            process.stdout.close()
            process.wait()  # Wait for the process to complete

            if process.returncode == 0:
                # After completion, find the latest file(s)
                downloaded_files = os.listdir(session_download_folder)
                
                if len(downloaded_files) > 1:
                    # If multiple files, create a zip file
                    zip_filename = "playlist.zip"
                    zip_path = os.path.join(session_download_folder, zip_filename)
                    with zipfile.ZipFile(zip_path, 'w') as zipf:
                        for file in downloaded_files:
                            file_path = os.path.join(session_download_folder, file)
                            zipf.write(file_path, arcname=file)
                    yield f"data: DOWNLOAD: {session_id}/{zip_filename}\n\n"
                elif downloaded_files:
                    # If only one file, just send its filename
                    yield f"data: DOWNLOAD: {session_id}/{downloaded_files[0]}\n\n"
                else:
                    yield f"data: Error: No files downloaded.\n\n"
                
                # Start a thread to delete the folder after a delay
                threading.Thread(target=delayed_delete, args=(session_download_folder,)).start()

            else:
                yield f"data: Error: Download exited with code {process.returncode}.\n\n"

        except Exception as e:
            yield f"data: Error: {str(e)}\n\n"

    return Response(generate(), mimetype='text/event-stream')

def delayed_delete(folder_path):
    # Wait for 5 minutes (300 seconds) before deleting
    time.sleep(300)
    shutil.rmtree(folder_path, ignore_errors=True)

@app.route('/downloads/<session_id>/<filename>')
def serve_download(session_id, filename):
    session_download_folder = os.path.join(BASE_DOWNLOAD_FOLDER, session_id)
    return send_from_directory(session_download_folder, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

