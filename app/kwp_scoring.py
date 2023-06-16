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
    'Saly': ['Rory McIlroy', 'Viktor Hovland', 'Tony Finau', 'Max Homa', 'Jason Day', 'Wyndham Clark', 'Mito Pereira'],
    'Harv': ['Scottie Scheffler', 'Jordan Spieth', 'Xander Schauffele', 'Cameron Smith', 'Sungjae Im', 'Tyrrell Hatton', 'Justin Rose'],
    "O'Leary": ['Brooks Koepka', 'Dustin Johnson', 'Collin Morikawa', 'Justin Thomas', 'Hideki Matsuyama', 'Adam Scott', 'Bryson DeChambeau'],
    'Corby': ['Tommy Fleetwood', 'Jon Rahm', 'Cameron Young', 'Matt Fitzpatrick', 'Corey Conners', 'Shane Lowry', 'Patrick Cantlay']
}

ESPN_URL = 'https://www.espn.com/golf/leaderboard'
# ESPN_URL = 'https://www.espn.com/golf/leaderboard/_/tournamentId/401465523'


def main():
    """
    For running manually
    """
    tourney, scores = get_team_scores()
    print(tourney)
    print(scores)


def get_team_scores(bonus=True):
    """
    Compile team scores
    """
    tourney, all_players = scrape_live_leaderboard(ESPN_URL)

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

        if bonus:
            team_score = sum(x['kwp_score_to_par'] - x['kwp_bonus']
                             for x in player_scores[:COUNTING_SCORES])
        else:
            team_score = sum(x['kwp_score_to_par']
                             for x in player_scores[:COUNTING_SCORES])

        team_scores.append({
            'manager_name': manager,
            'team_score': team_score,
            'player_scores': player_scores
        })

    team_scores.sort(key=lambda x: x['team_score'])

    return tourney, team_scores


def scrape_live_leaderboard(url):
    """
    Scrape ESPN leaderboard and return list containing all player scores:
    [keys: "tournament_name", "player_name", "position", "score_to_par": "thru"}, ...]
    return tourney, player_scores
    """
    # make request and check status
    r = requests.get(url, timeout=5)
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

    worst_score = -102  # placeholder

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
            # If tournament hasn't started yet get tee times instead
            print(f"**INDEX ERROR--tournament is probably not live** {td}")
            tee_time_offset = 1
            for i, td in enumerate(tds):
                for child in td.findChildren():
                    if child.has_attr('class') and len(child['class']) > 1 and child['class'][1] == 'leaderboard_player_name':
                        player = child.text
                        score = 0
                        thru = tds[i+tee_time_offset].text
                        bonus = 0
                        player_scores[player] = {
                            "tournament_name": tourney_name,
                            "player_name": player,
                            "position": None,
                            "kwp_score_to_par": score,
                            "kwp_bonus": bonus,
                            "today": None,
                            "thru": thru
                        }

    # update all players who MC/WD/DQ score to the cut placeholder
    for player, data in player_scores.items():
        if data["kwp_score_to_par"] is None:
            data["kwp_score_to_par"] = worst_score + KWP_CUT_PENALTY

    return tourney_name, player_scores


if __name__ == "__main__":
    main()
