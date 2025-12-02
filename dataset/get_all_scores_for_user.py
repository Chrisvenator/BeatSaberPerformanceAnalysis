import os
import traceback

import requests
import re, json
import config

def write_error(msg):
    os.makedirs("./.error", exist_ok=True)
    with open("./.error/latest.json", "w") as f:
        f.write(str(msg))


def load_player_scores(page=""):
    ## To load all scores, use "". To load 10 maps, use "-1" or "-2", ... "-n" based on the user scores pages.
    player_scores_file_location = config.player_scores_file_location + str(config.player_id) + page + ".json"

    # idk why, but when running this script directly, I need /dataset in front. But when running from main, I only need /scores...
    if not os.path.exists(player_scores_file_location):
        player_scores_file_location = "./dataset/scores/" + str(config.player_id) + "/" + str(config.player_id) + page + ".json"
        map_info_file_location = "./dataset/map_infos/"

        if not os.path.exists(player_scores_file_location):
            raise ValueError("Path to file does not exist! Please get all user scores beforehand.")

    with open(player_scores_file_location, "r") as f:
        print("loaded " + f.name)
        f = json.load(f)
        return f


def fix_known_mojibake(s):
    # common mishandled UTF-8 sequences
    replacements = {
        "â\\x99¡": "♥",
        "â\\x99¥": "♥",
        "â\\x99": "♥",  # fallback
    }
    for bad, good in replacements.items():
        s = s.replace(bad, good)
    return s


def clean_json(resp):
    # Convert dict keys wrapped in single quotes
    resp = re.sub(r"'(\w+)'(?=\s*:)", r'"\1"', resp)

    # Convert single-quoted string values, ignoring escaped \'
    # Match: : ' ... '
    # Where the final ' is NOT preceded by a backslash
    resp = re.sub(
        r":\s*'((?:[^'\\]|\\.)*)'(?!')",
        lambda m: ': "' + m.group(1).replace('"', r'\"').replace("\\'", "'") + '"',
        resp
    )

    # Replace arrays with single-quoted items → double-quoted items
    # like ['accuracy'] -> ["accuracy"] or ['hardcore', 'balanced', 'speed', 'electronic']
    resp = re.sub(
        r"\[\s*(?:'[^']*'(?:\s*,\s*'[^']*')*)\s*\]",
        lambda m: "[" + ", ".join(
            '"' + item.strip()[1:-1].replace('"', r'\"') + '"'
            for item in m.group(0).strip()[1:-1].split(",")
        ) + "]",
        resp
    )

    # Python literal → JSON literal
    resp = resp.replace("None", "null")
    resp = resp.replace("True", "true")
    resp = resp.replace("False", "false")

    resp = fix_known_mojibake(resp)

    try:
        resp = json.loads(resp)
        resp = json.dumps(resp, indent=2)
        return resp
    except Exception:
        print("CAUGHT IN clean_json")
        print(traceback.format_exc())
        write_error(resp) # Create a new directory and write the faulty code there. Helps with debugging
        return ""


def make_request(baseURL, playerID, limit, sortBy, page):
    url = baseURL + "/" + str(playerID) + "/scores?limit=" + str(limit) + "&sort=" + sortBy + "&page=" + str(page)
    print(url)
    response = requests.get(url)
    if response.status_code == 200:
        if not response.json()["playerScores"]:
            return None
        else:
            req = str(response.json()["playerScores"])
            # Save raw data for a Data Quality analysis
            if config.save_raws:
                with open(config.raw_data_file_location + str(config.player_id) + "-" + str(page) + ".json", "w") as f:
                    f.write(str(req))

            return clean_json(req)
    else:
        return None


def save_all_scores_for_user():
    limit = 10
    sort_by = "recent"
    page = 1

    successful_last_request = True
    while successful_last_request:
        req = make_request(config.score_saber_base_url, config.player_id, limit, sort_by, page)
        if req is None:
            successful_last_request = False
            print("Reached end of scores at page: " + str(page))
        elif req == "":
            continue
        else:
            with open(config.player_scores_file_location + str(config.player_id) + "-" + str(page) + ".json", "w") as f:
                f.write(str(req))
            page += 1
        # break


def read_file(page):
    with open(config.player_scores_file_location + str(config.player_id) + "-" + str(page) + ".json", "r") as f:
        print(f.name)
        f = json.load(f)
        return f


def merge_all_scores_for_user():
    all_scores = read_file(1)
    page = 2
    while os.path.exists(config.player_scores_file_location + str(config.player_id) + "-" + str(page) + ".json"):
        file = read_file(page)
        all_scores = all_scores + file
        page += 1

    with open(config.player_scores_file_location + str(config.player_id) + ".json", "w") as f:
        f.write(json.dumps(all_scores, indent=2))
    return all_scores


def get_scores_for_player_id():
    os.makedirs(config.player_scores_file_location, exist_ok=True)

    print("Getting scores from ScoreSaber...")
    save_all_scores_for_user()
    merge_all_scores_for_user()

if __name__ == "__main__":
    get_scores_for_player_id()
