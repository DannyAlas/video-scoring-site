import datetime
import json
import logging
import os
import sys
from typing import BinaryIO

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, Request, status
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import (HTMLResponse, JSONResponse, RedirectResponse,
                               StreamingResponse)
from fastapi.staticfiles import StaticFiles
from firebase_admin import auth, credentials, initialize_app, storage
from google.cloud import firestore

load_dotenv()
CHUNK_SIZE = 1024 * 1024
VIDEOS_DIR = r"D:\Media\onedrive\UCB-O365\Rootlab - Shock\mp4s"
logging.basicConfig(
    level=logging.WARNING, format="%(asctime)s - %(levelname)s: %(message)s"
)

log = logging.getLogger(__name__)


def exception_handler(exeption_type, exception, traceback):
    # set the message to me the last lines of the traceback
    log.error(
        f"Uncaught exception: {exception}",
        exc_info=(exeption_type, exception, traceback),
    )


sys.excepthook = exception_handler

env_creds = {
    "type": os.getenv("TYPE"),
    "project_id": os.getenv("PROJECT_ID"),
    "private_key_id": os.getenv("PRIVATE_KEY_ID"),
    "private_key": os.getenv("PRIVATE_KEY").replace("\\n", "\n"),
    "client_email": os.getenv("CLIENT_EMAIL"),
    "client_id": os.getenv("CLIENT_ID"),
    "auth_uri": os.getenv("AUTH_URI"),
    "token_uri": os.getenv("TOKEN_URI"),
    "auth_provider_x509_cert_url": os.getenv("AUTH_PROVIDER_X509_CERT_URL"),
    "client_x509_cert_url": os.getenv("CLIENT_X509_CERT_URL"),
}

cred = credentials.Certificate(env_creds)
firebase = initialize_app(cred)
db = firestore.Client.from_service_account_info(env_creds)
bucket = storage.bucket(name=os.getenv("STORAGEBUCKET"))
app = FastAPI()
backgound_tasks = BackgroundTasks()
allow_all = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_all,
    allow_credentials=True,
    allow_methods=allow_all,
    allow_headers=allow_all,
)
app.mount("/public", StaticFiles(directory="./src/public"), name="public")

#redirect to /
@app.get("/home")
async def home(request: Request):
    return RedirectResponse(url="/", status_code=302)

# on the root endpoint, return the ui if there is nothing after the slash
@app.get("/")
async def root(request: Request):
    log.info(f"ui request {request.headers}")
    # return static html file
    return HTMLResponse(content=open("./src/static/index.html", "r").read())


@app.get("/all", include_in_schema=False)
async def root(request: Request):
    log.info(f"all ui request {request.headers}")
    # return static html file
    return HTMLResponse(content=open("./src/static/all.html", "r").read())

@app.get("/login", include_in_schema=False)
async def login(request: Request):
    log.info(f"login ui request {request.headers}")
    cookie = request.cookies.get("session")
    if cookie is not None:
        try:
            auth.verify_session_cookie(cookie, check_revoked=True)
            return RedirectResponse(url="/")
        except:
            pass
    return HTMLResponse(content=open("./src/static/login.html", "r").read())

@app.post("/api/login", include_in_schema=False)
async def login(request: Request):
    # log.info(f"login request {request.headers}")
    user = await request.json()
    try:
        # if the users email is not a company email, return an error
        if not str(user["email"]).endswith("colorado.edu"):
            return JSONResponse(
                content={"message": "You must use a colorado.edu email"}, status_code=400
            )

        # create session cookie
        cookie = auth.create_session_cookie(
            id_token=user["stsTokenManager"]["accessToken"],
            expires_in=datetime.timedelta(days=5),
        )
        # check if user exists in database
        if not db.collection("users").document(user["uid"]).get().exists:
            db.collection("users").document(user["uid"]).set(
                {
                    "email": user["email"],
                    "displayName": user["displayName"],
                    "keybindings": [
                        {
                            "key": {
                                "key": " ",
                                "keyCode": 32,
                                "which": 32,
                                "code": "Space",
                                "location": 0,
                                "altKey": False,
                                "ctrlKey": False,
                                "metaKey": False,
                                "shiftKey": False,
                                "repeat": False,
                            },
                            "action": "Play/pause video",
                        },
                        {
                            "key": {
                                "key": "z",
                                "keyCode": 90,
                                "which": 90,
                                "code": "KeyZ",
                                "location": 0,
                                "altKey": False,
                                "ctrlKey": True,
                                "metaKey": False,
                                "shiftKey": False,
                                "repeat": False,
                            },
                            "action": "Undo last timestamp",
                        },
                        {
                            "key": {
                                "key": "ArrowLeft",
                                "keyCode": 37,
                                "which": 37,
                                "code": "ArrowLeft",
                                "location": 0,
                                "altKey": False,
                                "ctrlKey": False,
                                "metaKey": False,
                                "shiftKey": False,
                                "repeat": False,
                            },
                            "action": "Move video back one frame",
                        },
                        {
                            "key": {
                                "key": "ArrowRight",
                                "keyCode": 39,
                                "which": 39,
                                "code": "ArrowRight",
                                "location": 0,
                                "altKey": False,
                                "ctrlKey": False,
                                "metaKey": False,
                                "shiftKey": False,
                                "repeat": False,
                            },
                            "action": "Move video forward one frame",
                        },
                        {
                            "key": {
                                "key": "ArrowRight",
                                "keyCode": 39,
                                "which": 39,
                                "code": "ArrowRight",
                                "location": 0,
                                "altKey": False,
                                "ctrlKey": False,
                                "metaKey": False,
                                "shiftKey": False,
                                "repeat": False,
                            },
                            "action": "Move video back one second",
                        },
                        {
                            "key": {
                                "key": "ArrowRight",
                                "keyCode": 39,
                                "which": 39,
                                "code": "ArrowRight",
                                "location": 0,
                                "altKey": False,
                                "ctrlKey": False,
                                "metaKey": False,
                                "shiftKey": True,
                                "repeat": False,
                            },
                            "action": "Move video forward one second",
                        },
                        {
                            "key": {
                                "key": "ArrowDown",
                                "keyCode": 40,
                                "which": 40,
                                "code": "ArrowDown",
                                "location": 0,
                                "altKey": False,
                                "ctrlKey": False,
                                "metaKey": False,
                                "shiftKey": False,
                                "repeat": False,
                            },
                            "action": "Move video back one minute",
                        },
                        {
                            "key": {
                                "key": "ArrowUp",
                                "keyCode": 38,
                                "which": 38,
                                "code": "ArrowUp",
                                "location": 0,
                                "altKey": False,
                                "ctrlKey": False,
                                "metaKey": False,
                                "shiftKey": False,
                                "repeat": False,
                            },
                            "action": "Move video forward one minute",
                        },
                        {
                            "key": {
                                "key": "s",
                                "keyCode": 83,
                                "which": 83,
                                "code": "KeyS",
                                "location": 0,
                                "altKey": False,
                                "ctrlKey": False,
                                "metaKey": False,
                                "shiftKey": False,
                                "repeat": False,
                            },
                            "action": "Add timestamp",
                        },
                        {
                            "key": {
                                "key": "s",
                                "keyCode": 83,
                                "which": 83,
                                "code": "KeyS",
                                "location": 0,
                                "altKey": False,
                                "ctrlKey": True,
                                "metaKey": False,
                                "shiftKey": False,
                                "repeat": False,
                            },
                            "action": "Save timestamps",
                        },
                        {
                            "key": {
                                "key": "d",
                                "keyCode": 68,
                                "which": 68,
                                "code": "KeyD",
                                "location": 0,
                                "altKey": False,
                                "ctrlKey": False,
                                "metaKey": False,
                                "shiftKey": True,
                                "repeat": False,
                            },
                            "action": "Delete timestamp",
                        },
                        {
                            "key": {
                                "key": "R",
                                "keyCode": 82,
                                "which": 82,
                                "code": "KeyR",
                                "location": 0,
                                "altKey": False,
                                "ctrlKey": False,
                                "metaKey": False,
                                "shiftKey": True,
                                "repeat": False,
                            },
                            "action": "Reload timestamps",
                        },
                        {
                            "key": {
                                "key": "E",
                                "keyCode": 69,
                                "which": 69,
                                "code": "KeyE",
                                "location": 0,
                                "altKey": False,
                                "ctrlKey": False,
                                "metaKey": False,
                                "shiftKey": True,
                                "repeat": False,
                            },
                            "action": "Export timestamps",
                        },
                        {
                            "key": {
                                "key": "H",
                                "keyCode": 72,
                                "which": 72,
                                "code": "KeyH",
                                "location": 0,
                                "altKey": False,
                                "ctrlKey": False,
                                "metaKey": False,
                                "shiftKey": True,
                                "repeat": False,
                            },
                            "action": "Show/hide keybindings",
                        },
                    ],
                }
            )
        # return session cookie
        response = JSONResponse(
            content={"message": "Successfully logged in"}, status_code=200
        )
        response.set_cookie(key="session", value=cookie)
        return response
    except Exception as e:
        log.warning(f"login attempt failed: {e}")
        return HTTPException(
            detail={"message": "There was an error logging in"}, status_code=400
        )


@app.get("/logout", include_in_schema=False)
async def logout(request: Request):
    log.info(f"logout request {request.headers}")
    cookie = request.cookies.get("session")
    if cookie is not None:
        try:
            auth.verify_session_cookie(cookie, check_revoked=True)
            response = JSONResponse(
                content={"message": "Successfully logged out"}, status_code=200
            )
            response.delete_cookie(key="session")
            return RedirectResponse(url="/", status_code=302)
        except:
            pass
    return RedirectResponse(url="/")


@app.get("/api/user", include_in_schema=False)
async def user(request: Request):
    """
    Returns the user object for the current user
    """
    # log.info(f"user request {request.headers}")
    cookie = request.cookies.get("session")
    if cookie is not None:
        try:
            decoded_claims = auth.verify_session_cookie(cookie, check_revoked=True)
            user = auth.get_user(decoded_claims["user_id"])
            return JSONResponse(
                content=json.loads(json.dumps(user._data)), status_code=200
            )
        except:
            pass
    return JSONResponse(content={}, status_code=401)


@app.get("/api/videos", include_in_schema=False)
async def videos(request: Request):
    """
    Returns the videos for the current user
    """
    # log.info(f"videos request {request.headers}")
    cookie = request.cookies.get("session")
    if cookie is not None:
        try:
            decoded_claims = auth.verify_session_cookie(cookie, check_revoked=True)
            user = auth.get_user(decoded_claims["user_id"])
            videos = []
            for video in db.collection("videos").stream():
                d = video.to_dict()
                d["id"] = video.id
                videos.append(d)
            return JSONResponse(content=videos, status_code=200)
        except:
            pass
    return JSONResponse(content={}, status_code=401)


@app.get("/api/video/{video_id}", include_in_schema=False)
async def video(request: Request, video_id: str):
    """
    Returns the video for the current user
    """
    # log.info(f"video request {request.headers}")
    cookie = request.cookies.get("session")
    if cookie is not None:
        try:
            decoded_claims = auth.verify_session_cookie(cookie, check_revoked=True)
            user = auth.get_user(decoded_claims["user_id"])
        except:
            return JSONResponse(content={}, status_code=401)

        try:
            # check if video exists in the database
            video = db.collection("videos").document(video_id).get()
            if video.exists:
                d = video.to_dict()
                d["id"] = video.id
                return JSONResponse(content=d, status_code=200)
            else:
                return JSONResponse(content={}, status_code=404)
        except:
            JSONResponse(content={}, status_code=500)


@app.post("/api/video/{video_id}", include_in_schema=False)
async def video(request: Request, video_id: str):
    """
    Returns the video for the current user
    """
    # log.info(f"video request {request.headers}")
    cookie = request.cookies.get("session")
    if cookie is not None:
        try:
            decoded_claims = auth.verify_session_cookie(cookie, check_revoked=True)
            user = auth.get_user(decoded_claims["user_id"])
        except:
            return JSONResponse(content={}, status_code=401)

        try:
            request_data = await request.json()
            # regardless of whether the video exists, update the video
            # check if video exists in the database
            video = db.collection("videos").document(video_id).get()
            if video.exists:
                db.collection("videos").document(video_id).update(request_data)
                return JSONResponse(content={}, status_code=200)
            else:
                return JSONResponse(content={}, status_code=404)
        except:
            JSONResponse(content={}, status_code=500)


####### video streaming code ########
def send_bytes_range_requests(
    file_obj: BinaryIO, start: int, end: int, chunk_size: int = 10_000
):
    """Send a file in chunks using Range Requests specification RFC7233

    `start` and `end` parameters are inclusive due to specification
    """
    with file_obj as f:
        f.seek(start)
        while (pos := f.tell()) <= end:
            read_size = min(chunk_size, end + 1 - pos)
            yield f.read(read_size)


def _get_range_header(range_header: str, file_size: int) -> tuple[int, int]:
    def _invalid_range():
        return HTTPException(
            status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE,
            detail=f"Invalid request range (Range:{range_header!r})",
        )

    try:
        h = range_header.replace("bytes=", "").split("-")
        start = int(h[0]) if h[0] != "" else 0
        end = int(h[1]) if h[1] != "" else file_size - 1
    except ValueError:
        raise _invalid_range()

    if start > end or start < 0 or end > file_size - 1:
        raise _invalid_range()
    return start, end


@app.get("/video/{video_id}", include_in_schema=False)
def range_requests_response(request: Request):
    """Returns StreamingResponse using Range Requests of a given file"""
    file_path = os.path.join(VIDEOS_DIR, request.path_params["video_id"])
    if not os.path.exists(file_path):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="File not found")
    file_size = os.stat(file_path).st_size
    range_header = request.headers.get("range")
    headers = {
        "content-type": "video/mp4",
        "accept-ranges": "bytes",
        "content-encoding": "identity",
        "content-length": str(file_size),
        "access-control-expose-headers": (
            "content-type, accept-ranges, content-length, "
            "content-range, content-encoding"
        ),
    }
    start = 0
    end = file_size - 1
    status_code = status.HTTP_200_OK

    if range_header is not None:
        start, end = _get_range_header(range_header, file_size)
        size = end - start + 1
        headers["content-length"] = str(size)
        headers["content-range"] = f"bytes {start}-{end}/{file_size}"
        status_code = status.HTTP_206_PARTIAL_CONTENT

    return StreamingResponse(
        send_bytes_range_requests(open(file_path, mode="rb"), start, end),
        headers=headers,
        status_code=status_code,
    )


@app.post("/api/timestamps/{video_id}", include_in_schema=False)
async def timestamps(request: Request, video_id: str):
    cookie = request.cookies.get("session")
    if cookie is not None:
        try:
            decoded_claims = auth.verify_session_cookie(cookie, check_revoked=True)
            user = auth.get_user(decoded_claims["user_id"])
        except:
            return JSONResponse(content={}, status_code=401)

        try:
            ts_arr = await request.json()
            # check if video exists in the database
            timestamps = db.collection("timestamps").document(video_id).get()
            if timestamps.exists:
                # set the timestamps
                db.collection("timestamps").document(video_id).set({"ts": ts_arr})
                # if the scorer for the video is not the current user, add the user to the list of scorers
                video = db.collection("videos").document(video_id).get()
                if video.exists:
                    d = video.to_dict()
                    if user.display_name not in d["scorers"]:
                        d["scorers"].append(user.display_name)
                        db.collection("videos").document(video_id).set(d)
                return JSONResponse(content={}, status_code=200)
            else:
                # create the timestamps
                db.collection("timestamps").document(video_id).set({"ts": ts_arr})
                return JSONResponse(content={}, status_code=201)
        except:
            JSONResponse(content={}, status_code=500)


@app.get("/api/timestamps/{video_id}", include_in_schema=False)
async def timestamps(request: Request, video_id: str):
    """Returns the timestamps for a video. Timestamps are stored as a tuple of (start, end) in seconds"""
    log.info(f"timestamps request {request.headers}")
    cookie = request.cookies.get("session")
    if cookie is not None:
        try:
            decoded_claims = auth.verify_session_cookie(cookie, check_revoked=True)
            user = auth.get_user(decoded_claims["user_id"])
        except:
            return JSONResponse(content={}, status_code=401)

        try:
            # check if the timestamps exist in the database
            timestamps = db.collection("timestamps").document(video_id).get()
            if timestamps.exists:
                d = timestamps.to_dict()
                d["id"] = timestamps.id
                return JSONResponse(content=d, status_code=200)
            else:
                return JSONResponse(content={}, status_code=404)
        except:
            JSONResponse(content={}, status_code=500)


@app.get("/api/user/keybindings", include_in_schema=False)
async def get_keybindings(request: Request):
    """Returns the keybindings for the current user"""
    cookie = request.cookies.get("session")
    if cookie is not None:
        try:
            decoded_claims = auth.verify_session_cookie(cookie, check_revoked=True)
            user = auth.get_user(decoded_claims["user_id"])
        except:
            return JSONResponse(content={}, status_code=401)

        try:
            keybindings = (
                db.collection("users").document(user.uid).get().to_dict()["keybindings"]
            )
            return JSONResponse(content=keybindings, status_code=200)
        except Exception as e:
            print(e)
            return JSONResponse(content={}, status_code=500)


@app.post("/api/user/keybindings", include_in_schema=False)
async def update_keybindings(request: Request):
    """Updates the keybindings for the current user"""
    cookie = request.cookies.get("session")
    if cookie is not None:
        try:
            decoded_claims = auth.verify_session_cookie(cookie, check_revoked=True)
            user = auth.get_user(decoded_claims["user_id"])
        except:
            return JSONResponse(content={}, status_code=401)

        try:
            # will be a dict of oldKey: key, newKey: key
            old_new_key = await request.json()
            # get the current keybindings
            current_keybindings = (
                db.collection("users").document(user.uid).get("keybindings")
            )
            for key_act in current_keybindings:
                if key_act["key"] == old_new_key["oldKey"]:
                    key_act["key"] = old_new_key["newKey"]
                    break
            # update the keybindings
            db.collection("users").document(user.uid).set(
                {"keybindings": current_keybindings}
            )
            return JSONResponse(content=current_keybindings, status_code=200)
        except:
            JSONResponse(content={}, status_code=500)
