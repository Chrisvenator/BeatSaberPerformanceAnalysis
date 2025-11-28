import ast
import json
import os

import requests

from dataset import config
from get_all_scores_for_user import clean_json, load_player_scores


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
                    os.makedirs(map_info_file_location + "missing", exist_ok=True)
                    print("Could not find hash \"" + map_hash.upper() + "\" in " + response.json()["id"])
                    save_map_info(clean_json(str(response.json())), response.json()["id"], map_info_file_location + "missing")
                    missing += 1
    print("Maps with a wrong hash: " + str(missing))
    return maps


def save_map_info(beatmap, id, map_info_file_location):
    print("saving " + id + "...")
    with open(map_info_file_location + "/" + id + ".json", "w") as f:
        f.write(str(beatmap))


def get_maps_for_player_id():

    os.makedirs(config.map_info_file_location, exist_ok=True)

    player_json = load_player_scores()
    map_hashes = extract_map_hashes(player_json)
    get_and_save_maps_from_beatsaver_by_hashes(config.beatsaver_api_hashes_map_info_url, map_hashes, config.map_info_file_location)


if __name__ == "__main__":
    get_maps_for_player_id()
