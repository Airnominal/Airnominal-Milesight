from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import json
import os


root = os.getenv("ROOT_PATH") or ""
app = FastAPI(root_path=root)


@app.post("/")
async def create_file(request: Request):
    payload = await request.json()

    with open("data.json", "r") as file:
        try: data = json.load(file) or []
        except: data = []

    with open("data.json", "w") as file:
        data.append(payload)
        json.dump(data, file)

    return {"message": "Data received successfully"}


@app.get("/data")
async def get_data():
    with open("data.json", "r") as file:
        data = json.load(file)

    return data
