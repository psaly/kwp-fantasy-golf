'''
Backend api endpoints for slack requests
'''
from fastapi import FastAPI, Request, HTTPException
import app.kwp_scoring as LiveScoring
import app.slack_utils as Slack

app = FastAPI()


@app.get("/")
@app.get("/scores")
def live_scores():
    """
    Live scoring test
    """
    _, scores = LiveScoring.get_team_scores(bonus=True)
    return scores


@app.post('/api/v1/slack/scores')
async def slack_scores(req: Request):
    """
    Endpoint for slack /scores.
    """
    form = await req.form()

    if not Slack.valid_request(form, Slack.SlackChannel.KWP):
        raise HTTPException(status_code=400, detail="Invalid token.")

    response_in_channel = "-h" not in form["text"]
    include_bonus = "-b" in form["text"]

    tourney_name, team_scores = LiveScoring.get_team_scores(
        bonus=include_bonus)

    return Slack.build_slack_response(
        team_scores,
        tourney_name,
        in_channel=response_in_channel,
        show_player_scores=True,
        bonus=include_bonus
    )
