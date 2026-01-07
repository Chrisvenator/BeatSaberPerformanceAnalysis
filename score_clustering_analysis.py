#!/usr/bin/env python3
"""
Clustering analysis for Beat Saber score dataset.

What it does
- Loads your dataset via dataset.load_dataset.load_dataset(ranked=True)
- Builds a feature matrix from selected numeric columns + optional map_tag one-hot
- Standardizes features
- Tries a range of k values and picks the best by silhouette score (if available)
- Fits KMeans with the chosen k
- Saves:
  - clustered_scores.csv (original rows + cluster label)
  - cluster_summary.csv (cluster means in original units)
  - cluster_stars_vs_accuracy.png (main result plot)

Run:
  python cluster_analysis.py

Optional:
  python cluster_analysis.py --k-min 3 --k-max 8 --outdir out --no-tags
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

from dataset.load_dataset import load_dataset


@dataclass
class FitResult:
    k: int
    silhouette: Optional[float]
    inertia: float

CLUSTER_NAMES = {
    0: "High-risk difficulty push",
    1: "Comfort / accuracy farming",
    2: "Controlled progression",
    3: "Execution failures",
    4: "Precision mastery",
    5: "High-difficulty mastery",
}


def _pick_feature_columns(df: pd.DataFrame) -> List[str]:
    """
    Pick a sensible default set of numeric features from the columns that exist.
    You can edit this list if you want a different definition of "performance profile".
    """
    candidates = [
        "stars",
        "accuracy",
        "weighted_pp",
        "pp",
        "weight",
        "nps",
        "notes",
        "noteCount",
        "maxScore",
        "duration",
        "bpm",
    ]
    return [c for c in candidates if c in df.columns]


def _build_feature_matrix(
    df: pd.DataFrame,
    numeric_cols: List[str],
    include_tags: bool = True,
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Returns (X_df, feature_names). X_df has only numeric columns ready for scaling.
    """
    if not numeric_cols:
        raise ValueError("No numeric feature columns found. Check your dataset columns.")

    X = df[numeric_cols].copy()

    # Convert to numeric (just in case)
    for c in numeric_cols:
        X[c] = pd.to_numeric(X[c], errors="coerce")

    # Optional one-hot for map_tag
    feature_names = numeric_cols[:]
    if include_tags and "map_tag" in df.columns:
        tags = df["map_tag"].astype("category")
        onehot = pd.get_dummies(tags, prefix="tag", dummy_na=False)
        # If there are no tags (all NaN), onehot could be empty
        if onehot.shape[1] > 0:
            X = pd.concat([X, onehot], axis=1)
            feature_names.extend(list(onehot.columns))

    # Drop rows with missing feature values
    X = X.dropna(axis=0, how="any")
    return X, feature_names


def _fit_kmeans_with_selection(
    X_scaled: np.ndarray,
    k_min: int,
    k_max: int,
    random_state: int,
) -> Tuple[KMeans, List[FitResult]]:
    """
    Fit KMeans for k in [k_min, k_max], choose best by silhouette score.
    Falls back to inertia if silhouette cannot be computed.
    """
    results: List[FitResult] = []
    best_model: Optional[KMeans] = None
    best_score: Optional[float] = None

    for k in range(k_min, k_max + 1):
        model = KMeans(n_clusters=k, n_init=20, random_state=random_state)
        labels = model.fit_predict(X_scaled)

        sil: Optional[float] = None
        try:
            # silhouette requires at least 2 clusters and no empty clusters
            if len(set(labels)) > 1 and X_scaled.shape[0] > k:
                sil = float(silhouette_score(X_scaled, labels))
        except Exception:
            sil = None

        results.append(FitResult(k=k, silhouette=sil, inertia=float(model.inertia_)))

        if sil is not None:
            if best_score is None or sil > best_score:
                best_score = sil
                best_model = model

    if best_model is not None:
        return best_model, results

    # Fallback if silhouette is unavailable for all k: pick lowest inertia
    best_k = min(results, key=lambda r: r.inertia).k
    fallback = KMeans(n_clusters=best_k, n_init=20, random_state=random_state).fit(X_scaled)
    return fallback, results


def _summarize_clusters(df_kept: pd.DataFrame, label_col: str, cols: List[str]) -> pd.DataFrame:
    """
    Compute cluster means/medians/counts on selected columns in original units.
    """
    summary_cols = [c for c in cols if c in df_kept.columns]
    grp = df_kept.groupby(label_col, observed=True)

    summary = grp[summary_cols].agg(["count", "mean", "median", "std"])
    # Flatten column names
    summary.columns = ["_".join([str(a), str(b)]) for a, b in summary.columns.to_list()]
    summary = summary.reset_index()
    return summary


def _plot_clusters_stars_accuracy(
    df_kept: pd.DataFrame,
    outpath: str,
    label_col: str = "cluster",
) -> None:
    """
    Main visualization: stars vs accuracy (%) colored by cluster label.
    Uses accuracy bands similar to your earlier visuals.
    """
    if "stars" not in df_kept.columns or "accuracy" not in df_kept.columns:
        raise ValueError("Need 'stars' and 'accuracy' columns to plot stars vs accuracy.")

    plot_df = df_kept.copy()
    plot_df["accuracy_pct"] = plot_df["accuracy"] * 100.0

    fig, ax = plt.subplots(figsize=(12, 6))

    # Accuracy rank bands
    ranges = [
        ("SSS", 100, 100, "#FF0000"),
        ("SS", 90, 100, "#00FFFF"),
        ("S", 80, 90, "#32c7b7"),
        ("A", 65, 80, "#4CAF50"),
        ("B", 50, 65, "#d9ac26"),
        ("C", 35, 50, "#d67028"),
        ("D", 20, 35, "#c42c2c"),
        ("E", 0, 20, "#470101"),
    ]

    min_acc = float(plot_df["accuracy_pct"].min())
    ranges = [r for r in ranges if r[2] >= min_acc]

    for _, y0, y1, color in ranges:
        ax.axhspan(y0, y1, color=color, alpha=0.20)


    # Scatter by cluster
    clusters = sorted(plot_df[label_col].unique().tolist())
    for cl in clusters:
        sub = plot_df[plot_df[label_col] == cl]
        label = f"Cluster {cl}: {CLUSTER_NAMES.get(cl, 'Unlabeled')}"
        ax.scatter(
            sub["stars"],
            sub["accuracy_pct"],
            s=14,
            alpha=0.85,
            label=label,
            zorder=2,
        )

    ax.set_title("Performance Profiles Identified via K-Means Clustering: Map Difficulty vs Accuracy")
    ax.set_xlabel("Map Difficulty (★ Rating)")
    ax.set_ylabel("Accuracy (%)")
    ax.grid(True, alpha=0.35)
    ax.legend(title="Clusters", loc="lower left")

    # Right-side labels for bands
    ax2 = ax.twinx()
    ax2.set_ylim(ax.get_ylim())
    tick_pos = [(y0 + y1) / 2 for (_, y0, y1, _) in ranges]
    tick_labels = [label for (label, _, _, _) in ranges]
    ax2.set_yticks(tick_pos)
    ax2.set_yticklabels(tick_labels)
    for tick, (_, _, _, color) in zip(ax2.get_yticklabels(), ranges):
        tick.set_color(color)
        tick.set_fontweight("bold")

    plt.tight_layout()
    fig.savefig(outpath, dpi=160)
    plt.close(fig)


def main(save_csv_files = False) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--k-min", type=int, default=3, help="Minimum number of clusters to try")
    parser.add_argument("--k-max", type=int, default=7, help="Maximum number of clusters to try")
    parser.add_argument("--random-state", type=int, default=42, help="Random seed")
    parser.add_argument("--outdir", type=str, default="clustering_out", help="Output directory")
    parser.add_argument("--no-tags", action="store_true", help="Do not include map_tag one-hot features")
    args = parser.parse_args()

    # Load ranked dataset (matches your earlier graphs)
    df = load_dataset(True)

    numeric_cols = _pick_feature_columns(df)
    if "accuracy" not in numeric_cols and "accuracy" in df.columns:
        numeric_cols.append("accuracy")
    if "stars" not in numeric_cols and "stars" in df.columns:
        numeric_cols.append("stars")

    # Build feature matrix
    X_df, feature_names = _build_feature_matrix(df, numeric_cols, include_tags=(not args.no_tags))

    # Keep matching rows from df (after NaN drop in X_df)
    df_kept = df.loc[X_df.index].copy()

    # Scale
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_df.to_numpy())

    # Fit + select k
    model, results = _fit_kmeans_with_selection(
        X_scaled,
        k_min=args.k_min,
        k_max=args.k_max,
        random_state=args.random_state,
    )

    df_kept["cluster"] = model.labels_.astype(int)
    diag = pd.DataFrame([r.__dict__ for r in results])
    summary_cols = ["stars", "accuracy", "weighted_pp", "pp", "nps"]
    summary = _summarize_clusters(df_kept, "cluster", summary_cols)

    if save_csv_files:
        os.makedirs(args.outdir, exist_ok=True)

        diag.to_csv(os.path.join(args.outdir, "k_selection_diagnostics.csv"), index=False)
        df_kept.to_csv(os.path.join(args.outdir, "clustered_scores.csv"), index=False)
        summary.to_csv(os.path.join(args.outdir, "cluster_summary.csv"), index=False)

        plot_path = os.path.join(args.outdir, "cluster_stars_vs_accuracy.png")
        _plot_clusters_stars_accuracy(df_kept, plot_path, label_col="cluster")

    _plot_clusters_stars_accuracy(df_kept, "./score_clustering_analysis.png", label_col="cluster")

    # Print quick report
    chosen_k = model.n_clusters
    best_sil = diag["silhouette"].max() if "silhouette" in diag.columns else None
    print(f"Done. Chosen k = {chosen_k}")
    if pd.notna(best_sil):
        print(f"Best silhouette among tried k: {best_sil:.4f}")
    print(f"Outputs written to: {args.outdir}")
    print(" - k_selection_diagnostics.csv")
    print(" - clustered_scores.csv")
    print(" - cluster_summary.csv")
    print(" - cluster_stars_vs_accuracy.png")
    print("\nFeatures used:")
    for name in feature_names:
        print(f" - {name}")


if __name__ == "__main__":
    main()
