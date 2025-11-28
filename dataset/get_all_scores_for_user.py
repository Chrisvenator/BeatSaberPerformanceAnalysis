import os
import traceback

import requests
import re, json
from ftfy import fix_text


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
    except Exception:
        print(traceback.format_exc())

        # Create a new directory and write the faulty code there. Helps with debugging
        os.makedirs("./.error", exist_ok=True)
        with open("./.error/latest.json", "w") as f:
            f.write(str(resp))
        exit(1)
    return resp


def make_request(baseURL, playerID, limit, sortBy, page):
    url = baseURL + "/" + str(playerID) + "/scores?limit=" + str(limit) + "&sort=" + sortBy + "&page=" + str(page)
    print(url)
    response = requests.get(url)
    if response.status_code == 200:
        if not response.json()["playerScores"]:
            return None
        else:
            return clean_json(str(response.json()["playerScores"]))
    else:
        return None


def save_all_scores_for_user(player_id, player_scores_file_location):
    base_url = "https://scoresaber.com/api/player"
    limit = 10
    sort_by = "recent"
    page = 1

    successful_last_request = True
    while successful_last_request:
        req = make_request(base_url, player_id, limit, sort_by, page)
        if req is None:
            successful_last_request = False
            print("Reached end of scores at page: " + str(page))
        else:
            with open(player_scores_file_location + str(player_id) + "-" + str(page) + ".json", "w") as f:
                f.write(str(req))
            page += 1
        # break


def read_file(player_id, player_scores_file_location, page):
    with open(player_scores_file_location + str(player_id) + "-" + str(page) + ".json", "r") as f:
        print(f.name)
        f = json.load(f)
        return f


def merge_all_scores_for_user(player_id, player_scores_file_location):
    all_scores = read_file(player_id, player_scores_file_location, 1)
    page = 2
    while os.path.exists(player_scores_file_location + str(player_id) + "-" + str(page) + ".json"):
        file = read_file(player_id, player_scores_file_location, page)
        all_scores = all_scores + file
        page += 1

    with open(player_scores_file_location + str(player_id) + ".json", "w") as f:
        f.write(json.dumps(all_scores, indent=2))
    return all_scores


def get_scores_for(player_id):
    player_scores_file_location = "./scores/" + str(player_id) + "/"
    os.makedirs(player_scores_file_location, exist_ok=True)

    save_all_scores_for_user(player_id, player_scores_file_location)
    merge_all_scores_for_user(player_id, player_scores_file_location)

if __name__ == "__main__":
    get_scores_for(76561198274713084)
