from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

import secrets
import json
import os


config_root_path = os.getenv("MILESIGHT_ROOT_PATH") or ""
config_username = os.getenv("MILESIGHT_SUBMIT_USERNAME")
config_password = os.getenv("MILESIGHT_SUBMIT_PASSWORD")

app = FastAPI(root_path=config_root_path)
security = HTTPBasic(auto_error=False)

@app.post("/")
async def create_file(request: Request, credentials: HTTPBasicCredentials = Depends(security)):
    if config_username and config_password:
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Basic"},
            )

        is_correct_username = secrets.compare_digest(credentials.username.encode("utf8"), config_username.encode("utf8"))
        is_correct_password = secrets.compare_digest(credentials.password.encode("utf8"), config_password.encode("utf8"))

        if not is_correct_username or not is_correct_password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Basic"},
            )

    payload = await request.json()

    try:
        with open("data.json", "r") as file:
            data = json.load(file) or []
    except:
        data = []

    with open("data.json", "w") as file:
        data.append(payload)
        json.dump(data, file)

    return {"message": "Data received successfully"}


@app.get("/data")
async def get_data():
    with open("data.json", "r") as file:
        data = json.load(file)

    return data
