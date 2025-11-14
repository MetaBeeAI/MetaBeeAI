#!/usr/bin/env python3
"""
Network Analysis for MetaBeeAI Database

This script creates network visualizations showing connectivity between bee species
and nicotinic cholinergic pesticides, with edge thickness proportional to study counts.
"""

import json
import os
import warnings
from typing import Dict, Tuple

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import seaborn as sns

warnings.filterwarnings("ignore")

# Set up plotting style
plt.style.use("default")
sns.set_palette("Set3")


def load_and_process_data(output_dir: str) -> Tuple[pd.DataFrame, pd.DataFrame, Dict]:
    """Load and process bee species and pesticides data."""
    print("Loading and processing data...")

    # Load bee species data
    bee_species_file = os.path.join(output_dir, "bee_species_data.json")
    pesticides_file = os.path.join(output_dir, "pesticides_data.json")

    bee_species_data = []
    pesticides_data = []

    if os.path.exists(bee_species_file):
        with open(bee_species_file, "r", encoding="utf-8") as f:
            bee_species_data = json.load(f)
        print(f"  Loaded {len(bee_species_data)} bee species entries")
    else:
        print(f"  Warning: {bee_species_file} not found")
        return pd.DataFrame(), pd.DataFrame(), {}

    if os.path.exists(pesticides_file):
        with open(pesticides_file, "r", encoding="utf-8") as f:
            pesticides_data = json.load(f)
        print(f"  Loaded {len(pesticides_data)} pesticide entries")
    else:
        print(f"  Warning: {pesticides_file} not found")
        return pd.DataFrame(), pd.DataFrame(), {}

    # Convert to DataFrames
    bee_df = pd.DataFrame(bee_species_data)
    pesticides_df = pd.DataFrame(pesticides_data)

    # Apply bee species standardization (same logic as trend_analysis.py)
    def get_standardized_bee_name(row):
        genus = row.get("genus", "")
        species = row.get("species", "")
        species_name = row.get("species_name", "")

        # Priority 1: If we have both genus and species, use them
        if genus and species and genus != "" and species != "":
            return f"{genus} {species}"

        # Priority 2: If genus/species missing, use species_name (but exclude "Species not specified")
        if species_name and species_name != "" and species_name.lower() != "species not specified":
            return species_name

        # If species_name is "Species not specified" or empty, return None to exclude from analysis
        return None

    # Apply standardization
    bee_df["standardized_bee_name"] = bee_df.apply(get_standardized_bee_name, axis=1)

    # Filter out excluded entries
    bee_df_filtered = bee_df[bee_df["standardized_bee_name"].notna()]

    # Filter pesticides to only nicotinic cholinergic pesticides
    nicotinic_pesticides = {
        # Neonicotinoids
        "imidacloprid",
        "thiamethoxam",
        "clothianidin",
        "acetamiprid",
        "thiacloprid",
        "dinotefuran",
        "nitenpyram",
        # Sulfoximines
        "sulfoxaflor",
        # Butenolides
        "flupyradifurone",
        # Spinosyns
        "spinosad",
        "spinetoram",
    }

    # Filter out empty pesticide names and non-nicotinic pesticides
    pesticides_df_filtered = pesticides_df[
        (pesticides_df["pesticide_name"].notna())
        & (pesticides_df["pesticide_name"] != "")
        & (pesticides_df["pesticide_name"].str.strip() != "")
        & (pesticides_df["pesticide_name"].isin(nicotinic_pesticides))
    ]

    print(f"  Valid bee species entries: {len(bee_df_filtered)}")
    print(f"  Nicotinic pesticide entries: {len(pesticides_df_filtered)}")

    # Get unique papers with both bee species and nicotinic pesticides
    papers_with_bees = set(bee_df_filtered["paper_id"].unique())
    papers_with_pesticides = set(pesticides_df_filtered["paper_id"].unique())
    papers_with_both = papers_with_bees.intersection(papers_with_pesticides)

    print(f"  Papers with both bee species and nicotinic pesticides: {len(papers_with_both)}")

    return bee_df_filtered, pesticides_df_filtered, {"papers_with_both": papers_with_both}


def create_co_occurrence_matrix(bee_df: pd.DataFrame, pesticides_df: pd.DataFrame, papers_with_both: set) -> pd.DataFrame:
    """Create a co-occurrence matrix between bee species and pesticides."""
    print("\nCreating co-occurrence matrix...")

    co_occurrence_data = []

    for paper_id in papers_with_both:
        # Get bee species for this paper
        paper_bees = bee_df[bee_df["paper_id"] == paper_id]
        bee_species = paper_bees["standardized_bee_name"].unique()

        # Get pesticides for this paper
        paper_pesticides = pesticides_df[pesticides_df["paper_id"] == paper_id]
        pesticides = paper_pesticides["pesticide_name"].unique()

        # Create combinations using genus names only
        for bee in bee_species:
            # Extract genus (first word) from species name
            bee_genus = bee.split()[0] if " " in bee else bee

            # Skip "bee communities" and other non-genus entries
            if bee_genus.lower() in ["bee", "communities", "bee communities"]:
                continue

            for pesticide in pesticides:
                # Each paper counts as 1 study for this bee genus-pesticide combination
                co_occurrence_data.append(
                    {
                        "paper_id": paper_id,
                        "bee_genus": bee_genus,
                        "pesticide": pesticide,
                        "study_count": 1,  # Each paper = 1 study
                    }
                )

    co_occurrence_df = pd.DataFrame(co_occurrence_data)

    if co_occurrence_df.empty:
        print("  No co-occurrence data found!")
        return pd.DataFrame()

    # Remove duplicate paper_id combinations (same paper testing same bee genus + pesticide)
    co_occurrence_df_deduped = co_occurrence_df.drop_duplicates(["paper_id", "bee_genus", "pesticide"])

    # Filter out bee genera with fewer than 3 studies (3 papers)
    bee_study_counts = co_occurrence_df_deduped.groupby("bee_genus")["paper_id"].nunique()
    bee_genera_multiple_studies = bee_study_counts[bee_study_counts >= 3].index.tolist()

    print(
        f"  Filtering to {len(bee_genera_multiple_studies)} bee genera with ≥3 studies (removed {len(bee_study_counts) - len(bee_genera_multiple_studies)} with <3 studies)"
    )

    co_occurrence_df_filtered = co_occurrence_df_deduped[
        co_occurrence_df_deduped["bee_genus"].isin(bee_genera_multiple_studies)
    ]

    if co_occurrence_df_filtered.empty:
        print("  No co-occurrence data found after filtering!")
        return pd.DataFrame()

    # Create co-occurrence matrix - count unique papers per bee genus-pesticide combination
    co_occurrence_matrix = (
        co_occurrence_df_filtered.groupby(["bee_genus", "pesticide"])["paper_id"].nunique().reset_index(name="study_count")
    )

    print(f"  Found {len(co_occurrence_matrix)} bee-pesticide combinations")

    return co_occurrence_matrix


def create_bipartite_network(co_occurrence_matrix: pd.DataFrame, output_dir: str):
    """Create a bipartite network visualization."""
    print("\nCreating bipartite network visualization...")

    if co_occurrence_matrix.empty:
        print("  No data to visualize!")
        return

    # Create network graph
    G = nx.Graph()

    # Add nodes and edges
    for _, row in co_occurrence_matrix.iterrows():
        bee_genus = row["bee_genus"]
        pesticide = row["pesticide"]
        study_count = row["study_count"]

        # Add nodes
        G.add_node(bee_genus, node_type="bee")
        G.add_node(pesticide, node_type="pesticide")

        # Add edge with weight
        G.add_edge(bee_genus, pesticide, weight=study_count)

    # Get node lists
    bee_nodes = [n for n in G.nodes() if G.nodes[n]["node_type"] == "bee"]
    pesticide_nodes = [n for n in G.nodes() if G.nodes[n]["node_type"] == "pesticide"]

    print(f"  Network has {len(bee_nodes)} bee species and {len(pesticide_nodes)} pesticides")

    # Sort nodes by study count (most studied at top)
    bee_totals = co_occurrence_matrix.groupby("bee_genus")["study_count"].sum().sort_values(ascending=False)
    pesticide_totals = co_occurrence_matrix.groupby("pesticide")["study_count"].sum().sort_values(ascending=False)

    # Reorder bee and pesticide nodes by study count
    bee_nodes_sorted = [bee for bee in bee_totals.index if bee in bee_nodes]
    pesticide_nodes_sorted = [pesticide for pesticide in pesticide_totals.index if pesticide in pesticide_nodes]

    # Create layout - bees on left, pesticides on right
    pos = {}

    # Position bee nodes on the left (sorted by study count, most at top)
    bee_y_positions = np.linspace(0.95, 0.05, len(bee_nodes_sorted))  # Move away from edges
    for i, bee in enumerate(bee_nodes_sorted):
        pos[bee] = (0.05, bee_y_positions[i])  # Move towards center

    # Position pesticide nodes on the right (sorted by study count, most at top)
    pesticide_y_positions = np.linspace(0.95, 0.05, len(pesticide_nodes_sorted))  # Move away from edges
    for i, pesticide in enumerate(pesticide_nodes_sorted):
        pos[pesticide] = (0.95, pesticide_y_positions[i])  # Move towards center

    # Create figure
    fig, ax = plt.subplots(1, 1, figsize=(20, 16))

    # Calculate edge weights for visualization
    edges = G.edges()
    weights = [G[u][v]["weight"] for u, v in edges]

    # Normalize weights for edge thickness (min 2, max 12)
    if weights:
        min_weight = min(weights)
        max_weight = max(weights)
        if max_weight > min_weight:
            edge_widths = [2 + 10 * (w - min_weight) / (max_weight - min_weight) for w in weights]
        else:
            edge_widths = [4] * len(weights)
    else:
        edge_widths = [3] * len(edges)

    # Draw edges
    nx.draw_networkx_edges(G, pos, width=edge_widths, alpha=0.6, edge_color="gray")

    # Get positions for labels (nodes will not be drawn)
    bee_pos = {k: v for k, v in pos.items() if k in bee_nodes_sorted}
    pesticide_pos = {k: v for k, v in pos.items() if k in pesticide_nodes_sorted}

    # Add labels with white background rectangles
    # Bee labels (left side)
    bee_labels = {bee: bee for bee in bee_nodes_sorted}
    for bee, (x, y) in bee_pos.items():
        # Add white rectangle behind text
        ax.text(
            x,
            y,
            bee,
            fontsize=24,
            fontweight="bold",
            ha="center",
            va="center",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8, edgecolor="none"),
        )

    # Pesticide labels (right side)
    pesticide_labels = {pesticide: pesticide for pesticide in pesticide_nodes_sorted}
    for pesticide, (x, y) in pesticide_pos.items():
        # Add white rectangle behind text
        ax.text(
            x,
            y,
            pesticide,
            fontsize=24,
            fontweight="bold",
            ha="center",
            va="center",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8, edgecolor="none"),
        )

    # Set plot properties
    ax.set_xlim(-0.1, 1.1)
    ax.set_ylim(-0.05, 1.05)
    ax.set_aspect("equal")
    ax.axis("off")

    plt.tight_layout()

    # Save plot
    plots_dir = os.path.join(output_dir, "network_plots")
    os.makedirs(plots_dir, exist_ok=True)
    plt.savefig(os.path.join(plots_dir, "bee_pesticide_bipartite_network.png"), dpi=300, bbox_inches="tight")
    plt.close()

    print(f"  Bipartite network saved to: {plots_dir}/bee_pesticide_bipartite_network.png")


def create_pesticide_stressor_network(output_dir: str):
    """Create a bipartite network connecting pesticides to additional stressors."""
    print("\nCreating pesticide-stressor network...")

    # Load additional stressors data
    stressors_file = os.path.join(output_dir, "additional_stressors_data.json")
    if not os.path.exists(stressors_file):
        print("  No additional stressors data found!")
        return

    with open(stressors_file, "r") as f:
        stressors_data = json.load(f)

    # Load pesticides data (JSON format)
    pesticides_file = os.path.join(output_dir, "pesticides_data.json")
    if not os.path.exists(pesticides_file):
        print("  No pesticides JSON data found!")
        return

    with open(pesticides_file, "r") as f:
        pesticides_data = json.load(f)

    # Filter to nicotinic pesticides only
    nicotinic_pesticides = {
        "imidacloprid",
        "thiamethoxam",
        "clothianidin",
        "acetamiprid",
        "thiacloprid",
        "dinotefuran",
        "nitenpyram",
        "sulfoxaflor",
        "flupyradifurone",
        "spinosad",
        "spinetoram",
    }

    # Create paper_id to pesticides mapping
    paper_pesticides = {}
    for pesticide_entry in pesticides_data:
        paper_id = pesticide_entry.get("paper_id")
        pesticide_name = pesticide_entry.get("pesticide_name", "").strip()

        if pesticide_name and pesticide_name in nicotinic_pesticides:
            if paper_id not in paper_pesticides:
                paper_pesticides[paper_id] = set()
            paper_pesticides[paper_id].add(pesticide_name)

    # Create co-occurrence data
    co_occurrence_data = []
    papers_with_both = set()

    for stressor_entry in stressors_data:
        paper_id = stressor_entry.get("paper_id")
        stressor_type = stressor_entry.get("stressor_type", "").strip()

        # Skip empty stressor types
        if not stressor_type:
            continue

        # Check if this paper has nicotinic pesticides
        if paper_id in paper_pesticides:
            papers_with_both.add(paper_id)
            pesticides = paper_pesticides[paper_id]

            for pesticide in pesticides:
                co_occurrence_data.append({"paper_id": paper_id, "pesticide": pesticide, "stressor_type": stressor_type})

    if not co_occurrence_data:
        print("  No pesticide-stressor co-occurrence data found!")
        return

    # Create co-occurrence matrix
    co_occurrence_df = pd.DataFrame(co_occurrence_data)
    co_occurrence_df_deduped = co_occurrence_df.drop_duplicates(["paper_id", "pesticide", "stressor_type"])

    co_occurrence_matrix = (
        co_occurrence_df_deduped.groupby(["pesticide", "stressor_type"]).size().reset_index(name="study_count")
    )

    print(f"  Found {len(co_occurrence_matrix)} pesticide-stressor combinations across {len(papers_with_both)} papers")

    # Create network graph
    G = nx.Graph()

    # Add nodes and edges
    for _, row in co_occurrence_matrix.iterrows():
        pesticide = row["pesticide"]
        stressor_type = row["stressor_type"]
        study_count = row["study_count"]

        # Add nodes
        G.add_node(pesticide, node_type="pesticide")
        G.add_node(stressor_type, node_type="stressor")

        # Add edge with weight
        G.add_edge(pesticide, stressor_type, weight=study_count)

    # Get node lists
    pesticide_nodes = [n for n in G.nodes() if G.nodes[n]["node_type"] == "pesticide"]
    stressor_nodes = [n for n in G.nodes() if G.nodes[n]["node_type"] == "stressor"]

    print(f"  Network has {len(pesticide_nodes)} pesticides and {len(stressor_nodes)} stressor types")

    # Sort nodes by study count (most studied at top)
    pesticide_totals = co_occurrence_matrix.groupby("pesticide")["study_count"].sum().sort_values(ascending=False)
    stressor_totals = co_occurrence_matrix.groupby("stressor_type")["study_count"].sum().sort_values(ascending=False)

    pesticide_nodes_sorted = [pesticide for pesticide in pesticide_totals.index if pesticide in pesticide_nodes]
    stressor_nodes_sorted = [stressor for stressor in stressor_totals.index if stressor in stressor_nodes]

    # Create layout - pesticides on left, stressors on right
    pos = {}

    # Position pesticide nodes on the left (sorted by study count, most at top)
    pesticide_y_positions = np.linspace(0.95, 0.05, len(pesticide_nodes_sorted))  # Move away from edges
    for i, pesticide in enumerate(pesticide_nodes_sorted):
        pos[pesticide] = (0.05, pesticide_y_positions[i])  # Move towards center

    # Position stressor nodes on the right (sorted by study count, most at top)
    stressor_y_positions = np.linspace(0.95, 0.05, len(stressor_nodes_sorted))  # Move away from edges
    for i, stressor in enumerate(stressor_nodes_sorted):
        pos[stressor] = (0.95, stressor_y_positions[i])  # Move towards center

    # Create figure
    fig, ax = plt.subplots(1, 1, figsize=(20, 16))

    # Calculate edge weights for visualization
    edges = G.edges()
    edge_weights = [G[u][v]["weight"] for u, v in edges]
    max_weight = max(edge_weights) if edge_weights else 1
    edge_widths = [max(2, w / max_weight * 8) for w in edge_weights] if max_weight > 0 else [3] * len(edges)

    # Draw edges
    nx.draw_networkx_edges(G, pos, width=edge_widths, alpha=0.6, edge_color="gray")

    # Get positions for labels (nodes will not be drawn)
    pesticide_pos = {k: v for k, v in pos.items() if k in pesticide_nodes_sorted}
    stressor_pos = {k: v for k, v in pos.items() if k in stressor_nodes_sorted}

    # Add labels with white background rectangles
    # Pesticide labels (left side)
    pesticide_labels = {pesticide: pesticide for pesticide in pesticide_nodes_sorted}
    for pesticide, (x, y) in pesticide_pos.items():
        # Add white rectangle behind text
        ax.text(
            x,
            y,
            pesticide,
            fontsize=24,
            fontweight="bold",
            ha="center",
            va="center",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8, edgecolor="none"),
        )

    # Stressor labels (right side)
    stressor_labels = {stressor: stressor for stressor in stressor_nodes_sorted}
    for stressor, (x, y) in stressor_pos.items():
        # Add white rectangle behind text
        ax.text(
            x,
            y,
            stressor,
            fontsize=24,
            fontweight="bold",
            ha="center",
            va="center",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8, edgecolor="none"),
        )

    # Set plot properties
    ax.set_xlim(-0.1, 1.1)
    ax.set_ylim(-0.05, 1.05)
    ax.set_aspect("equal")
    ax.axis("off")

    plt.tight_layout()

    # Save plot
    plots_dir = os.path.join(output_dir, "network_plots")
    os.makedirs(plots_dir, exist_ok=True)
    plt.savefig(os.path.join(plots_dir, "pesticide_stressor_network.png"), dpi=300, bbox_inches="tight")
    plt.close()

    print(f"  Pesticide-stressor network saved to: {plots_dir}/pesticide_stressor_network.png")


def create_tripartite_network(bee_pesticide_matrix: pd.DataFrame, output_dir: str):
    """Create a tripartite network connecting bee genera, pesticides, and additional stressors."""
    print("\nCreating tripartite network...")

    # Load additional stressors data
    stressors_file = os.path.join(output_dir, "additional_stressors_data.json")
    if not os.path.exists(stressors_file):
        print("  No additional stressors data found!")
        return

    with open(stressors_file, "r") as f:
        stressors_data = json.load(f)

    # Load pesticides data (JSON format)
    pesticides_file = os.path.join(output_dir, "pesticides_data.json")
    if not os.path.exists(pesticides_file):
        print("  No pesticides JSON data found!")
        return

    with open(pesticides_file, "r") as f:
        pesticides_data = json.load(f)

    # Filter to nicotinic pesticides only
    nicotinic_pesticides = {
        "imidacloprid",
        "thiamethoxam",
        "clothianidin",
        "acetamiprid",
        "thiacloprid",
        "dinotefuran",
        "nitenpyram",
        "sulfoxaflor",
        "flupyradifurone",
        "spinosad",
        "spinetoram",
    }

    # Create paper_id to pesticides mapping
    paper_pesticides = {}
    for pesticide_entry in pesticides_data:
        paper_id = pesticide_entry.get("paper_id")
        pesticide_name = pesticide_entry.get("pesticide_name", "").strip()

        if pesticide_name and pesticide_name in nicotinic_pesticides:
            if paper_id not in paper_pesticides:
                paper_pesticides[paper_id] = set()
            paper_pesticides[paper_id].add(pesticide_name)

    # Create pesticide-stressor co-occurrence data
    pesticide_stressor_data = []
    papers_with_pesticide_stressor = set()

    for stressor_entry in stressors_data:
        paper_id = stressor_entry.get("paper_id")
        stressor_type = stressor_entry.get("stressor_type", "").strip()

        if not stressor_type or paper_id not in paper_pesticides:
            continue

        papers_with_pesticide_stressor.add(paper_id)
        pesticides = paper_pesticides[paper_id]

        for pesticide in pesticides:
            pesticide_stressor_data.append({"paper_id": paper_id, "pesticide": pesticide, "stressor_type": stressor_type})

    if not pesticide_stressor_data:
        print("  No pesticide-stressor co-occurrence data found!")
        return

    # Create pesticide-stressor matrix
    pesticide_stressor_df = pd.DataFrame(pesticide_stressor_data)
    pesticide_stressor_df_deduped = pesticide_stressor_df.drop_duplicates(["paper_id", "pesticide", "stressor_type"])
    pesticide_stressor_matrix = (
        pesticide_stressor_df_deduped.groupby(["pesticide", "stressor_type"]).size().reset_index(name="study_count")
    )

    # Create network graph
    G = nx.Graph()

    # Add bee-pesticide edges from existing matrix
    for _, row in bee_pesticide_matrix.iterrows():
        bee_genus = row["bee_genus"]
        pesticide = row["pesticide"]
        study_count = row["study_count"]

        G.add_node(bee_genus, node_type="bee")
        G.add_node(pesticide, node_type="pesticide")
        G.add_edge(bee_genus, pesticide, weight=study_count, edge_type="bee_pesticide")

    # Add pesticide-stressor edges
    for _, row in pesticide_stressor_matrix.iterrows():
        pesticide = row["pesticide"]
        stressor_type = row["stressor_type"]
        study_count = row["study_count"]

        G.add_node(stressor_type, node_type="stressor")
        if pesticide not in G.nodes():  # In case pesticide not in bee-pesticide matrix
            G.add_node(pesticide, node_type="pesticide")
        G.add_edge(pesticide, stressor_type, weight=study_count, edge_type="pesticide_stressor")

    # Get node lists
    bee_nodes = [n for n in G.nodes() if G.nodes[n]["node_type"] == "bee"]
    pesticide_nodes = [n for n in G.nodes() if G.nodes[n]["node_type"] == "pesticide"]
    stressor_nodes = [n for n in G.nodes() if G.nodes[n]["node_type"] == "stressor"]

    print(
        f"  Tripartite network has {len(bee_nodes)} bee genera, {len(pesticide_nodes)} pesticides, and {len(stressor_nodes)} stressor types"
    )

    # Sort nodes by study count (most studied at top)
    bee_totals = bee_pesticide_matrix.groupby("bee_genus")["study_count"].sum().sort_values(ascending=False)
    pesticide_totals = bee_pesticide_matrix.groupby("pesticide")["study_count"].sum().sort_values(ascending=False)
    stressor_totals = pesticide_stressor_matrix.groupby("stressor_type")["study_count"].sum().sort_values(ascending=False)

    bee_nodes_sorted = [bee for bee in bee_totals.index if bee in bee_nodes]
    pesticide_nodes_sorted = [pesticide for pesticide in pesticide_totals.index if pesticide in pesticide_nodes]
    stressor_nodes_sorted = [stressor for stressor in stressor_totals.index if stressor in stressor_nodes]

    # Create layout - bees on left, pesticides in center, stressors on right
    pos = {}

    # Position bee nodes on the left
    bee_y_positions = np.linspace(0.95, 0.05, len(bee_nodes_sorted))
    for i, bee in enumerate(bee_nodes_sorted):
        pos[bee] = (0.05, bee_y_positions[i])

    # Position pesticide nodes in the center
    pesticide_y_positions = np.linspace(0.95, 0.05, len(pesticide_nodes_sorted))
    for i, pesticide in enumerate(pesticide_nodes_sorted):
        pos[pesticide] = (0.5, pesticide_y_positions[i])

    # Position stressor nodes on the right
    stressor_y_positions = np.linspace(0.95, 0.05, len(stressor_nodes_sorted))
    for i, stressor in enumerate(stressor_nodes_sorted):
        pos[stressor] = (0.95, stressor_y_positions[i])

    # Create figure
    fig, ax = plt.subplots(1, 1, figsize=(24, 16))

    # Calculate edge weights for visualization
    bee_pesticide_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get("edge_type") == "bee_pesticide"]
    pesticide_stressor_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get("edge_type") == "pesticide_stressor"]

    bee_pesticide_weights = [G[u][v]["weight"] for u, v in bee_pesticide_edges]
    pesticide_stressor_weights = [G[u][v]["weight"] for u, v in pesticide_stressor_edges]

    max_bee_pesticide = max(bee_pesticide_weights) if bee_pesticide_weights else 1
    max_pesticide_stressor = max(pesticide_stressor_weights) if pesticide_stressor_weights else 1

    bee_pesticide_widths = (
        [max(2, w / max_bee_pesticide * 8) for w in bee_pesticide_weights]
        if max_bee_pesticide > 0
        else [3] * len(bee_pesticide_edges)
    )
    pesticide_stressor_widths = (
        [max(2, w / max_pesticide_stressor * 8) for w in pesticide_stressor_weights]
        if max_pesticide_stressor > 0
        else [3] * len(pesticide_stressor_edges)
    )

    # Draw edges with different colors
    if bee_pesticide_edges:
        nx.draw_networkx_edges(
            G, pos, edgelist=bee_pesticide_edges, width=bee_pesticide_widths, alpha=0.6, edge_color="steelblue"
        )

    if pesticide_stressor_edges:
        nx.draw_networkx_edges(
            G, pos, edgelist=pesticide_stressor_edges, width=pesticide_stressor_widths, alpha=0.6, edge_color="orange"
        )

    # Get positions for labels (nodes will not be drawn)
    bee_pos = {k: v for k, v in pos.items() if k in bee_nodes_sorted}
    pesticide_pos = {k: v for k, v in pos.items() if k in pesticide_nodes_sorted}
    stressor_pos = {k: v for k, v in pos.items() if k in stressor_nodes_sorted}

    # Add labels with white background rectangles
    # Bee labels (left side)
    bee_labels = {bee: bee for bee in bee_nodes_sorted}
    for bee, (x, y) in bee_pos.items():
        # Add white rectangle behind text
        ax.text(
            x,
            y,
            bee,
            fontsize=24,
            fontweight="bold",
            ha="center",
            va="center",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.6, edgecolor="none"),
        )

    # Pesticide labels (center)
    pesticide_labels = {pesticide: pesticide for pesticide in pesticide_nodes_sorted}
    for pesticide, (x, y) in pesticide_pos.items():
        # Add white rectangle behind text
        ax.text(
            x,
            y,
            pesticide,
            fontsize=24,
            fontweight="bold",
            ha="center",
            va="center",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.6, edgecolor="none"),
        )

    # Stressor labels (right side)
    stressor_labels = {stressor: stressor for stressor in stressor_nodes_sorted}
    for stressor, (x, y) in stressor_pos.items():
        # Add white rectangle behind text
        ax.text(
            x,
            y,
            stressor,
            fontsize=24,
            fontweight="bold",
            ha="center",
            va="center",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.6, edgecolor="none"),
        )

    # Set plot properties
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.05, 1.05)
    ax.set_aspect("equal")
    ax.axis("off")

    plt.tight_layout()

    # Save plot
    plots_dir = os.path.join(output_dir, "network_plots")
    os.makedirs(plots_dir, exist_ok=True)
    plt.savefig(os.path.join(plots_dir, "tripartite_network.png"), dpi=300, bbox_inches="tight")
    plt.close()

    print(f"  Tripartite network saved to: {plots_dir}/tripartite_network.png")


def create_network_statistics(co_occurrence_matrix: pd.DataFrame, output_dir: str):
    """Generate network statistics and save to file."""
    print("\nGenerating network statistics...")

    if co_occurrence_matrix.empty:
        print("  No data to analyze!")
        return

    # Calculate statistics
    total_connections = len(co_occurrence_matrix)
    total_studies = co_occurrence_matrix["study_count"].sum()

    bee_stats = (
        co_occurrence_matrix.groupby("bee_genus")["study_count"]
        .agg(["sum", "count", "mean"])
        .sort_values("sum", ascending=False)
    )
    pesticide_stats = (
        co_occurrence_matrix.groupby("pesticide")["study_count"]
        .agg(["sum", "count", "mean"])
        .sort_values("sum", ascending=False)
    )

    # Save statistics to file
    stats_file = os.path.join(output_dir, "network_statistics.txt")

    with open(stats_file, "w") as f:
        f.write("BEE SPECIES - NICOTINIC PESTICIDE NETWORK STATISTICS\n")
        f.write("=" * 55 + "\n\n")

        f.write("OVERVIEW\n")
        f.write("-" * 20 + "\n")
        f.write(f"Total bee-pesticide connections: {total_connections}\n")
        f.write(f"Total studies across all connections: {total_studies}\n")
        f.write(f"Average studies per connection: {total_studies/total_connections:.2f}\n\n")

        f.write("TOP BEE GENERA BY TOTAL STUDIES\n")
        f.write("-" * 32 + "\n")
        for i, (genus, row) in enumerate(bee_stats.head(15).iterrows(), 1):
            f.write(f"{i:2d}. {genus}: {row['sum']} studies, {row['count']} pesticides, {row['mean']:.1f} avg/pesticide\n")
        f.write("\n")

        f.write("TOP PESTICIDES BY TOTAL STUDIES\n")
        f.write("-" * 32 + "\n")
        for i, (pesticide, row) in enumerate(pesticide_stats.head(10).iterrows(), 1):
            f.write(f"{i:2d}. {pesticide}: {row['sum']} studies, {row['count']} bee genera, {row['mean']:.1f} avg/genus\n")
        f.write("\n")

        f.write("TOP BEE-PESTICIDE COMBINATIONS\n")
        f.write("-" * 35 + "\n")
        top_combinations = co_occurrence_matrix.nlargest(20, "study_count")
        for i, (_, row) in enumerate(top_combinations.iterrows(), 1):
            f.write(f"{i:2d}. {row['bee_genus']} + {row['pesticide']}: {row['study_count']} studies\n")

    print(f"  Network statistics saved to: {stats_file}")


def create_pesticide_stressor_summary(output_dir: str):
    """Generate comprehensive summary statistics for pesticides and stressors data."""
    print("\nGenerating pesticide and stressor summary...")

    # Load pesticides data
    pesticides_file = os.path.join(output_dir, "pesticides_data.json")
    stressors_file = os.path.join(output_dir, "additional_stressors_data.json")

    if not os.path.exists(pesticides_file) or not os.path.exists(stressors_file):
        print("  Required data files not found!")
        return

    with open(pesticides_file, "r") as f:
        pesticides_data = json.load(f)

    with open(stressors_file, "r") as f:
        stressors_data = json.load(f)

    # Define nicotinic pesticides
    nicotinic_pesticides = {
        "imidacloprid",
        "thiamethoxam",
        "clothianidin",
        "acetamiprid",
        "thiacloprid",
        "dinotefuran",
        "nitenpyram",
        "sulfoxaflor",
        "flupyradifurone",
        "spinosad",
        "spinetoram",
    }

    # Process pesticides data
    pesticides_df = pd.DataFrame(pesticides_data)
    pesticides_df_filtered = pesticides_df[
        (pesticides_df["pesticide_name"].notna())
        & (pesticides_df["pesticide_name"] != "")
        & (pesticides_df["pesticide_name"].str.strip() != "")
    ]

    # Separate nicotinic and non-nicotinic pesticides
    pesticides_df_nicotinic = pesticides_df_filtered[pesticides_df_filtered["pesticide_name"].isin(nicotinic_pesticides)]
    pesticides_df_other = pesticides_df_filtered[~pesticides_df_filtered["pesticide_name"].isin(nicotinic_pesticides)]

    # Process stressors data
    stressors_df = pd.DataFrame(stressors_data)
    stressors_df_filtered = stressors_df[
        (stressors_df["stressor_type"].notna())
        & (stressors_df["stressor_type"] != "")
        & (stressors_df["stressor_type"].str.strip() != "")
    ]

    # Generate summary statistics
    summary_file = os.path.join(output_dir, "pesticide_stressor_summary.txt")

    with open(summary_file, "w") as f:
        f.write("PESTICIDES AND ADDITIONAL STRESSORS DATA SUMMARY\n")
        f.write("=" * 50 + "\n\n")

        # PESTICIDES SUMMARY
        f.write("PESTICIDES DATA OVERVIEW\n")
        f.write("-" * 25 + "\n")
        f.write(f"Total pesticide entries: {len(pesticides_data)}\n")
        f.write(f"Non-empty pesticide entries: {len(pesticides_df_filtered)}\n")
        f.write(f"Unique papers with pesticides: {pesticides_df_filtered['paper_id'].nunique()}\n")
        f.write(f"Unique pesticide names: {pesticides_df_filtered['pesticide_name'].nunique()}\n")
        f.write(f"Nicotinic pesticide entries: {len(pesticides_df_nicotinic)}\n")
        f.write(f"Other pesticide entries: {len(pesticides_df_other)}\n\n")

        # TOP PESTICIDES
        f.write("TOP 15 PESTICIDES (ALL TYPES)\n")
        f.write("-" * 30 + "\n")
        top_pesticides = pesticides_df_filtered["pesticide_name"].value_counts().head(15)
        for i, (pesticide, count) in enumerate(top_pesticides.items(), 1):
            pesticide_type = "Nicotinic" if pesticide in nicotinic_pesticides else "Other"
            f.write(f"{i:2d}. {pesticide}: {count} studies ({pesticide_type})\n")
        f.write("\n")

        # NICOTINIC PESTICIDES
        f.write("NICOTINIC CHOLINERGIC PESTICIDES\n")
        f.write("-" * 35 + "\n")
        nicotinic_counts = pesticides_df_nicotinic["pesticide_name"].value_counts()
        for i, (pesticide, count) in enumerate(nicotinic_counts.items(), 1):
            papers = pesticides_df_nicotinic[pesticides_df_nicotinic["pesticide_name"] == pesticide]["paper_id"].nunique()
            f.write(f"{i:2d}. {pesticide}: {count} studies, {papers} papers\n")
        f.write("\n")

        # STRESSORS SUMMARY
        f.write("ADDITIONAL STRESSORS DATA OVERVIEW\n")
        f.write("-" * 35 + "\n")
        f.write(f"Total stressor entries: {len(stressors_data)}\n")
        f.write(f"Non-empty stressor entries: {len(stressors_df_filtered)}\n")
        f.write(f"Unique papers with stressors: {stressors_df_filtered['paper_id'].nunique()}\n")
        f.write(f"Unique stressor types: {stressors_df_filtered['stressor_type'].nunique()}\n\n")

        # STRESSOR TYPES
        f.write("STRESSOR TYPES DISTRIBUTION\n")
        f.write("-" * 30 + "\n")
        stressor_counts = stressors_df_filtered["stressor_type"].value_counts()
        for i, (stressor_type, count) in enumerate(stressor_counts.items(), 1):
            papers = stressors_df_filtered[stressors_df_filtered["stressor_type"] == stressor_type]["paper_id"].nunique()
            f.write(f"{i:2d}. {stressor_type}: {count} entries, {papers} papers\n")
        f.write("\n")

        # CO-OCCURRENCE ANALYSIS
        f.write("PESTICIDE-STRESSOR CO-OCCURRENCE\n")
        f.write("-" * 35 + "\n")

        # Papers with both pesticides and stressors
        pesticide_papers = set(pesticides_df_filtered["paper_id"].unique())
        stressor_papers = set(stressors_df_filtered["paper_id"].unique())
        papers_with_both = pesticide_papers.intersection(stressor_papers)

        f.write(f"Papers with pesticides: {len(pesticide_papers)}\n")
        f.write(f"Papers with stressors: {len(stressor_papers)}\n")
        f.write(f"Papers with both: {len(papers_with_both)}\n")
        f.write(f"Papers with only pesticides: {len(pesticide_papers - stressor_papers)}\n")
        f.write(f"Papers with only stressors: {len(stressor_papers - pesticide_papers)}\n\n")

        # TOP PESTICIDE-STRESSOR COMBINATIONS
        if papers_with_both:
            f.write("TOP PESTICIDE-STRESSOR COMBINATIONS\n")
            f.write("-" * 40 + "\n")

            # Create co-occurrence data
            co_occurrence_data = []
            for paper_id in papers_with_both:
                paper_pesticides = pesticides_df_filtered[pesticides_df_filtered["paper_id"] == paper_id][
                    "pesticide_name"
                ].unique()
                paper_stressors = stressors_df_filtered[stressors_df_filtered["paper_id"] == paper_id]["stressor_type"].unique()

                for pesticide in paper_pesticides:
                    for stressor in paper_stressors:
                        co_occurrence_data.append({"pesticide": pesticide, "stressor_type": stressor, "paper_id": paper_id})

            if co_occurrence_data:
                co_occurrence_df = pd.DataFrame(co_occurrence_data)
                co_occurrence_df_deduped = co_occurrence_df.drop_duplicates(["paper_id", "pesticide", "stressor_type"])
                combination_counts = (
                    co_occurrence_df_deduped.groupby(["pesticide", "stressor_type"]).size().sort_values(ascending=False)
                )

                for i, ((pesticide, stressor), count) in enumerate(combination_counts.head(20).items(), 1):
                    pesticide_type = "Nicotinic" if pesticide in nicotinic_pesticides else "Other"
                    f.write(f"{i:2d}. {pesticide} + {stressor}: {count} papers ({pesticide_type})\n")

        f.write("\n")
        f.write("SUMMARY COMPLETED\n")
        f.write("=" * 20 + "\n")

    print(f"  Pesticide and stressor summary saved to: {summary_file}")


def main():
    """Main function to run the network analysis."""
    print("MetaBeeAI Database Network Analysis")
    print("=" * 40)

    # Set up paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "output")

    # Load and process data
    bee_df, pesticides_df, metadata = load_and_process_data(output_dir)

    if bee_df.empty or pesticides_df.empty:
        print("Error: Could not load required data files!")
        return

    # Create co-occurrence matrix
    co_occurrence_matrix = create_co_occurrence_matrix(bee_df, pesticides_df, metadata["papers_with_both"])

    if co_occurrence_matrix.empty:
        print("Error: No co-occurrence data found!")
        return

    # Create visualizations
    # create_bipartite_network(co_occurrence_matrix, output_dir)  # Removed - output not needed
    # create_pesticide_stressor_network(output_dir)  # Removed - output not needed
    create_tripartite_network(co_occurrence_matrix, output_dir)
    create_network_statistics(co_occurrence_matrix, output_dir)
    create_pesticide_stressor_summary(output_dir)

    print("\nNetwork analysis completed successfully!")
    print(f"Results saved to: {output_dir}/network_plots/")
    print(f"Statistics saved to: {output_dir}/network_statistics.txt")


if __name__ == "__main__":
    main()
