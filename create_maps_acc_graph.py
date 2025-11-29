import matplotlib.pyplot as plt
import pandas as pd

from dataset.load_dataset import load_dataset


def create_maps_acc_graph():
    df = load_dataset(True)
    print(df.shape)

    df.plot.scatter(
        x="stars",
        y="accuracy",
        # s=df["weighted_pp"],
        c=df["weighted_pp"]
    )

    plt.show()


def __main__():
    create_maps_acc_graph()


if __name__ == "__main__":
    __main__()
