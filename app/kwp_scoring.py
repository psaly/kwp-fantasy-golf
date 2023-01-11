'''
Scoring code
'''
import requests
from bs4 import BeautifulSoup

# Penalty for missed cut (worst score of anyone who made the cut + penalty)
KWP_CUT_PENALTY = 2
# Number of player scores counting toward team score
COUNTING_SCORES = 4
# Bonuses for 1-2-3-4-5 place finishes
KWP_BONUSES = [10, 5, 3, 2, 1]

kwp_teams = {
    'Saly': ['Tony Finau', 'Viktor Hovland', 'Tom Kim', 'Max Homa', 'Aaron Wise', 'Sahith Theegala', 'Keegan Bradley'],
    'Harv': ['Jordan Spieth', 'Seamus Power', 'J.J. Spaun', 'Brian Harman', 'Sungjae Im', 'Scottie Scheffler', 'Xander Schauffele'],
    "O'Leary": ['Justin Thomas', 'Sam Burns', 'Hideki Matsuyama', 'Collin Morikawa', 'Will Zalatoris', 'Billy Horschel', 'Adam Scott'],
    'Corby': ['Jon Rahm', 'Patrick Cantlay', 'Matt Fitzpatrick', 'Cameron Young', 'Corey Conners', 'Russell Henley', 'Sepp Straka'],
}


def main():
    """
    For running manually
    """
    all_players = scrape_live_leaderboard(
        'https://www.espn.com/golf/leaderboard/_/tournamentId/401465512')

    team_scores = []

    for manager, players in kwp_teams.items():
        player_scores = []
        for p in players:

            try:
                player_data = all_players[p]
                player_scores.append({
                    'player_name': p,
                    'kwp_score_to_par': player_data['kwp_score_to_par'],
                    'thru': player_data['thru'],
                    'kwp_bonus': player_data['kwp_bonus']
                })
            except KeyError:
                player_scores.append({
                    'player_name': p,
                    'kwp_score_to_par': 100,
                    'thru': 'not entered',
                    'kwp_bonus': 0
                })

        player_scores.sort(key=lambda x: x['kwp_score_to_par'])

        # if bonus
        team_score = sum(x['kwp_score_to_par'] - x['kwp_bonus']
                         for x in player_scores[:COUNTING_SCORES])
        # team_score = sum(x['kwp_score_to_par']
        #                  for x in player_scores[:COUNTING_SCORES])

        team_scores.append({
            'manager_name': manager,
            'team_score': team_score,
            'player_scores': player_scores
        })

    team_scores.sort(key=lambda x: x['team_score'])

    print(team_scores)


def scrape_live_leaderboard(url="https://www.espn.com/golf/leaderboard") -> list:
    """
    Scrape ESPN leaderboard and return list containing all player scores:
    [keys: "tournament_name", "player_name", "position", "score_to_par": "thru"}, ...]
    """
    # make request and check status
    r = requests.get(url)
    r.raise_for_status()

    soup = BeautifulSoup(r.content, 'html.parser')

    # Get tournament name
    tourney_name = soup.select_one('.Leaderboard__Event__Title').text

    # Check if the tournament is final because the formatting changes
    status = soup.find('div', class_='status')
    final = status and status.findChild() and 'Final' in status.findChild(
    ).text and 'Round' not in status.findChild().text

    # for storing parsed player data
    player_scores = {}

    worst_score = -1000  # placeholder

    pos_offset = 1  # will be changed to 2 if we see there are movement arrows in the table
    # loop through all tds
    tds = soup.select('td')
    for i, td in enumerate(tds):
        try:
            for child in td.findChildren():
                if child.has_attr('class') and child['class'][0] == 'MovementArrow':
                    pos_offset = 2
                if child.has_attr('class') and len(child['class']) > 1 and child['class'][1] == 'leaderboard_player_name':
                    pos = None
                    score = None
                    thru = 'F' if final else tds[i+3].text
                    today = tds[i+5].text if final else tds[i+2].text
                    player = child.text
                    kwp_bonus = 0

                    score_text = tds[i+1].text

                    if score_text == 'E':
                        score = 0
                    else:
                        try:
                            score = int(score_text)
                            worst_score = max(worst_score, score)

                        # if not an integer, will be CUT/WD/DQ etc. -- ESPN does this weird
                        except ValueError:
                            pos = score_text

                    # get position if we haven't already and store bonuses
                    if pos is None:
                        pos = tds[i-pos_offset].text
                    try:
                        pos_int = int(pos.lstrip("T"))
                        if pos_int < 6:
                            kwp_bonus = KWP_BONUSES[pos_int - 1]

                    except ValueError:
                        pass

                    # add to players list
                    # score could be None still if we need to fill in with worst score
                    # Maybe create an object here?

                    player_scores[player] = {
                        "tournament_name": tourney_name,
                        "player_name": player,
                        "position": pos,
                        "kwp_score_to_par": score,
                        "kwp_bonus": kwp_bonus,
                        "today": today,
                        "thru": thru
                    }

        except KeyError:
            print(f"**WEIRD ERROR** {td}")
        except IndexError:
            print(f"**INDEX ERROR--tournament is probably not live** {td}")

    print(f"Tourney: {tourney_name}")

    # update all players who MC/WD/DQ score to the cut placeholder
    for player, data in player_scores.items():
        if data["kwp_score_to_par"] is None:
            data["kwp_score_to_par"] = worst_score + KWP_CUT_PENALTY

    return player_scores


if __name__ == "__main__":
    main()