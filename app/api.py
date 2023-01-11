'''
Backend api endpoints for slack requests
'''
from fastapi import FastAPI
import app.kwp_scoring as LiveScoring

app = FastAPI()


@app.get("/", tags=["Home"])
def get_root():
    """
    Test endpoint
    """
    return {
        "message": "Welcome."
    }


@app.get("/scores")
def live_scores():
    """
    Live scoring
    """
    return LiveScoring.scrape_live_leaderboard(
        'https://www.espn.com/golf/leaderboard/_/tournamentId/401465512')
