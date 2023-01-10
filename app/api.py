
from fastapi import FastAPI

app = FastAPI()


@app.get("/", tags=["Home"])
def get_root():
    """
    Test endpoint
    """
    return {
        "message": "Welcome."
    }
