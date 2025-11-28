import ast
import json
import os

import requests

from get_all_scores_for_user import clean_json


def load_player_json(player_scores_file_location):
    with open(player_scores_file_location, "r") as f:
        print("loaded " + f.name)
        f = json.load(f)
        return f


def extract_map_hashes(scores):
    hashes = []
    for score in scores:
        hashes.append(score["leaderboard"]["songHash"])
    print("loaded " + str(len(hashes)) + " map hashes")
    return hashes


def get_and_save_maps_from_beatsaver_by_hashes(url, map_hashes, map_info_file_location):
    maps = []
    missing = 0
    print(map_hashes)
    for map_hash in map_hashes:
        response = requests.get(url + map_hash)
        if response.status_code == 200:
            if not response.json():
                return None
            else:
                found_hash = False
                for version in response.json()["versions"]:
                    if version["hash"].upper() == map_hash.upper():
                        save_map_info(clean_json(str(version)), map_hash, map_info_file_location)
                        found_hash = True

                if not found_hash:
                    print("Could not find hash \"" + map_hash.upper() + "\" in " + response.json()["id"])
                    save_map_info(clean_json(str(response.json())), response.json()["id"], map_info_file_location + "/missing")
                    missing += 1
    print("Maps with a wrong hash: " + str(missing))
    return maps


def save_map_info(beatmap, id, map_info_file_location):
    print("saving " + id + "...")
    with open(map_info_file_location + "/" + id + ".json", "w") as f:
        f.write(str(beatmap))


def get_maps_for_player_id(player_id):
    page = ""  ## To load all scores, use "". To load 10 maps, use "-1" or "-2", ... "-n" based on the user scores pages.

    beatsaver_api_hashes_map_info_url = "https://api.beatsaver.com/maps/hash/"

    player_scores_file_location = "./scores/" + str(player_id) + "/" + str(player_id) + page + ".json"
    map_info_file_location = "./map_infos/"

    # idk why, but when running this script directly, I need /dataset in front. But when running from main, I only need /scores...
    if not os.path.exists(player_scores_file_location):
        player_scores_file_location = "./dataset/scores/" + str(player_id) + "/" + str(player_id) + page + ".json"
        map_info_file_location = "./dataset/map_infos/"

        if not os.path.exists(player_scores_file_location):
            raise ValueError("Path to file does not exist! Please get all user scores beforehand.")

    os.makedirs(map_info_file_location, exist_ok=True)

    player_json = load_player_json(player_scores_file_location)
    map_hashes = extract_map_hashes(player_json)
    get_and_save_maps_from_beatsaver_by_hashes(beatsaver_api_hashes_map_info_url, map_hashes, map_info_file_location)


if __name__ == "__main__":
    get_maps_for_player_id(76561198274713084)
