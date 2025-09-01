# #         '''extrapolate for previous weeks and try to see trend '''

# #         '''optimize/clean code'''

# #         '''Should be able to show over any period of weeks'''

# #         '''rank if player has 4 or more points in 3 outta 3 weeks'''


# #         '''if player has 4 or more points in 2 outta 3 weeks, rank'''

# #'''MAKE SURE ALL YOUR GAMEWEEKS START AT 0! NO CONFUSING BS!!!'''

# #'''NEED TO OPTIMIZE CODE! TAKING TOO LONG''' ---> inevitable cost of looking at every player.

# #'''Reduce time of List_of_consistent_players and reduce times you call fetch_player_history'''

#'''experiment with only haaland captain(viable strat), only salah, haaland or salah'''

import sys
import aiohttp
import requests
import asyncio
from fpl import FPL
from prettytable import PrettyTable
from fpl.utils import team_converter
import statistics
import time

total_points = 247 ###Points I started with at GW 5
average_cost = []
total_points_1 = 247
average_cost_1 = []
total_points_2 = 247
average_cost_2 = []
total_points_3 = 247
average_cost_3 = []
total_points_4 = 247
average_cost_4 = []
total_points_5 = 247
average_cost_5 = []
total_points_6 = 247
average_cost_6 = []
total_points_7 = 247
average_cost_7 = []
total_points_8 = 247
average_cost_8 = []
total_points_9 = 247
average_cost_9 = []


async def fetch_players(session):
    """Fetches players from FPL api and converts them to usable objects through the FPL import"""
    fpl = FPL(session)
    return await fpl.get_players()


async def fetch_player_history(session, player_id):
    """Gets the player's data from all the previous gameweeks"""
    next_url = f"https://fantasy.premierleague.com/api/element-summary/{player_id}/"
    response = await session.get(next_url)
    return await response.json()


def returned_consistently(gameweek, history, in_a_row, excused_weeks=0):
    if (len(history) <= gameweek - 1):  # Exits function if player hasn't played enough gameweeks
        return False

    counter = 0
    history_points_list = []
    for i in range(gameweek-in_a_row,gameweek):
        history_points_list.append(history[i]["total_points"])
        if history[i]["total_points"] < 4:
            counter+=1
            if counter > excused_weeks:
                return False
    return history_points_list

def make_table(player_achievement_dicts, in_a_row, gameweek):
    """Function makes the table that displays the data."""
    player_table = PrettyTable()  # Makes table object
    player_table.field_names = [
        "Player",
        "£",
        *[f"Gameweek {gameweek - i}" for i in range(in_a_row)],
        f"{in_a_row} Week Average",
        "Total Average",
    ]  # Makes top row
    player_table.align["Player"] = "l"

    for _,player in player_achievement_dicts.items():  # Creates data to add to table
        gameweek_points_list = [player[1][i] for i in range(in_a_row)]
        gameweek_points_list.reverse()
        total_points = sum(gameweek_points_list)
        average = total_points / len(gameweek_points_list)
        points = player[0].points_per_game
        add_row_list = [player[0].web_name, f"£{player[0].now_cost / 10}"]
        add_row_list.extend(gameweek_points_list)
        add_row_list.extend([average, points])
        player_table.add_row(add_row_list)

    print(player_table)


def create_dictionary(list_of_consistent_players):
    """Updates the player_achievement_dict for every person who made it through that gameweek"""
    player_achievement_dict = {}
    for player in list_of_consistent_players:
        player_achievement_dict[player[0].web_name] = player[0]
    return player_achievement_dict


async def best_captain_total_points(team, gameweek, session):
    """Given a team, returns the total score with best possible captain."""
    total_score = 0
    highest_scorer = [0, "player"]
    for player in team:
        history = await fetch_player_history(session, player.id)
        if history["history"][gameweek]["total_points"] > highest_scorer[0]:
            total_score -= highest_scorer[0]
            total_score += history["history"][gameweek]["total_points"] * 2
            highest_scorer = [
                history["history"][gameweek]["total_points"],
                player.web_name,
            ]
        else:
            total_score += history["history"][gameweek]["total_points"]
    return total_score


def remove_highest_std(player_scores):
    """Remove the score that contributes the most to the standard deviation."""
    if len(player_scores) == 0:
        return []

    mean = statistics.mean(player_scores)
    index_to_remove = max(
        range(len(player_scores)), key=lambda i: (player_scores[i] - mean) ** 2
    )

    del player_scores[index_to_remove]
    return player_scores


def cv(player_scores):
    """Coefficient of variation calculation."""
    if len(player_scores) == 0:
        return (0, 0, 0)

    mean = statistics.mean(player_scores)
    std = statistics.stdev(player_scores)

    if mean == 0 or std == 0:
        return (0, 0, 0)

    cv_val = std / mean

    if cv_val == 0:
        return (0, 0, 0)

    return (mean, std, 1 / cv_val)


def ordered_best_cv(list_of_player_lists):
    """Order players by best CV."""
    cv_list = []
    for (player_scores) in (list_of_player_lists):
        if cv(player_scores[0])[2] < 1:
            new_player_score_list = remove_highest_std(player_scores[0])
            if cv(new_player_score_list)[2] < 1:
                continue
            else:
                cv_list.append((new_player_score_list, player_scores[1]))
        else:
            cv_list.append(player_scores)
    cv_list.sort(key=lambda x: statistics.mean(x[0]), reverse=True)
    returned_list = [player[1] for player in cv_list]
    return returned_list


async def add_team_points(team, gameweek, session, cap):
    """Add team points given a team and a chosen captain."""
    total_score = 0
    for player in team:
        history = await fetch_player_history(session, player.id)
        total_score += history["history"][gameweek]["total_points"]
    history = await fetch_player_history(session, cap.id)
    total_score += history["history"][gameweek]["total_points"]
    return total_score


async def captain_points(cap, gameweek, session):
    """Return captain's points."""
    history = await fetch_player_history(session, cap.id)
    captain_points = history["history"][gameweek]["total_points"]
    return captain_points


async def highest_average_scorer_captain_name(team, gameweek, session, in_a_row):
    """Find the highest average scorer in the given team for captain."""
    whole_team_list = []
    for player in team:
        history = await fetch_player_history(session, player.id)
        list_of_scores = [
            history["history"][gameweek - i]["total_points"]
            for i in range(1, in_a_row + 1)
            if len(history["history"]) >= gameweek
        ]
        whole_team_list.append((list_of_scores, player))
    whole_team_list.sort(key=lambda x: statistics.mean(x[0]), reverse=True)
    captain_object = whole_team_list[0][1]
    return captain_object.web_name


async def team_versus(team, gameweek, session):
    total_score = 0
    highest_scorer = [0, "player"]
    for player in team:
        history = await fetch_player_history(session, player.id)
        if history["history"][gameweek]["total_points"] > highest_scorer[0]:
            total_score -= highest_scorer[0]
            total_score += history["history"][gameweek]["total_points"] * 2
            highest_scorer = [
                history["history"][gameweek]["total_points"],
                history["history"][gameweek]["opponent_team"],
            ]
        else:
            total_score += history["history"][gameweek]["total_points"]
    if highest_scorer[1] == "player":
        return None
    else:
        return team_converter(highest_scorer[1])


async def best_captain_points_finder(player_achievement_dict, gameweek, session):
    """Find the points of the best captain from the dict."""
    highest_scorer = [0, "player"]
    for _,player in player_achievement_dict.items():
        if gameweek == 11 and player.web_name == "Harrison": 
            continue
        history = await fetch_player_history(session, player.id)
        if history["history"][gameweek]["total_points"] > highest_scorer[0]:
            highest_scorer = [history["history"][gameweek]["total_points"],player.web_name]
    return highest_scorer[0]


async def best_captain_name_finder(player_achievement_dict, gameweek, session):
    """Find the name of the best captain."""
    highest_scorer = [0, "player"]
    for _,player in player_achievement_dict.items():
        if gameweek == 11 and player.web_name == "Harrison": 
            continue
        history = await fetch_player_history(session, player.id)
        if history["history"][gameweek]["total_points"] > highest_scorer[0]:
            highest_scorer = [
                history["history"][gameweek]["total_points"],
                player.web_name,
            ]
    return highest_scorer[1]


async def list_of_consistent_players(players, gameweek, in_a_row, session, excused_weeks):
    """Yield players that returned consistently."""
    for player in players:
        history = await fetch_player_history(session, player.id)
        consistently = returned_consistently(gameweek, history["history"], in_a_row, excused_weeks)
        if consistently:
            yield (player,consistently)

def print_data(final_team,total_gameweek_points,best_captain_points,best_captain_name,average_scorer_captain_name,average_scorer_captain_points,total_cost,gameweek,in_a_row,excused_weeks,total_points,average_cost):
    print(f"Final Team: {final_team}")
    print(f"Gameweek: {gameweek+1}")
    print(f"Best Captain: {best_captain_name}")
    print(f"Best Captain points doubled: {best_captain_points*2}")
    print(f"My Captain: {average_scorer_captain_name}")
    print(f"My Captain points doubled: {average_scorer_captain_points*2}")
    print(f"Gameweek Points: {total_gameweek_points}")
    print(f"Weeks in a row: {in_a_row}")
    print(f"Excused Weeks: {excused_weeks}")
    print(f"Total Points: {total_points}")
    print(f"Team Total Cost: {total_cost}")
    print(f"Team Total Average Cost: {round(statistics.mean(average_cost),1)}")
    print("---------------------------------------")


def make_usable_team(team,formation):
    '''takes in team which is a list of player objects and the formation which is a tuple and outputs a valid team'''
    valid_team = []
    for i in range(1,len(formation)+1):
        counter = 0
        for player in team:
            if counter == formation[i-1]:
                break
            if player.element_type == i:
                valid_team.append(player)
                counter += 1
    return valid_team


def predicted_team(new_all_ordered_times_added, cap):
    if cap is None:
        # Handle the scenario if no captain was found.
        raise ValueError("No captain was provided.")

    if cap in new_all_ordered_times_added:
        new_all_ordered_times_added.remove(cap)
        possible_team = [cap]
    else:
        possible_team = [cap]

    goalkeeper_counter = 0
    defender_counter = 0
    midfielder_counter = 0
    attacker_counter = 0
    for player in new_all_ordered_times_added:
        if player is None:
            continue
        if player.element_type == 1:
            goalkeeper_counter += 1
        if player.element_type == 2:
            defender_counter += 1
        if player.element_type == 3:
            midfielder_counter += 1
        if player.element_type == 4:
            attacker_counter += 1
        possible_team.append(player)
        if (
            goalkeeper_counter >= 1
            and defender_counter >= 3
            and midfielder_counter >= 5
            and attacker_counter >= 2
        ):
            return make_usable_team(possible_team, (1, 3, 5, 2))
        if (
            goalkeeper_counter >= 1
            and defender_counter >= 3
            and midfielder_counter >= 4
            and attacker_counter >= 3
        ):
            return make_usable_team(possible_team, (1, 3, 4, 3))
        if (
            goalkeeper_counter >= 1
            and defender_counter >= 4
            and midfielder_counter >= 5
            and attacker_counter >= 1
        ):
            return make_usable_team(possible_team, (1, 4, 5, 1))
        if (
            goalkeeper_counter >= 1
            and defender_counter >= 4
            and midfielder_counter >= 4
            and attacker_counter >= 2
        ):
            return make_usable_team(possible_team, (1, 4, 4, 2))
        if (
            goalkeeper_counter >= 1
            and defender_counter >= 4
            and midfielder_counter >= 3
            and attacker_counter >= 3
        ):
            return make_usable_team(possible_team, (1, 4, 3, 3))
        if (
            goalkeeper_counter >= 1
            and defender_counter >= 5
            and midfielder_counter >= 4
            and attacker_counter >= 1
        ):
            return make_usable_team(possible_team, (1, 5, 4, 1))
        if (
            goalkeeper_counter >= 1
            and defender_counter >= 5
            and midfielder_counter >= 3
            and attacker_counter >= 2
        ):
            return make_usable_team(possible_team, (1, 5, 3, 2))
        if (
            goalkeeper_counter >= 1
            and defender_counter >= 5
            and midfielder_counter >= 2
            and attacker_counter >= 3
        ):
            return make_usable_team(possible_team, (1, 5, 2, 3))


async def find_captain_with_cv(new_all_ordered_times_added, gameweek, in_a_row, session):
    whole_team_list = []
    for player in new_all_ordered_times_added:
        history = await fetch_player_history(session, player.id)
        possible_captain_score = []
        for i in range(1, in_a_row + 1):
            if len(history["history"]) >= gameweek:
                possible_captain_score.append(history["history"][gameweek - i]["total_points"])
        whole_team_list.append((possible_captain_score, player))
    ordered = ordered_best_cv(whole_team_list)
    if not ordered:
        return None
    captain_object = ordered[0]
    return captain_object

async def find_captain_at_beginning(new_all_ordered_times_added, gameweek, in_a_row, session):
    '''Finds best captain based on best average of all players in new_all_ordered_times_added'''
    whole_team_list = []
    for player in new_all_ordered_times_added:
        history = await fetch_player_history(session, player.id)
        possible_captain_score = []
        for i in range(1, in_a_row + 1):
            if len(history["history"]) >= gameweek:
                possible_captain_score.append(history["history"][gameweek - i]["total_points"])
        if possible_captain_score:
            whole_team_list.append((possible_captain_score, player))
    if not whole_team_list:
        return None
    whole_team_list.sort(key=lambda x: statistics.mean(x[0]), reverse=True)  # Sorts by highest average
    captain_object = whole_team_list[0][1]
    return captain_object

async def prep_team_data(new_all_ordered_times_added,gimme_cap,player_achievement_dict,gameweek,session,in_a_row):
    final_predicted_team = predicted_team(new_all_ordered_times_added, gimme_cap)
    final_team_names = []
    total_cost = 0
    for player in final_predicted_team:
        final_team_names.append(player.web_name)
        total_cost += player.now_cost / 10

    best_captain_points = await best_captain_points_finder(player_achievement_dict, gameweek, session)
    best_captain_name = await best_captain_name_finder(player_achievement_dict, gameweek, session)
    average_scorer_captain_name = gimme_cap.web_name
    average_scorer_captain_points = await captain_points(gimme_cap, gameweek, session)
    team_total_points = await add_team_points(final_predicted_team, gameweek, session, gimme_cap)
    return (final_team_names,team_total_points,best_captain_points,best_captain_name,average_scorer_captain_name,average_scorer_captain_points,total_cost)

async def cheap_average_team(player_achievement_dict, gameweek, session, in_a_row):
    new_all_ordered_times_added = []
    for _,player in player_achievement_dict.items():
        new_all_ordered_times_added.append(player)
    new_all_ordered_times_added.sort(key=lambda x: (float(x.points_per_game) ** 2 / x.now_cost),reverse=True)

    gimme_cap = await find_captain_at_beginning(
        new_all_ordered_times_added, gameweek, in_a_row, session
    )

    if gimme_cap is None:
        raise ValueError("No players available to choose a captain from in cheap_average_team.")

    return await prep_team_data(new_all_ordered_times_added,gimme_cap,player_achievement_dict,gameweek,session,in_a_row)

async def points_average_team(player_achievement_dict, gameweek, session, in_a_row):
    new_all_ordered_times_added = []
    for _,player in player_achievement_dict.items():
        new_all_ordered_times_added.append(player)
    new_all_ordered_times_added.sort(key=lambda x: x.points_per_game,reverse=True)

    gimme_cap = await find_captain_at_beginning(
        new_all_ordered_times_added, gameweek, in_a_row, session
    )

    if gimme_cap is None:
        raise ValueError("No players available to choose a captain from in points_average_team.")

    return await prep_team_data(new_all_ordered_times_added,gimme_cap,player_achievement_dict,gameweek,session,in_a_row)

async def pointsovertime_average_team(player_achievement_dict, gameweek, session, in_a_row):
    new_all_ordered_times_added = []
    for _,player in player_achievement_dict.items():
        new_all_ordered_times_added.append(player)
    whole_list = []
    for player in new_all_ordered_times_added:
        history = await fetch_player_history(session, player.id)
        list_of_scores = [history["history"][gameweek - i]["total_points"] for i in range(1, in_a_row + 1) if len(history["history"]) >= gameweek]
        if list_of_scores:
            whole_list.append((list_of_scores,player))
    whole_list.sort(key=lambda x: statistics.mean(x[0]),reverse=True)

    if not whole_list:
        raise ValueError("No players available to form a team in pointsovertime_average_team.")

    new_all_ordered_times_added = [player[1] for player in whole_list]

    gimme_cap = await find_captain_at_beginning(
        new_all_ordered_times_added, gameweek, in_a_row, session
    )

    if gimme_cap is None:
        raise ValueError("No captain available in pointsovertime_average_team.")

    return await prep_team_data(new_all_ordered_times_added,gimme_cap,player_achievement_dict,gameweek,session,in_a_row)

async def pointsovertimecheap_average_team(player_achievement_dict, gameweek, session, in_a_row):
    new_all_ordered_times_added = []
    for _,player in player_achievement_dict.items():
        new_all_ordered_times_added.append(player)
    whole_list = []
    for player in new_all_ordered_times_added:
        history = await fetch_player_history(session, player.id)
        list_of_scores = [history["history"][gameweek - i]["total_points"] for i in range(1, in_a_row + 1) if len(history["history"]) >= gameweek]
        if list_of_scores:
            whole_list.append((list_of_scores,player))
    whole_list.sort(key=lambda x: statistics.mean(x[0])**2 / x[1].now_cost,reverse=True)

    if not whole_list:
        raise ValueError("No players available to form a team in pointsovertimecheap_average_team.")

    new_all_ordered_times_added = [player[1] for player in whole_list]

    gimme_cap = await find_captain_at_beginning(
        new_all_ordered_times_added, gameweek, in_a_row, session
    )

    if gimme_cap is None:
        raise ValueError("No captain available in pointsovertimecheap_average_team.")

    return await prep_team_data(new_all_ordered_times_added,gimme_cap,player_achievement_dict,gameweek,session,in_a_row)

###CV CAPTAIN

async def cheap_cv_team(player_achievement_dict, gameweek, session, in_a_row):
    new_all_ordered_times_added = []
    for _,player in player_achievement_dict.items():
        new_all_ordered_times_added.append(player)
    new_all_ordered_times_added.sort(key=lambda x: (float(x.points_per_game) ** 2 / x.now_cost),reverse=True)

    gimme_cap = await find_captain_with_cv(new_all_ordered_times_added, gameweek, in_a_row, session)
    if gimme_cap is None:
        raise ValueError("No captain available in cheap_cv_team.")

    return await prep_team_data(new_all_ordered_times_added,gimme_cap,player_achievement_dict,gameweek,session,in_a_row)

async def points_cv_team(player_achievement_dict, gameweek, session, in_a_row):
    new_all_ordered_times_added = []
    for _,player in player_achievement_dict.items():
        new_all_ordered_times_added.append(player)
    new_all_ordered_times_added.sort(key=lambda x: x.points_per_game,reverse=True)

    gimme_cap = await find_captain_with_cv(new_all_ordered_times_added, gameweek, in_a_row, session)
    if gimme_cap is None:
        raise ValueError("No captain available in points_cv_team.")

    return await prep_team_data(new_all_ordered_times_added,gimme_cap,player_achievement_dict,gameweek,session,in_a_row)

async def pointsovertime_cv_team(player_achievement_dict, gameweek, session, in_a_row):
    new_all_ordered_times_added = []
    for _,player in player_achievement_dict.items():
        new_all_ordered_times_added.append(player)
    whole_list = []
    for player in new_all_ordered_times_added:
        history = await fetch_player_history(session, player.id)
        list_of_scores = [history["history"][gameweek - i]["total_points"] for i in range(1, in_a_row + 1) if len(history["history"]) >= gameweek]
        if list_of_scores:
            whole_list.append((list_of_scores,player))
    whole_list.sort(key=lambda x: statistics.mean(x[0]),reverse=True)

    if not whole_list:
        raise ValueError("No players available in pointsovertime_cv_team.")

    new_all_ordered_times_added = [player[1] for player in whole_list]

    gimme_cap = await find_captain_with_cv(new_all_ordered_times_added, gameweek, in_a_row, session)
    if gimme_cap is None:
        raise ValueError("No captain available in pointsovertime_cv_team.")

    return await prep_team_data(new_all_ordered_times_added,gimme_cap,player_achievement_dict,gameweek,session,in_a_row)

async def pointsovertimecheap_cv_team(player_achievement_dict, gameweek, session, in_a_row):
    new_all_ordered_times_added = []
    for _,player in player_achievement_dict.items():
        new_all_ordered_times_added.append(player)
    whole_list = []
    for player in new_all_ordered_times_added:
        history = await fetch_player_history(session, player.id)
        list_of_scores = [history["history"][gameweek - i]["total_points"] for i in range(1, in_a_row + 1) if len(history["history"]) >= gameweek]
        if list_of_scores:
            whole_list.append((list_of_scores,player))
    whole_list.sort(key=lambda x: statistics.mean(x[0])**2 / x[1].now_cost,reverse=True)

    if not whole_list:
        raise ValueError("No players available in pointsovertimecheap_cv_team.")

    new_all_ordered_times_added = [player[1] for player in whole_list]

    gimme_cap = await find_captain_with_cv(new_all_ordered_times_added, gameweek, in_a_row, session)
    if gimme_cap is None:
        raise ValueError("No captain available in pointsovertimecheap_cv_team.")

    return await prep_team_data(new_all_ordered_times_added,gimme_cap,player_achievement_dict,gameweek,session,in_a_row)

### SALAH CAPTAIN

async def cheap_salah_team(player_achievement_dict, gameweek, session, in_a_row):
    new_all_ordered_times_added = list(player_achievement_dict.values())
    new_all_ordered_times_added.sort(key=lambda x: (float(x.points_per_game) ** 2 / x.now_cost),reverse=True)

    salah = None
    for player in new_all_ordered_times_added:
        if player.web_name == 'Salah':
            salah = player
            break

    if salah is None:
        for player in new_all_ordered_times_added:
            if player.web_name == 'Haaland':
                salah = player
                break

    # If still None, fallback to another logic:
    if salah is None:
        if new_all_ordered_times_added:
            salah = new_all_ordered_times_added[0]  # fallback: just pick the top player
        else:
            raise ValueError("No players found to captain in cheap_salah_team.")

    gimme_cap = salah
    return await prep_team_data(new_all_ordered_times_added,gimme_cap,player_achievement_dict,gameweek,session,in_a_row)

async def points_salah_team(player_achievement_dict, gameweek, session, in_a_row):
    new_all_ordered_times_added = list(player_achievement_dict.values())
    new_all_ordered_times_added.sort(key=lambda x: x.points_per_game,reverse=True)

    salah = None
    for player in new_all_ordered_times_added:
        if player.web_name == 'Salah':
            salah = player
            break

    if salah is None:
        for player in new_all_ordered_times_added:
            if player.web_name == 'Haaland':
                salah = player
                break

    if salah is None:
        if new_all_ordered_times_added:
            salah = new_all_ordered_times_added[0]
        else:
            raise ValueError("No players found to captain in points_salah_team.")

    gimme_cap = salah

    return await prep_team_data(new_all_ordered_times_added,gimme_cap,player_achievement_dict,gameweek,session,in_a_row)

async def pointsovertime_salah_team(player_achievement_dict, gameweek, session, in_a_row):
    new_all_ordered_times_added = list(player_achievement_dict.values())
    whole_list = []
    for player in new_all_ordered_times_added:
        history = await fetch_player_history(session, player.id)
        list_of_scores = [history["history"][gameweek - i]["total_points"] for i in range(1, in_a_row + 1) if len(history["history"]) >= gameweek]
        if list_of_scores:
            whole_list.append((list_of_scores,player))
    whole_list.sort(key=lambda x: statistics.mean(x[0]),reverse=True)

    if not whole_list:
        raise ValueError("No players available in pointsovertime_salah_team.")

    new_all_ordered_times_added = [player[1] for player in whole_list]

    salah = None
    for player in new_all_ordered_times_added:
        if player.web_name == 'Salah':
            salah = player
            break
    if salah is None:
        for player in new_all_ordered_times_added:
            if player.web_name == 'Haaland':
                salah = player
                break

    if salah is None:
        if new_all_ordered_times_added:
            salah = new_all_ordered_times_added[0]
        else:
            raise ValueError("No players found to captain in pointsovertime_salah_team.")

    gimme_cap = salah

    return await prep_team_data(new_all_ordered_times_added,gimme_cap,player_achievement_dict,gameweek,session,in_a_row)


async def main(gameweek, in_a_row, excused_weeks=0):
    global total_points
    global total_points_1
    global total_points_2
    global total_points_3
    global total_points_4
    global total_points_5
    global total_points_6
    global total_points_7
    global total_points_8
    global total_points_9
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        players = await fetch_players(session)
        player_achievement_dicts = {}
        start = time.time()
        async for player in  list_of_consistent_players(players, gameweek, in_a_row, session, excused_weeks):
            player_achievement_dicts[player[0].web_name] = player
        print(time.time() - start)
        print('*********************')
        starter = time.time()
        make_table(player_achievement_dicts, in_a_row, gameweek)
        print(time.time()-starter)
        print('*********************')

        player_achievement_dict ={}
        final_list = []
        for _,player in player_achievement_dicts.items():
            final_list.append(player)
        final_list.sort(key=lambda x: sum(x[1]), reverse=True)
        for player in final_list:
            player_achievement_dict[player[0].web_name] = player[0]

        # CHEAP
        (final_team,total_gameweek_points,best_captain_points,best_captain_name,average_scorer_captain_name,average_scorer_captain_points,total_cost,) = await cheap_average_team(player_achievement_dict, gameweek, session, in_a_row)
        
        total_points += total_gameweek_points
        average_cost.append(total_cost)

        print_data(final_team,total_gameweek_points,best_captain_points,best_captain_name,average_scorer_captain_name,average_scorer_captain_points,total_cost,gameweek,in_a_row,excused_weeks,total_points,average_cost)

        # EXPENSIVE TEAM
        (final_team,total_gameweek_points,best_captain_points,best_captain_name,average_scorer_captain_name,average_scorer_captain_points,total_cost) = await points_average_team(player_achievement_dict, gameweek, session, in_a_row)
        total_points_1 += total_gameweek_points
        average_cost_1.append(total_cost)
        print_data(final_team,total_gameweek_points,best_captain_points,best_captain_name,average_scorer_captain_name,average_scorer_captain_points,total_cost,gameweek,in_a_row,excused_weeks,total_points_1,average_cost_1)

        # POINTS OVER TIME
        (final_team,total_gameweek_points,best_captain_points,best_captain_name,average_scorer_captain_name,average_scorer_captain_points,total_cost) = await pointsovertime_average_team(player_achievement_dict, gameweek, session, in_a_row)
        total_points_2 += total_gameweek_points
        average_cost_2.append(total_cost)
        print_data(final_team,total_gameweek_points,best_captain_points,best_captain_name,average_scorer_captain_name,average_scorer_captain_points,total_cost,gameweek,in_a_row,excused_weeks,total_points_2,average_cost_2)

        # POINTS OVER TIME CHEAP
        (final_team,total_gameweek_points,best_captain_points,best_captain_name,average_scorer_captain_name,average_scorer_captain_points,total_cost) = await pointsovertimecheap_average_team(player_achievement_dict, gameweek, session, in_a_row)
        total_points_3 += total_gameweek_points
        average_cost_3.append(total_cost)
        print_data(final_team,total_gameweek_points,best_captain_points,best_captain_name,average_scorer_captain_name,average_scorer_captain_points,total_cost,gameweek,in_a_row,excused_weeks,total_points_3,average_cost_3)

        # CHEAP WITH CV CAPTAIN
        (final_team,total_gameweek_points,best_captain_points,best_captain_name,average_scorer_captain_name,average_scorer_captain_points,total_cost) = await cheap_cv_team(player_achievement_dict, gameweek, session, in_a_row)
        total_points_4 += total_gameweek_points
        average_cost_4.append(total_cost)
        print_data(final_team,total_gameweek_points,best_captain_points,best_captain_name,average_scorer_captain_name,average_scorer_captain_points,total_cost,gameweek,in_a_row,excused_weeks,total_points_4,average_cost_4)

        # EXPENSIVE TEAM CV CAPTAIN
        (final_team,total_gameweek_points,best_captain_points,best_captain_name,average_scorer_captain_name,average_scorer_captain_points,total_cost) = await points_cv_team(player_achievement_dict, gameweek, session, in_a_row)
        total_points_5 += total_gameweek_points
        average_cost_5.append(total_cost)
        print_data(final_team,total_gameweek_points,best_captain_points,best_captain_name,average_scorer_captain_name,average_scorer_captain_points,total_cost,gameweek,in_a_row,excused_weeks,total_points_5,average_cost_5)

        # POINTS OVER TIME WITH CV
        (final_team,total_gameweek_points,best_captain_points,best_captain_name,average_scorer_captain_name,average_scorer_captain_points,total_cost) = await pointsovertime_cv_team(player_achievement_dict, gameweek, session, in_a_row)
        total_points_6 += total_gameweek_points
        average_cost_6.append(total_cost)
        print_data(final_team,total_gameweek_points,best_captain_points,best_captain_name,average_scorer_captain_name,average_scorer_captain_points,total_cost,gameweek,in_a_row,excused_weeks,total_points_6,average_cost_6)

        # POINTS OVER TIME CHEAP WITH CV
        (final_team,total_gameweek_points,best_captain_points,best_captain_name,average_scorer_captain_name,average_scorer_captain_points,total_cost) = await pointsovertimecheap_cv_team(player_achievement_dict, gameweek, session, in_a_row)
        total_points_7 += total_gameweek_points
        average_cost_7.append(total_cost)
        print_data(final_team,total_gameweek_points,best_captain_points,best_captain_name,average_scorer_captain_name,average_scorer_captain_points,total_cost,gameweek,in_a_row,excused_weeks,total_points_7,average_cost_7)

        # CHEAP WITH SALAH
        (final_team,total_gameweek_points,best_captain_points,best_captain_name,average_scorer_captain_name,average_scorer_captain_points,total_cost,) = await cheap_salah_team(player_achievement_dict, gameweek, session, in_a_row)
        total_points_8 += total_gameweek_points
        average_cost_8.append(total_cost)
        print_data(final_team,total_gameweek_points,best_captain_points,best_captain_name,average_scorer_captain_name,average_scorer_captain_points,total_cost,gameweek,in_a_row,excused_weeks,total_points_8,average_cost_8)

        # EXPENSIVE TEAM WITH SALAH
        (final_team,total_gameweek_points,best_captain_points,best_captain_name,average_scorer_captain_name,average_scorer_captain_points,total_cost) = await points_salah_team(player_achievement_dict, gameweek, session, in_a_row)
        total_points_9 += total_gameweek_points
        average_cost_9.append(total_cost)
        print_data(final_team,total_gameweek_points,best_captain_points,best_captain_name,average_scorer_captain_name,average_scorer_captain_points,total_cost,gameweek,in_a_row,excused_weeks,total_points_9,average_cost_9)


if __name__ == "__main__":
    if sys.version_info >= (3, 7):
        loop = asyncio.get_event_loop()

        for i in range(0, 2):
            loop.run_until_complete(main(i, 2, 1))
