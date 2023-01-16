'''
Backend api endpoints for slack requests
'''
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
import requests
import app.kwp_scoring as LiveScoring
import app.slack_utils as Slack

app = FastAPI()


def _slack_response(req_form):
    response_in_channel = "-h" not in req_form["text"]
    include_bonus = "-b" in req_form["text"]

    tourney_name, team_scores = LiveScoring.get_team_scores(
        bonus=include_bonus)

    slack_response = Slack.build_slack_response(
        team_scores,
        tourney_name,
        in_channel=response_in_channel,
        show_player_scores=True,
        bonus=include_bonus
    )

    print(slack_response)

    requests.post(req_form['response_url'], data=slack_response, timeout=5)


@app.get("/")
@app.get("/scores")
def live_scores():
    """
    Live scoring test
    """
    _, scores = LiveScoring.get_team_scores(bonus=True)
    return scores


@app.post('/api/v1/slack/scores')
async def slack_scores(req: Request, bgtasks: BackgroundTasks):
    """
    Endpoint for slack /scores.
    Respond with 200 OK (slack must receive within 3s) and spawn bg task.
    """
    form = await req.form()

    if not Slack.valid_request(form, Slack.SlackChannel.KWP):
        raise HTTPException(status_code=400, detail="Invalid token.")

    bgtasks.add_task(_slack_response, form)

    return
