import pandas as pd


def load_dataset(ranked=False):
    data = pd.read_csv("./dataset/bs_scoring_dataset_76561198274713084.csv")
    if ranked:
        data = data[data["pp"] > 0]
    print("Loaded Dataset with the shape: " + str(data.shape))
    return data