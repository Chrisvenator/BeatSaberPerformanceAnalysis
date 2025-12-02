import matplotlib.pyplot as plt
import numpy as np

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

    # convert ranges to percent
    ranges_pct = [(label, y0 * 100, y1 * 100, color) for (label, y0, y1, color) in ranges]

    # draw color bands
    for label, y0, y1, color in ranges_pct:
        ax.axhspan(y0, y1, color=color, alpha=0.25)

    # scatter in percent
    df["accuracy_pct"] = df["accuracy"] * 100

    scatter = ax.scatter(
        df["stars"],
        df["accuracy_pct"],
        c=df["weighted_pp"],
        cmap="plasma",
        s=10,
        label="Map Score",
        zorder=2
    )

    plt.title("Player Performance Across Beat Saber Map Difficulty")
    plt.xlabel("Map Difficulty (★ Rating)")
    plt.ylabel("Accuracy (%)")

    # 2nd-degree polynomial (curve)
    coef = np.polyfit(df["stars"], df["accuracy_pct"], 13)
    poly = np.poly1d(coef)

    xs = np.linspace(df["stars"].min(), df["stars"].max(), 300)
    ax.plot(
        xs,
        poly(xs),
        linewidth=2,
        c="red",
        label="Average accuracy",
        zorder=3
    )

    top20 = df.nlargest(20, "weighted_pp")
    m20, b20 = np.polyfit(top20["stars"], top20["accuracy_pct"], 1)
    y_top20 = m20 * xs + b20

    mask = y_top20 < 100

    xs_visible = xs[mask]
    y_visible = y_top20[mask]

    ax.plot(
        xs_visible,
        y_visible,
        linewidth=2,
        c="yellow",
        label="Top 20 trend",
        zorder=1,
    )

    ax.legend()

    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label("weighted performance points (pp)\nweighted_pp = raw_pp × 0.965^map_index")

    ax.tick_params(axis='x', labelrotation=30)
    ax.grid()

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


    plt.show()


def __main__():
    create_maps_acc_graph()


if __name__ == "__main__":
    __main__()
