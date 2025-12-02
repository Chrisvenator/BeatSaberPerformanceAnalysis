import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd

from matplotlib.ticker import FuncFormatter
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

    ranges_pct = [(label, y0 * 100, y1 * 100, color) for (label, y0, y1, color) in ranges]

    for label, y0, y1, color in ranges_pct:
        ax.axhspan(y0, y1, color=color, alpha=0.25)

    df["accuracy_pct"] = df["accuracy"] * 100
    df["star_cat"] = df["stars"].astype("category")
    codes = df["star_cat"].cat.codes

    mask = codes != -1
    df = df[mask]
    codes = codes[mask]

    ax.scatter(
        df["timeSet"],
        df["accuracy_pct"],
        c=codes,
        cmap="inferno",   # stars color map
        s=10,
        zorder=2
    )

    plt.title("Player Performance Across Beat Saber Map Difficulties over Time")
    plt.xlabel("Date Score set")
    plt.ylabel("Accuracy (%)")

    df["t_sec"] = (df["timeSet"] - df["timeSet"].min()).dt.total_seconds()
    df["star_int"] = df["stars"].round().astype(int)

    cmap = plt.cm.inferno

    star_levels = [2, 4, 6, 8, 10, 12]

    star_min = df["stars"].min()
    star_max = df["stars"].max()
    star_range = max(star_max - star_min, 1e-6)  # avoid division by zero

    for star in star_levels:
        sub = df[df["star_int"] == star].sort_values("t_sec")

        if len(sub) < 6:
            continue

        t = sub["t_sec"].to_numpy()
        y = sub["accuracy_pct"].to_numpy()

        coef = np.polyfit(t, y, 6)  # 3 is usually stable enough
        poly = np.poly1d(coef)

        t_vals = np.linspace(t.min(), t.max(), 300)
        date_vals = df["timeSet"].min() + pd.to_timedelta(t_vals, unit="s")

        color_val = (star - star_min) / star_range
        color_val = max(0.0, min(1.0, color_val))  # clamp to [0, 1]

        ax.plot(
            date_vals,
            poly(t_vals),
            linewidth=2,
            color=cmap(color_val),
            label=f"{star}★ avg",
            zorder=3,
        )

    ax2 = ax.twinx()
    ax2.set_ylim(ax.get_ylim())  # gleiche Skala

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

    ax.legend(title="Star curves (even)")

    plt.show()


def __main__():
    create_maps_acc_graph()


if __name__ == "__main__":
    __main__()
