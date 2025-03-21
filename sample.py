from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests

app = FastAPI()

class URLRequest(BaseModel):
    post_url: str

@app.post("/resolve-fb-url/")
async def resolve_fb_url(request: URLRequest):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(request.post_url, allow_redirects=True, headers=headers, timeout=10)
        final_url = response.url

        return {"resolved_url": final_url}

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error resolving URL: {str(e)}")
