import os
import threading
from contextlib import suppress
from urllib.parse import urlparse

from dotenv import load_dotenv
from quart import Quart, Response, request, send_file, send_from_directory
from quart_cors import cors
from util.download import (CACHE_DIR, DOWNLOAD_DIR, ZIP_DIR, start,
                           start_playlist)
from util.spotify import start_token_thread
from util.statistics import (cacheStorage, playlistStorage, songStorage,
                             totalCaches, totalPlaylists, totalSongData,
                             totalSongs, totalStorage)

app = Quart(__name__)
app = cors(app, allow_origin="*")

load_dotenv()
port = os.environ.get("port")
ip = os.environ.get("ip")


async def serve_audio(id):
    try:
        path, filename = await start(id)
        file = os.path.basename(path)
        response = Response(status=302)
        response.headers["Location"] = f"/download/track/{file}"
        # path, filename = await start(id)
        # return (
        #     await send_file(
        #         path,
        #         as_attachment=True,
        #         attachment_filename=filename,
        #     ),
        #     200,
        # )
    except:
        return {"failed": True, "message": "Song not found"}, 404


async def serve_playlist(id):
    try:
        filename = await start_playlist(id)
        response = Response(status=302)
        response.headers["Location"] = f"/download/playlist/{id}.zip"
        return response
        # return (
        #     await send_file(
        #         filename,
        #         as_attachment=True,
        #         attachment_filename=f"{id}.zip",
        #         mimetype="application/zip",
        #     ),
        #     200,
        # )
    except:
        return {"failed": True, "message": "Playlist not found"}, 404


@app.route("/action", methods=["POST"])
async def serve_action():
    form = await request.form
    link = form["link"]
    id = urlparse(link).path.split("/")[-1]
    if "/playlist/" in link:
        return await serve_playlist(id)
    if "/track/" in link:
        return await serve_audio(id)

    return await send_file("static/result.html")


@app.route("/stats")
async def serve_stats():
    return {
        "failed": False,
        "data": {
            "total": await totalCaches(),
            "songs": await totalSongs(),
            "caches": await totalSongData(),
            "playlists": await totalPlaylists(),
        },
        "storage": {
            "total": await totalStorage(),
            "songs": await songStorage(),
            "playlists": await playlistStorage(),
            "caches": await cacheStorage(),
        },
    }


@app.route("/")
async def serve_index():
    return await send_file("static/index.html")


@app.route("/<path:path>")
async def serve_static(path):
    return await send_from_directory("static", path)


@app.route("/download/playlist/<path:path>")
async def serve_playlist_download(path):
    return await send_from_directory(ZIP_DIR, path)


@app.route("/download/track/<path:path>")
async def serve_track_download(path):
    return await send_from_directory(DOWNLOAD_DIR, path)


token_thread = threading.Thread(target=start_token_thread)
token_thread.start()

if __name__ == "__main__":
    for directory in {CACHE_DIR, ZIP_DIR, DOWNLOAD_DIR}:
        with suppress(FileExistsError):
            os.mkdir(directory)

    app.run(ip, port=port)
