import csv
import json

import pandas as pd

import config
from dataset.config import csv_file_path
from dataset.get_all_scores_for_user import load_player_scores, write_error
from dataset.load_dataset import load_dataset


def load_map_info(map_hash, verbose=True):
    with open(config.map_info_file_location + map_hash.upper() + ".json", "r") as f:
        if verbose:
            print("loaded " + f.name)
        f = json.load(f)
        return f


def create_dataset():
    data = []
    scores = load_player_scores("")[0]
    map_info = load_map_info(scores["leaderboard"]["songHash"])

    score_keys = [key for key in scores["score"]]  # score
    score_keys.remove("leaderboardPlayerInfo")
    score_keys.remove("hmd")
    score_keys.remove("hasReplay")
    score_keys.remove("deviceControllerLeft")
    score_keys.remove("deviceControllerRight")
    score_keys.remove("id")
    score_keys.remove("deviceHmd")
    leaderboard_keys = [key for key in scores["leaderboard"]]  # leaderboard
    leaderboard_keys.remove("createdDate")
    leaderboard_keys.remove("lovedDate")
    leaderboard_keys.remove("difficulty")
    leaderboard_keys.remove("difficulties")
    leaderboard_keys.remove("songHash")
    leaderboard_keys.remove("dailyPlays")
    leaderboard_keys.remove("playerScore")
    leaderboard_keys.remove("id")
    difficulty_keys = [key for key in scores["leaderboard"]["difficulty"]]  # difficulty
    difficulty_keys.remove("leaderboardId")
    difficulty_keys.remove("difficulty")
    difficulty_keys.remove("gameMode")
    difficulty_keys.remove("difficultyRaw")

    map_info_keys = [key for key in map_info]
    map_info_keys.remove("diffs")
    map_info_keys.remove("state")
    map_info_keys.remove("downloadURL")
    map_info_keys.remove("coverURL")
    map_info_keys.remove("previewURL")
    map_info_keys.remove("id")
    map_info_keys.remove("name")
    map_info_keys.remove("metadata")
    map_info_keys.remove("plays")
    map_info_keys.remove("downloads")
    map_info_keys.remove("uploaded")
    map_info_keys.remove("updatedAt")
    map_info_keys.remove("lastPublishedAt")
    map_info_keys.remove("description")
    map_info_keys.remove("uploader")

    diffs_keys = [key for key in map_info["diffs"][0]]
    diffs_keys.remove("paritySummary")
    diffs_keys.remove("environment")
    diffs_keys.remove("difficulty")
    parity_summary_keys = [key for key in map_info["diffs"][0]["paritySummary"]]

    data.append(
        score_keys +
        leaderboard_keys +
        difficulty_keys +
        map_info_keys +
        diffs_keys +
        parity_summary_keys +
        ["weighted_pp"] +  # add header row + extra column for weighted pp
        ["accuracy"] +
        ["tags"] +
        ["beatsaver_id"]
    )

    scores = load_player_scores("")
    i = 0
    for score in scores:
        i += 1
        print("Iteration: " + str(i))
        try:
            map_info = load_map_info(score["leaderboard"]["songHash"], False)
        except:
            print("Did not find Map " + score["leaderboard"]["songHash"] + ". Skipping...")
            continue

        score_values = [score["score"].get(k) for k in score_keys]
        leaderboard_values = [score["leaderboard"].get(k) for k in leaderboard_keys]
        difficulty_values = [score["leaderboard"]["difficulty"].get(k) for k in difficulty_keys]

        map_info_values = [map_info.get(k) for k in map_info_keys]
        diffs = [
            map_info["diffs"][i]
            for i in range(len(map_info["diffs"]))
            if (
                    ("_" + map_info["diffs"][i]["difficulty"] + "_") in score["leaderboard"]["difficulty"]["difficultyRaw"]
                    and map_info["diffs"][i]["characteristic"] in score["leaderboard"]["difficulty"]["difficultyRaw"]
            )
        ]
        if len(diffs) != 1:
            print("WARNING! There was something wrong! There are multiple diffs with the same name(?). Skipping...")
            continue

        diffs = diffs[0]
        diffs_values = [diffs.get(k) for k in diffs_keys]
        parity_summary_values = [diffs["paritySummary"].get(k) for k in parity_summary_keys]

        # compute weighted pp = pp + weight
        pp = score["score"].get("pp") or 0
        weight = score["score"].get("weight") or 0
        weighted_pp = pp * weight

        base_score = score["score"].get("baseScore") or 0
        max_score = score["leaderboard"].get("maxScore") or 1
        accuracy = base_score / max_score

        tags = map_info.get("tags") or ""

        beatsaver_id = map_info.get("id")

        data.append(
            score_values +
            leaderboard_values +
            difficulty_values +
            map_info_values +
            diffs_values +
            parity_summary_values +
            [weighted_pp] +
            [accuracy] +
            [tags] +
            [beatsaver_id]
        )

    with open(csv_file_path, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(data)

    print("Successfully created and saved Dataset.")
    df = pd.read_csv(csv_file_path)
    print("Stats:")
    print(df.dtypes)
    print(df.shape)


if __name__ == "__main__":
    create_dataset()
