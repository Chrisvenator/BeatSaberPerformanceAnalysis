
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd

from matplotlib.ticker import FuncFormatter
from dataset.load_dataset import load_dataset


def create_maps_acc_graph():
    df = load_dataset(False)
    print(df.shape)

    x_values = np.arange(0, 13, 0.5)
    x_labels = [f"{v}★" for v in x_values]

    fig, ax = plt.subplots(figsize=(12, 6))
    plt.xticks(x_values, x_labels)

    # (Label, y0, y1, Farbe)
    ranges = [
        ("SSS", 1.00, 1.00, "#FF0000"),
        ("SS", 0.90, 1.00, "#00FFFF"),
        ("S", 0.80, 0.90, "#32c7b7"),
        ("A", 0.65, 0.80, "#4CAF50"),
        ("B", 0.50, 0.65, "#d9ac26"),
        ("C", 0.35, 0.50, "#d67028"),
        ("D", 0.20, 0.35, "#c42c2c"),
        ("E", 0.00, 0.20, "#470101"),
    ]


    min_acc = df["accuracy"].min()
    ranges = [r for r in ranges if r[2] >= min_acc]

    # convert ranges to percent
    ranges_pct = [(label, y0 * 100, y1 * 100, color) for (label, y0, y1, color) in ranges]

    # draw color bands
    for label, y0, y1, color in ranges_pct:
        ax.axhspan(y0, y1, color=color, alpha=0.25)

    df["accuracy_pct"] = df["accuracy"] * 100

    df["map_tag_cat"] = df["map_tag"].astype("category")
    codes = df["map_tag_cat"].cat.codes

    # keep only rows where code != -1 (meaning valid tag)
    mask = codes != -1
    df = df[mask]
    codes = codes[mask]  # keep codes aligned with df

    ax.scatter(
        df["timeSet"],
        df["accuracy_pct"],
        c=codes,
        cmap="inferno",
        s=10,
        zorder=2
    )

    handles = []
    labels = df["map_tag"].astype("category").cat.categories

    for i, lab in enumerate(labels):
        handles.append(plt.Line2D([], [], marker="o", linestyle="",
                                  color=plt.cm.inferno(i / (len(labels) - 1))))
    ax.legend(handles, labels, title="map_tag")


    plt.title("Player Performance Across Beat Saber Map Genres over Time")
    plt.xlabel("Date Score set")
    plt.ylabel("Accuracy (%)")

    # convert time to numeric
    df["t_sec"] = (df["timeSet"] - df["timeSet"].min()).dt.total_seconds()

    # numeric time
    df["t_sec"] = (df["timeSet"] - df["timeSet"].min()).dt.total_seconds()

    # use the same colormap as the scatter
    cmap = plt.cm.plasma
    codes = df["map_tag_cat"].cat.codes
    tags = df["map_tag_cat"].cat.categories

    for code_val, tag in enumerate(tags):
        sub = df[df["map_tag"] == tag]

        if len(sub) < 5:
            continue

        t = sub["t_sec"]
        y = sub["accuracy_pct"]

        coef = np.polyfit(t, y, 6)
        poly = np.poly1d(coef)

        t_vals = np.linspace(t.min(), t.max(), 300)
        date_vals = df["timeSet"].min() + pd.to_timedelta(t_vals, unit="s")

        ax.plot(
            date_vals,
            poly(t_vals),
            linewidth=2,
            color=cmap(code_val / (len(tags) - 1)),
            label=f"{tag} trend",
            zorder=3
        )

    # zweite y-Achse für Ranks
    ax2 = ax.twinx()
    ax2.set_ylim(ax.get_ylim())  # gleiche Skala

    # Ticks in die Mitte der Bereiche setzen
    tick_pos = [(y0 + y1) / 2 for (_, y0, y1, _) in ranges_pct]
    tick_labels = [label for (label, _, _, _) in ranges_pct]

    ax2.set_yticks(tick_pos)
    ax2.set_yticklabels(tick_labels)

    for tick, (_, y0, y1, color) in zip(ax2.get_yticklabels(), ranges_pct):
        tick.set_color(color)
        tick.set_fontweight("bold")

    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, pos: f"{v:.0f}%"))

    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")



    plt.show()


def __main__():
    create_maps_acc_graph()


if __name__ == "__main__":
    __main__()
