from datetime import datetime

import pandas as pd

allowed_tags = [
    "challenge",
    "accuracy",
    "speed",
    "tech"
    "poodle",
    # "fitness",
    "balanced",
    # "dance",
]

def load_dataset(ranked=False):
    data = pd.read_csv("./dataset/bs_scoring_dataset_76561198274713084.csv")

    if ranked:
        data = data[data["pp"] > 0]

    data = data[data["accuracy"] < 200]

    data["timeSet"] = pd.to_datetime(data["timeSet"], utc=True)
    data = data[data["timeSet"] < pd.Timestamp("2024-03-01", tz="UTC")]
    data = data[data["timeSet"] > pd.Timestamp("2020-12-01", tz="UTC")]

    ct = 0
    map_tags = []

    for tags_list in data["tags"]:
        map_tag = None

        if pd.notna(tags_list):
            tags_list = str(tags_list)
            tags_list = tags_list.replace("[", "").replace("]", "").replace("'", "")
            tags = [t.strip() for t in tags_list.split(",")]

            for tag in tags:
                for allowed_tag in allowed_tags:
                    if tag == allowed_tag:
                        ct += 1
                        map_tag = tag
                        break
                if map_tag is not None:
                    break

        map_tags.append(map_tag)

    data["map_tag"] = map_tags
    print("Found " + str(ct) + " Maps with Tags")

    print("Loaded Dataset with the shape: " + str(data.shape))
    return data