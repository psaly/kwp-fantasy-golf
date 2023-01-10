__author__ = 'piercesaly'

import requests
from bs4 import BeautifulSoup

KWP_CUT_PENALTY = 2

# Bonuses for 1-2-3-4-5 place finishes
KWP_BONUSES = [10, 5, 3, 2, 1]


def main():
    """
    Main
    """
    players = scrape_live_leaderboard(
        'https://www.espn.com/golf/leaderboard/_/tournamentId/401465512')
    print(players)


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
    all_players = []

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
                    all_players.append({
                        "tournament_name": tourney_name,
                        "player_name": player,
                        "position": pos,
                        "kwp_score_to_par": score,
                        "kwp_bonus": kwp_bonus,
                        "today": today,
                        "thru": thru
                    })
        except KeyError:
            print(f"**WEIRD ERROR** {td}")
        except IndexError:
            print(f"**INDEX ERROR--tournament is probably not live** {td}")

    print(f"Tourney: {tourney_name}")

    # update all players who MC/WD/DQ score to the cut placeholder
    for player in all_players:
        if player["kwp_score_to_par"] is None:
            player["kwp_score_to_par"] = worst_score + KWP_CUT_PENALTY

    return all_players


if __name__ == "__main__":
    main()
