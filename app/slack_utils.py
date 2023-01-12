'''
For interacting with Slack
'''
from enum import Enum


class SlackChannel(Enum):
    '''
    Slack Object
    '''
    PFGL = (None, None)
    KWP = ('b9dpA3duAR2GWr9mHOClpgQL', 'TRSTAS2GJ')

    def __init__(self, token, team_id) -> None:
        self.token = token
        self.team_id = team_id


def valid_request(slack_form, channel: SlackChannel):
    '''
    Whether incoming request is valid
    '''
    return slack_form['token'] == channel.token and slack_form['team_id'] == channel.team_id


def build_slack_response(team_scoring: list[dict], tourney_name: str,
                         in_channel=True, show_player_scores=True, bonus=False
                         ) -> dict:
    """
    Build json for Slack response
    """
    scores_string = ''
    breakdown_string = ''

    for s in team_scoring:
        scores_string += f'*{s["manager_name"]}*: `{_display_score_to_par(s["team_score"])}`\n'
        breakdown_string += f'*{s["manager_name"]}*\n'

        for p in s["player_scores"]:
            breakdown_string += f'>{p["player_name"]}: `{_display_score_to_par(p["kwp_score_to_par"])}` thru {p["thru"]}\n'

        breakdown_string += '\n'

    if bonus:
        scores_string += '_Bonus: ON_'
    else:
        scores_string += '_Bonus: OFF_'

    slack_res = {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": tourney_name
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": scores_string
                }
            },
            {
                "type": "divider"
            }
        ]
    }

    if show_player_scores:
        slack_res["blocks"].extend([
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": breakdown_string
                }
            },
            {
                "type": "divider"
            }
        ])

    if in_channel:
        slack_res["response_type"] = "in_channel"

    print(slack_res)

    return slack_res


def _display_score_to_par(score: int) -> str:
    """
    Convert 0 to E and add '+' for over par scores
    """
    if score > 0:
        return '+' + str(score)
    if score == 0:
        return 'E'
    return str(score)
