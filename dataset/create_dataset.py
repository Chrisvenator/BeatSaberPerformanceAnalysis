import csv
import json

import config
from dataset.config import csv_file_path
from dataset.get_all_scores_for_user import load_player_scores, write_error


def load_map_info(map_hash, verbose=True):
    with open(config.map_info_file_location + map_hash.upper() + ".json", "r") as f:
        if verbose:
            print("loaded " + f.name)
        f = json.load(f)
        return f


def create_csv():
    data = []
    scores = load_player_scores("")[0]
    map_info = load_map_info(scores["leaderboard"]["songHash"])

    score_keys = ([key for key in scores["score"]])  # score
    leaderboard_keys = ([key for key in scores["leaderboard"]])  # leaderboard
    leaderboard_keys.remove("difficulty")
    difficulty_keys = ([key for key in scores["leaderboard"]["difficulty"]])  # difficulty

    map_info_keys = [key for key in map_info]
    map_info_keys.remove("diffs")
    diffs_keys = [key for key in map_info["diffs"][0]]
    diffs_keys.remove("paritySummary")
    parity_summary_keys = [key for key in map_info["diffs"][0]["paritySummary"]]

    data.append(
        score_keys +
        leaderboard_keys +
        difficulty_keys +
        map_info_keys +
        diffs_keys +
        parity_summary_keys
    )

    scores = load_player_scores("")
    i = 0
    for score in scores:
        i+=1
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
        diffs_2 = [
            map_info["diffs"][i]
            for i in range(len(map_info["diffs"]))
            if (
                    (map_info["diffs"][i]["difficulty"]) in score["leaderboard"]["difficulty"]["difficultyRaw"]
                    and map_info["diffs"][i]["characteristic"] in score["leaderboard"]["difficulty"]["difficultyRaw"]
            )
        ]
        if len(diffs) != 1:
            write_error(diffs)
            exit(10)
        diffs = diffs[0]
        diffs_values = [diffs.get(k) for k in diffs_keys]
        parity_summary_values = [diffs["paritySummary"].get(k) for k in  parity_summary_keys]

        data.append(
            score_values +
            leaderboard_values +
            difficulty_values +
            map_info_values +
            diffs_values +
            parity_summary_values
        )

    with open(csv_file_path, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(data)



def create_dataset():
    create_csv()


if __name__ == "__main__":
    create_dataset()
