import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from dataset.load_dataset import load_dataset


def create_maps_acc_graph():
    df = load_dataset(True)
    print(df.shape)

    x_values = np.arange(0, 13, 0.5)
    x_labels = [f"{v}★" for v in x_values]

    fig, ax = plt.subplots(figsize=(12, 6))
    plt.xticks(x_values, x_labels)

    # (Label, y0, y1, Farbe)
    ranges = [
        ("SSS", 1.00, 1.00, "#FF0000"),
        ("SS",  0.90, 1.00, "#00E5FF"),
        ("S",   0.80, 0.90, "#FFD700"),
        ("A",   0.65, 0.80, "#4CAF50"),
        ("B",   0.50, 0.65, "#2196F3"),
        ("C",   0.35, 0.50, "#673AB7"),
        ("D",   0.20, 0.35, "#FF9800"),
        ("E",   0.00, 0.20, "#F44336"),
    ]

    min_acc = df["accuracy"].min()
    # Ranges filtern, die komplett unterhalb der Daten liegen
    ranges = [r for r in ranges if r[2] >= min_acc]

    # farbige Bereiche zeichnen
    for label, y0, y1, color in ranges:
        ax.axhspan(y0, y1, color=color, alpha=0.25)

    # Scatter
    df.plot.scatter(
        x="stars",
        y="accuracy",
        c=df["weighted_pp"],
        ax=ax
    )

    ax.tick_params(axis='x', labelrotation=30)
    ax.grid()

    # zweite y-Achse für Ranks
    ax2 = ax.twinx()
    ax2.set_ylim(ax.get_ylim())  # gleiche Skala

    # Ticks in die Mitte der Bereiche setzen
    tick_pos = [(y0 + y1) / 2 for (_, y0, y1, _) in ranges]
    tick_labels = [label for (label, _, _, _) in ranges]

    ax2.set_yticks(tick_pos)
    ax2.set_yticklabels(tick_labels)

    for tick, (_, y0, y1, color) in zip(ax2.get_yticklabels(), ranges):
        tick.set_color(color)
        tick.set_fontweight("bold")

    plt.show()



def __main__():
    create_maps_acc_graph()


if __name__ == "__main__":
    __main__()
