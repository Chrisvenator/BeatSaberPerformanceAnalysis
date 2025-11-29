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
    missing = 0
    maps = []

    i = 0

    for map_hash in map_hashes:
        i += 1

        # file_path = os.path.join(map_info_file_location, map_hash + ".json")
        # if os.path.exists(file_path):
        #     print("Already have " + map_hash + ", skipping download...")
        #     continue

        response = requests.get(url + map_hash)
        if response.status_code == 200:
            data = response.json()
            if not data:
                return None

            found_hash = False
            for version in data.get("versions", []):
                if version["hash"].upper() == map_hash.upper():
                    found_hash = True

                    # Flatten the versions list
                    flattened = {
                        k: v
                        for k, v in data.items()
                        if k != "versions"
                    }

                    # Merge the chosen version into the root
                    flattened.update(version)

                    # Now flatten stats (if present)
                    stats = flattened.pop("stats", None)
                    if isinstance(stats, dict):
                        for k, v in stats.items():
                            flattened[k] = v
                    print(str(i) + ": saving " + map_hash + "...")

                    save_map_info(
                        clean_json(json.dumps(flattened)),
                        map_hash,
                        map_info_file_location
                    )

                    # Save a duplicate of the raw data for further data quality analysis
                    if config.save_raws:
                        save_map_info(str(data), map_hash, config.raw_data_file_location)

            if not found_hash:
                os.makedirs(map_info_file_location + "missing", exist_ok=True)
                print("Could not find hash \"" + map_hash.upper() + "\" in " + response.json()["id"])
                save_map_info(clean_json(str(data)), data["id"], map_info_file_location + "missing")
                missing += 1
    print("Maps with a wrong hash: " + str(missing))
    return maps


def save_map_info(beatmap, id, map_info_file_location):
    with open(map_info_file_location + "/" + id + ".json", "w") as f:
        f.write(str(beatmap))


def get_maps_for_player_id():
    os.makedirs(config.map_info_file_location, exist_ok=True)

    player_json = load_player_scores()
    map_hashes = extract_map_hashes(player_json)
    get_and_save_maps_from_beatsaver_by_hashes(config.beatsaver_api_hashes_map_info_url, map_hashes, config.map_info_file_location)


if __name__ == "__main__":
    get_maps_for_player_id()
