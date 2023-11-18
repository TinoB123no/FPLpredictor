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
    """Function returns a boolean value on whether or not a player returned consistently over a period of weeks in a row. If true it returns True and a list of points gained during those weeks, returns False otherwise. History['history'] is passed in. History is the history of a player and is a dictionary inside a dictionary I believe. To index do history[@gameweek#]['what_you_want']."""
    # gameweek_list = [gameweek - i for i in range(1, in_a_row + 1)]  # List of all the gameweeks but minus one cause dictionary starts at 0 whereas FPL starts at GW 1

    # if (len(history) <= gameweek_list[0]):  # Exits function if player hasn't played enough gameweeks
    #     return False

    # gameweek_list = [gameweek - i for i in range(1, in_a_row + 1)]  # List of all the gameweeks but minus one cause dictionary starts at 0 whereas FPL starts at GW 1

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
    """Function makes the table that displays the data. Takes in players which is a list of tuples in the form: (FPL_player_object,player's gameweek scores list). It takes in the weeks in a row you want and up to the gameweek you want to be displayed also. ALSO ADDS PLAYERS TO THE ACHEIVEMENT DICTIONARY. Should probably be in a seperate function. Outputs this:
    +-------------+-------+------------+------------+------------+------------+------------+----------------+---------------+
    | Player      |   £   | Gameweek 5 | Gameweek 4 | Gameweek 3 | Gameweek 2 | Gameweek 1 | 5 Week Average | Total Average |
    +-------------+-------+------------+------------+------------+------------+------------+----------------+---------------+
    | Nketiah     |  £5.7 |     2      |     2      |     5      |     5      |     8      |      4.4       |      4.5      |
    | Saka        |  £8.6 |     6      |     4      |     8      |     3      |     10     |      6.2       |      6.6      |
    +-------------+-------+------------+------------+------------+------------+------------+----------------+---------------+
    """
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
    """Given a team which is a list of 11 fpl player objects, the gameweek of the score that you want(GAMEWEEK IS 1 MINUS THE WEEK YOU WANT BECAUSE INDEXING STARTS AT 0), and a session to help fetch historical data. Returns the total score with the captain's score doubled. Uses the best possible captain in your team list"""
    total_score = 0
    highest_scorer = [0, "player"]
    for (
        player
    ) in team:  # continuously looks for best captain in team and adds everyone's score
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
    """Function takes in a list of a player's score and removes the score contributing the most to the standard deviation. Made to be used with ordered_best function such that if a player's list had a bad cv(aka very unpredictable) then removing a wack score would made the std more stable and thus more reliable to look at."""
    if len(player_scores) == 0:
        return []

    mean = statistics.mean(player_scores)

    index_to_remove = max(  # Finds highest contributing index to std
        range(len(player_scores)), key=lambda i: (player_scores[i] - mean) ** 2
    )

    del player_scores[index_to_remove]
    return player_scores


def cv(player_scores):
    """Takes in a list of player scores and returns the mean, std, and 1/cv as a tuple. The cv is std/mean"""
    if len(player_scores) == 0:
        return (0, 0, 0)

    mean = statistics.mean(player_scores)
    std = statistics.stdev(player_scores)

    if mean == 0 or std == 0:
        return (0, 0, 0)

    cv = std / mean

    if cv == 0:
        return (0, 0, 0)

    return (mean, std, 1 / cv)


def ordered_best_cv(list_of_player_lists):
    """Takes in a list of tuples in the form: [(player_scores_list,player_object),...]Used to try and find the best captain for the gameweek based on their average and cv. If cv is below 1 then that means their scores vary wildly and hopefully by removing the highest contributing std we get a more clear picture of that players true average. Returns an ordered list of the highest averaging scorers as objects."""
    cv_list = []
    for (player_scores) in (list_of_player_lists):  # Seeing if player cv is below 1, if it is it removes it and checks again. If it still is it discards it
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
    """Given a team which is a list of 11 fpl player objects, the gameweek of the score that you want(GAMEWEEK IS 1 MINUS THE WEEK YOU WANT BECAUSE INDEXING STARTS AT 0), and a session to help fetch historical data, and however many weeks in a row you want. Returns the total score with the captain's score doubled. Finds captain by looking at who averaged the most in the previous weeks."""  # COUROUTINE SO YOU CAN ONLY RETURN 1 AT A TIME
    total_score = 0
    for player in team:  # adding scores
        history = await fetch_player_history(session, player.id)
        total_score += history["history"][gameweek]["total_points"]
    history = await fetch_player_history(session, cap.id)
    total_score += history["history"][gameweek]["total_points"]
    return total_score


async def captain_points(cap, gameweek, session):
    """Given a team which is a list of 11 fpl player objects, the gameweek of the score that you want(GAMEWEEK IS 1 MINUS THE WEEK YOU WANT BECAUSE INDEXING STARTS AT 0), and a session to help fetch historical data, and however many weeks in a row you want. Returns captain's score. Uses the best possible captain in your team list."""
    history = await fetch_player_history(session, cap.id)
    captain_points = history["history"][gameweek]["total_points"]
    return captain_points


async def highest_average_scorer_captain_name(team, gameweek, session, in_a_row):
    """Given a team which is a list of 11 fpl player objects, the gameweek of the score that you want(GAMEWEEK IS 1 MINUS THE WEEK YOU WANT BECAUSE INDEXING STARTS AT 0), and a session to help fetch historical data, and however many weeks in a row you want. Returns best captain's name."""
    whole_team_list = []
    for player in team:  # fetching scores
        history = await fetch_player_history(session, player.id)
        list_of_scores = [
            history["history"][gameweek - i]["total_points"]
            for i in range(1, in_a_row + 1)
            if len(history["history"]) >= gameweek
        ]
        whole_team_list.append((list_of_scores, player))
    whole_team_list.sort(
        key=lambda x: statistics.mean(x[0]), reverse=True
    )  # Sorts team by highest average scorer
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
    """used to find the points of the best captain of those who returned consistently"""
    highest_scorer = [0, "player"]
    for _,player in player_achievement_dict.items():
        if gameweek == 11 and player.web_name == "Harrison": #For some reason API hasn't updated Harrison's data. Updated everyone else's though
            continue
        history = await fetch_player_history(session, player.id)
        if history["history"][gameweek]["total_points"] > highest_scorer[0]:
            highest_scorer = [history["history"][gameweek]["total_points"],player.web_name]
    return highest_scorer[0]


async def best_captain_name_finder(player_achievement_dict, gameweek, session):
    """used to find the name of the best captain of those who returned consistently"""
    highest_scorer = [0, "player"]
    for _,player in player_achievement_dict.items():
        if gameweek == 11 and player.web_name == "Harrison": #For some reason API hasn't updated Harrison's data. Updated everyone else's though
            continue
        history = await fetch_player_history(session, player.id)
        if history["history"][gameweek]["total_points"] > highest_scorer[0]:
            highest_scorer = [
                history["history"][gameweek]["total_points"],
                player.web_name,
            ]
    return highest_scorer[1]


async def list_of_consistent_players(players, gameweek, in_a_row, session, excused_weeks):
    """Function takes in all the players in the FPL, the gameweek to end at, and how many weeks in a row and returns all the players that returned consistently. Returns a list of player objects"""
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
    captain_object = ordered_best_cv(whole_team_list)[0]
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
            whole_team_list.append((possible_captain_score, player))
    whole_team_list.sort(key=lambda x: statistics.mean(x[0]), reverse=True)  # Sorts team by highest average scorer
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
    '''Given the inputs, it makes a predictive team and outputs its stats such the players in the team, points it got that week, captain, ect.'''
    new_all_ordered_times_added = []
    for _,player in player_achievement_dict.items():
        new_all_ordered_times_added.append(player)
    new_all_ordered_times_added.sort(key=lambda x: (float(x.points_per_game) ** 2 / x.now_cost),reverse=True)

    gimme_cap = await find_captain_at_beginning(
        new_all_ordered_times_added, gameweek, in_a_row, session
    )

    return await prep_team_data(new_all_ordered_times_added,gimme_cap,player_achievement_dict,gameweek,session,in_a_row)

async def points_average_team(player_achievement_dict, gameweek, session, in_a_row):
    new_all_ordered_times_added = []
    for _,player in player_achievement_dict.items():
        new_all_ordered_times_added.append(player)
    new_all_ordered_times_added.sort(key=lambda x: x.points_per_game,reverse=True)

    gimme_cap = await find_captain_at_beginning(
        new_all_ordered_times_added, gameweek, in_a_row, session
    )

    return await prep_team_data(new_all_ordered_times_added,gimme_cap,player_achievement_dict,gameweek,session,in_a_row)

async def pointsovertime_average_team(player_achievement_dict, gameweek, session, in_a_row):
    '''Team based on who averaged the highest over the past in_a_row gameweeks'''
    new_all_ordered_times_added = []
    for _,player in player_achievement_dict.items():
        new_all_ordered_times_added.append(player)
    whole_list = []
    for player in new_all_ordered_times_added:  # fetching scores
        history = await fetch_player_history(session, player.id)
        list_of_scores = [history["history"][gameweek - i]["total_points"] for i in range(1, in_a_row + 1) if len(history["history"]) >= gameweek]
        whole_list.append((list_of_scores,player))
    whole_list.sort(key=lambda x: statistics.mean(x[0]),reverse=True)

    new_all_ordered_times_added = [player[1] for player in whole_list]

    gimme_cap = await find_captain_at_beginning(
        new_all_ordered_times_added, gameweek, in_a_row, session
    )

    return await prep_team_data(new_all_ordered_times_added,gimme_cap,player_achievement_dict,gameweek,session,in_a_row)

async def pointsovertimecheap_average_team(player_achievement_dict, gameweek, session, in_a_row):
    '''Team based on who averaged the highest over the past in_a_row gameweeks'''
    new_all_ordered_times_added = []
    for _,player in player_achievement_dict.items():
        new_all_ordered_times_added.append(player)
    whole_list = []
    for player in new_all_ordered_times_added:  # fetching scores
        history = await fetch_player_history(session, player.id)
        list_of_scores = [history["history"][gameweek - i]["total_points"] for i in range(1, in_a_row + 1) if len(history["history"]) >= gameweek]
        whole_list.append((list_of_scores,player))
    whole_list.sort(key=lambda x: statistics.mean(x[0])**2 / x[1].now_cost,reverse=True)

    new_all_ordered_times_added = [player[1] for player in whole_list]

    gimme_cap = await find_captain_at_beginning(
        new_all_ordered_times_added, gameweek, in_a_row, session
    )

    return await prep_team_data(new_all_ordered_times_added,gimme_cap,player_achievement_dict,gameweek,session,in_a_row)




###CV CAPTAIN



async def cheap_cv_team(player_achievement_dict, gameweek, session, in_a_row):
    '''Given the inputs, it makes a predictive team and outputs its stats such the players in the team, points it got that week, captain, ect.'''
    new_all_ordered_times_added = []
    for _,player in player_achievement_dict.items():
        new_all_ordered_times_added.append(player)
    new_all_ordered_times_added.sort(key=lambda x: (float(x.points_per_game) ** 2 / x.now_cost),reverse=True)

    gimme_cap = await find_captain_with_cv(new_all_ordered_times_added, gameweek, in_a_row, session)

    return await prep_team_data(new_all_ordered_times_added,gimme_cap,player_achievement_dict,gameweek,session,in_a_row)

async def points_cv_team(player_achievement_dict, gameweek, session, in_a_row):
    new_all_ordered_times_added = []
    for _,player in player_achievement_dict.items():
        new_all_ordered_times_added.append(player)
    new_all_ordered_times_added.sort(key=lambda x: x.points_per_game,reverse=True)

    gimme_cap = await find_captain_with_cv(new_all_ordered_times_added, gameweek, in_a_row, session)

    return await prep_team_data(new_all_ordered_times_added,gimme_cap,player_achievement_dict,gameweek,session,in_a_row)

async def pointsovertime_cv_team(player_achievement_dict, gameweek, session, in_a_row):
    '''Team based on who averaged the highest over the past in_a_row gameweeks'''
    new_all_ordered_times_added = []
    for _,player in player_achievement_dict.items():
        new_all_ordered_times_added.append(player)
    whole_list = []
    for player in new_all_ordered_times_added:  # fetching scores
        history = await fetch_player_history(session, player.id)
        list_of_scores = [history["history"][gameweek - i]["total_points"] for i in range(1, in_a_row + 1) if len(history["history"]) >= gameweek]
        whole_list.append((list_of_scores,player))
    whole_list.sort(key=lambda x: statistics.mean(x[0]),reverse=True)

    new_all_ordered_times_added = [player[1] for player in whole_list]

    gimme_cap = await find_captain_with_cv(new_all_ordered_times_added, gameweek, in_a_row, session)

    return await prep_team_data(new_all_ordered_times_added,gimme_cap,player_achievement_dict,gameweek,session,in_a_row)

async def pointsovertimecheap_cv_team(player_achievement_dict, gameweek, session, in_a_row):
    '''Team based on who averaged the highest over the past in_a_row gameweeks'''
    new_all_ordered_times_added = []
    for _,player in player_achievement_dict.items():
        new_all_ordered_times_added.append(player)
    whole_list = []
    for player in new_all_ordered_times_added:  # fetching scores
        history = await fetch_player_history(session, player.id)
        list_of_scores = [history["history"][gameweek - i]["total_points"] for i in range(1, in_a_row + 1) if len(history["history"]) >= gameweek]
        whole_list.append((list_of_scores,player))
    whole_list.sort(key=lambda x: statistics.mean(x[0])**2 / x[1].now_cost,reverse=True)

    new_all_ordered_times_added = [player[1] for player in whole_list]

    gimme_cap = await find_captain_with_cv(new_all_ordered_times_added, gameweek, in_a_row, session)

    return await prep_team_data(new_all_ordered_times_added,gimme_cap,player_achievement_dict,gameweek,session,in_a_row)

###SALAH CAPTAIN
async def cheap_salah_team(player_achievement_dict, gameweek, session, in_a_row):
    '''Given the inputs, it makes a predictive team and outputs its stats such the players in the team, points it got that week, captain, ect.'''
    new_all_ordered_times_added = []
    for _,player in player_achievement_dict.items():
        new_all_ordered_times_added.append(player)
    new_all_ordered_times_added.sort(key=lambda x: (float(x.points_per_game) ** 2 / x.now_cost),reverse=True)

    salah = None
    for player in new_all_ordered_times_added:
        if player.web_name == 'Salah':
            salah = player
    if salah is None:
        for player in new_all_ordered_times_added:
            if player.web_name == 'Haaland':
                salah = player

    gimme_cap = salah

    return await prep_team_data(new_all_ordered_times_added,gimme_cap,player_achievement_dict,gameweek,session,in_a_row)

async def points_salah_team(player_achievement_dict, gameweek, session, in_a_row):
    new_all_ordered_times_added = []
    for _,player in player_achievement_dict.items():
        new_all_ordered_times_added.append(player)
    new_all_ordered_times_added.sort(key=lambda x: x.points_per_game,reverse=True)

    salah = None
    for player in new_all_ordered_times_added:
        if player.web_name == 'Salah':
            salah = player
    if salah is None:
        for player in new_all_ordered_times_added:
            if player.web_name == 'Haaland':
                salah = player

    gimme_cap = salah

    return await prep_team_data(new_all_ordered_times_added,gimme_cap,player_achievement_dict,gameweek,session,in_a_row)

async def pointsovertime_salah_team(player_achievement_dict, gameweek, session, in_a_row):
    '''Team based on who averaged the highest over the past in_a_row gameweeks'''
    new_all_ordered_times_added = []
    for _,player in player_achievement_dict.items():
        new_all_ordered_times_added.append(player)
    whole_list = []
    for player in new_all_ordered_times_added:  # fetching scores
        history = await fetch_player_history(session, player.id)
        list_of_scores = [history["history"][gameweek - i]["total_points"] for i in range(1, in_a_row + 1) if len(history["history"]) >= gameweek]
        whole_list.append((list_of_scores,player))
    whole_list.sort(key=lambda x: statistics.mean(x[0]),reverse=True)

    new_all_ordered_times_added = [player[1] for player in whole_list]

    salah = None
    for player in new_all_ordered_times_added:
        if player.web_name == 'Salah':
            salah = player
    if salah is None:
        for player in new_all_ordered_times_added:
            if player.web_name == 'Haaland':
                salah = player

    gimme_cap = salah

    return await prep_team_data(new_all_ordered_times_added,gimme_cap,player_achievement_dict,gameweek,session,in_a_row)

# async def pointsovertimecheap_cv_team(player_achievement_dict, gameweek, session, in_a_row):
#     '''Team based on who averaged the highest over the past in_a_row gameweeks'''
#     new_all_ordered_times_added = []
#     for _,player in player_achievement_dict.items():
#         new_all_ordered_times_added.append(player)
#     whole_list = []
#     for player in new_all_ordered_times_added:  # fetching scores
#         history = await fetch_player_history(session, player.id)
#         list_of_scores = [history["history"][gameweek - i]["total_points"] for i in range(1, in_a_row + 1) if len(history["history"]) >= gameweek]
#         whole_list.append((list_of_scores,player))
#     whole_list.sort(key=lambda x: statistics.mean(x[0])**2 / x[1].now_cost,reverse=True)

#     new_all_ordered_times_added = [player[1] for player in whole_list]

#     gimme_cap = await find_captain_with_cv(new_all_ordered_times_added, gameweek, in_a_row, session)

#     return await prep_team_data(new_all_ordered_times_added,gimme_cap,player_achievement_dict,gameweek,session,in_a_row)

async def main(gameweek, in_a_row, excused_weeks=0):
    """Main function that is run. Pass in gameweek you want, how many weeks in a row, and how many excused gameweeks you want and does what I want"""
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
    connector = aiohttp.TCPConnector(ssl=False)  # Creates a connector object that allows a base for a connection. ssl=false allows for no encryption
    async with aiohttp.ClientSession(connector=connector) as session:  # creates session with connector.
        players = await fetch_players(session)
        # list_of_players = await list_of_consistent_players(players, gameweek, in_a_row, session, excused_weeks)
        player_achievement_dicts = {}
        start = time.time()
        async for player in  list_of_consistent_players(players, gameweek, in_a_row, session, excused_weeks):
            player_achievement_dicts[player[0].web_name] = player
        print(time.time() - start)
        print('*********************')
        # player_achievement_dict = create_dictionary(list_of_players)
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
        ####CHEAP
        (final_team,total_gameweek_points,best_captain_points,best_captain_name,average_scorer_captain_name,average_scorer_captain_points,total_cost,) = await cheap_average_team(player_achievement_dict, gameweek, session, in_a_row)
        
        total_points += total_gameweek_points
        average_cost.append(total_cost)

        print_data(final_team,total_gameweek_points,best_captain_points,best_captain_name,average_scorer_captain_name,average_scorer_captain_points,total_cost,gameweek,in_a_row,excused_weeks,total_points,average_cost)

        ##########EXPENSIVE TEAM
        (final_team,total_gameweek_points,best_captain_points,best_captain_name,average_scorer_captain_name,average_scorer_captain_points,total_cost) = await points_average_team(player_achievement_dict, gameweek, session, in_a_row)
        total_points_1 += total_gameweek_points
        average_cost_1.append(total_cost)
        print_data(final_team,total_gameweek_points,best_captain_points,best_captain_name,average_scorer_captain_name,average_scorer_captain_points,total_cost,gameweek,in_a_row,excused_weeks,total_points_1,average_cost_1)

        #####POINTS OVER TIME
        (final_team,total_gameweek_points,best_captain_points,best_captain_name,average_scorer_captain_name,average_scorer_captain_points,total_cost) = await pointsovertime_average_team(player_achievement_dict, gameweek, session, in_a_row)
        total_points_2 += total_gameweek_points
        average_cost_2.append(total_cost)
        print_data(final_team,total_gameweek_points,best_captain_points,best_captain_name,average_scorer_captain_name,average_scorer_captain_points,total_cost,gameweek,in_a_row,excused_weeks,total_points_2,average_cost_2)

        #####POINTS OVER TIME CHEAP
        (final_team,total_gameweek_points,best_captain_points,best_captain_name,average_scorer_captain_name,average_scorer_captain_points,total_cost) = await pointsovertimecheap_average_team(player_achievement_dict, gameweek, session, in_a_row)
        total_points_3 += total_gameweek_points
        average_cost_3.append(total_cost)
        print_data(final_team,total_gameweek_points,best_captain_points,best_captain_name,average_scorer_captain_name,average_scorer_captain_points,total_cost,gameweek,in_a_row,excused_weeks,total_points_3,average_cost_3)

        #####CHEAP WITH CV CAPTAIN 
        (final_team,total_gameweek_points,best_captain_points,best_captain_name,average_scorer_captain_name,average_scorer_captain_points,total_cost) = await cheap_cv_team(player_achievement_dict, gameweek, session, in_a_row)
        total_points_4 += total_gameweek_points
        average_cost_4.append(total_cost)
        print_data(final_team,total_gameweek_points,best_captain_points,best_captain_name,average_scorer_captain_name,average_scorer_captain_points,total_cost,gameweek,in_a_row,excused_weeks,total_points_4,average_cost_4)

        ##########EXPENSIVE TEAM CV CAPTAIN
        (final_team,total_gameweek_points,best_captain_points,best_captain_name,average_scorer_captain_name,average_scorer_captain_points,total_cost) = await points_cv_team(player_achievement_dict, gameweek, session, in_a_row)
        total_points_5 += total_gameweek_points
        average_cost_5.append(total_cost)
        print_data(final_team,total_gameweek_points,best_captain_points,best_captain_name,average_scorer_captain_name,average_scorer_captain_points,total_cost,gameweek,in_a_row,excused_weeks,total_points_5,average_cost_5)

        #####POINTS OVER TIME WITH CV
        (final_team,total_gameweek_points,best_captain_points,best_captain_name,average_scorer_captain_name,average_scorer_captain_points,total_cost) = await pointsovertime_cv_team(player_achievement_dict, gameweek, session, in_a_row)
        total_points_6 += total_gameweek_points
        average_cost_6.append(total_cost)
        print_data(final_team,total_gameweek_points,best_captain_points,best_captain_name,average_scorer_captain_name,average_scorer_captain_points,total_cost,gameweek,in_a_row,excused_weeks,total_points_6,average_cost_6)

        #####POINTS OVER TIME CHEAP WITH CV
        (final_team,total_gameweek_points,best_captain_points,best_captain_name,average_scorer_captain_name,average_scorer_captain_points,total_cost) = await pointsovertimecheap_cv_team(player_achievement_dict, gameweek, session, in_a_row)
        total_points_7 += total_gameweek_points
        average_cost_7.append(total_cost)
        print_data(final_team,total_gameweek_points,best_captain_points,best_captain_name,average_scorer_captain_name,average_scorer_captain_points,total_cost,gameweek,in_a_row,excused_weeks,total_points_7,average_cost_7)

        ####CHEAP WITH SALAH
        (final_team,total_gameweek_points,best_captain_points,best_captain_name,average_scorer_captain_name,average_scorer_captain_points,total_cost,) = await cheap_salah_team(player_achievement_dict, gameweek, session, in_a_row)
        
        total_points_8 += total_gameweek_points
        average_cost_8.append(total_cost)

        print_data(final_team,total_gameweek_points,best_captain_points,best_captain_name,average_scorer_captain_name,average_scorer_captain_points,total_cost,gameweek,in_a_row,excused_weeks,total_points_8,average_cost_8)

        ##########EXPENSIVE TEAM WITH SALAH
        (final_team,total_gameweek_points,best_captain_points,best_captain_name,average_scorer_captain_name,average_scorer_captain_points,total_cost) = await points_salah_team(player_achievement_dict, gameweek, session, in_a_row)
        total_points_9 += total_gameweek_points
        average_cost_9.append(total_cost)
        print_data(final_team,total_gameweek_points,best_captain_points,best_captain_name,average_scorer_captain_name,average_scorer_captain_points,total_cost,gameweek,in_a_row,excused_weeks,total_points_9,average_cost_9)

if __name__ == "__main__":
    if sys.version_info >= (3, 7):
        loop = asyncio.get_event_loop()

        for i in range(5, 12):
            loop.run_until_complete(main(i, 5, 2))

