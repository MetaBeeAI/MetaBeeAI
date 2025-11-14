#!/usr/bin/env python3
"""
Trend Analysis Script for MetaBeeAI Database

This script analyzes trends and co-occurrence patterns between bee species and pesticides
in the MetaBeeAI dataset, providing quantitative measures and visualizations.
"""

import json
import os
import warnings
from typing import Dict, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

warnings.filterwarnings("ignore")

# Set up plotting style
plt.style.use("default")
sns.set_palette("husl")


def load_data_files(output_dir: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load bee species and pesticides data from JSON files."""
    print("Loading data files...")

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

    if os.path.exists(pesticides_file):
        with open(pesticides_file, "r", encoding="utf-8") as f:
            pesticides_data = json.load(f)
        print(f"  Loaded {len(pesticides_data)} pesticide entries")
    else:
        print(f"  Warning: {pesticides_file} not found")

    # Convert to DataFrames
    bee_df = pd.DataFrame(bee_species_data) if bee_species_data else pd.DataFrame()
    pesticides_df = pd.DataFrame(pesticides_data) if pesticides_data else pd.DataFrame()

    return bee_df, pesticides_df


def get_papers_dir():
    """Get the papers directory path."""
    # Try to load from .env file first
    env_file = ".env"
    if not os.path.exists(env_file):
        env_file = os.path.join(os.path.dirname(__file__), "..", ".env")

    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key] = value

    # Default fallback
    default_path = "/Users/user/Documents/MetaBeeAI_dataset_final"
    papers_dir = os.path.join(os.getenv("METABEEAI_DATA_DIR", default_path), "papers")
    return papers_dir


def analyze_co_occurrence(bee_df: pd.DataFrame, pesticides_df: pd.DataFrame) -> Dict:
    """Analyze co-occurrence patterns between bee species and pesticides."""
    print("\nAnalyzing co-occurrence patterns...")

    # Define nicotinic cholinergic pesticides (nAChR agonists)
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
        # Nicotine and related compounds
        "nicotine",
        # Other nAChR agonists that might be in the data
        "cyantraniliprole",
        "chlorantraniliprole",  # diamides, also nAChR modulators
    }

    # Filter out papers with empty pesticide names
    pesticides_df_filtered = pesticides_df[
        (pesticides_df["pesticide_name"].notna())
        & (pesticides_df["pesticide_name"] != "")
        & (pesticides_df["pesticide_name"].str.strip() != "")
    ]

    print(f"  Pesticide entries before filtering: {len(pesticides_df)}")
    print(f"  Pesticide entries after filtering empty names: {len(pesticides_df_filtered)}")

    # Filter to include only nicotinic cholinergic pesticides
    pesticides_df_nicotinic = pesticides_df_filtered[pesticides_df_filtered["pesticide_name"].isin(nicotinic_pesticides)]

    print(f"  Pesticide entries after filtering for nicotinic cholinergic pesticides: {len(pesticides_df_nicotinic)}")

    # Show which nicotinic pesticides are found in the data
    found_nicotinic = pesticides_df_nicotinic["pesticide_name"].unique()
    print(f"  Nicotinic pesticides found in data: {sorted(found_nicotinic)}")

    # Show which pesticides were excluded
    excluded_pesticides = set(pesticides_df_filtered["pesticide_name"].unique()) - set(found_nicotinic)
    print(f"  Non-nicotinic pesticides excluded: {len(excluded_pesticides)} (showing top 10)")
    excluded_counts = (
        pesticides_df_filtered[~pesticides_df_filtered["pesticide_name"].isin(nicotinic_pesticides)]["pesticide_name"]
        .value_counts()
        .head(10)
    )
    for pesticide, count in excluded_counts.items():
        print(f"    {pesticide}: {count} studies")

    # Get unique papers with bee species data
    papers_with_bees = set(bee_df["paper_id"].unique())
    papers_with_nicotinic_pesticides = set(pesticides_df_nicotinic["paper_id"].unique())
    papers_with_both = papers_with_bees.intersection(papers_with_nicotinic_pesticides)

    print(f"  Papers with bee species data: {len(papers_with_bees)}")
    print(f"  Papers with nicotinic cholinergic pesticide data: {len(papers_with_nicotinic_pesticides)}")
    print(f"  Papers with both: {len(papers_with_both)}")

    # Create standardized bee species names
    def get_standardized_bee_name(row):
        """Get standardized bee species name using genus + species, fallback to species_name."""
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

    # Filter out excluded papers (those with None standardized_bee_name)
    bee_df_filtered = bee_df[bee_df["standardized_bee_name"].notna()]

    # Show some examples of the standardization
    print("  Standardization examples:")
    sample_data = bee_df[["species_name", "genus", "species", "standardized_bee_name"]].head(10)
    for _, row in sample_data.iterrows():
        standardized = row["standardized_bee_name"] if row["standardized_bee_name"] else "EXCLUDED"
        print(f"    '{row['species_name']}' -> '{standardized}' (genus: '{row['genus']}', species: '{row['species']}')")

    print(f"  Papers with valid bee species data: {len(bee_df_filtered)} (excluded: {len(bee_df) - len(bee_df_filtered)})")

    # Update papers_with_bees to only include those with valid bee species
    papers_with_bees = set(bee_df_filtered["paper_id"].unique())
    papers_with_both = papers_with_bees.intersection(papers_with_nicotinic_pesticides)

    print(f"  Papers with valid bee species and nicotinic cholinergic pesticide data: {len(papers_with_both)}")

    # Create co-occurrence matrix
    co_occurrence_data = []

    for paper_id in papers_with_both:
        # Get bee species for this paper
        paper_bees = bee_df_filtered[bee_df_filtered["paper_id"] == paper_id]
        bee_species = paper_bees["standardized_bee_name"].unique()

        # Get nicotinic pesticides for this paper
        paper_pesticides = pesticides_df_nicotinic[pesticides_df_nicotinic["paper_id"] == paper_id]
        pesticides = paper_pesticides["pesticide_name"].unique()

        # Create combinations
        for bee in bee_species:
            for pesticide in pesticides:
                co_occurrence_data.append({"paper_id": paper_id, "bee_species": bee, "pesticide": pesticide})

    co_occurrence_df = pd.DataFrame(co_occurrence_data)

    if co_occurrence_df.empty:
        print("  No co-occurrence data found!")
        return {}

    # Calculate statistics
    bee_pesticide_counts = co_occurrence_df.groupby(["bee_species", "pesticide"]).size().reset_index(name="count")

    # Most common combinations
    top_combinations = bee_pesticide_counts.nlargest(20, "count")

    # Individual counts
    bee_counts = co_occurrence_df["bee_species"].value_counts()
    pesticide_counts = co_occurrence_df["pesticide"].value_counts()

    return {
        "co_occurrence_df": co_occurrence_df,
        "bee_pesticide_counts": bee_pesticide_counts,
        "top_combinations": top_combinations,
        "bee_counts": bee_counts,
        "pesticide_counts": pesticide_counts,
        "papers_with_both": papers_with_both,
    }


def create_visualizations(analysis_data: Dict, output_dir: str):
    """Create visualizations for the trend analysis."""
    print("\nCreating visualizations...")

    if not analysis_data:
        print("  No data to visualize!")
        return

    # Create output directory for plots
    plots_dir = os.path.join(output_dir, "trend_analysis_plots")
    os.makedirs(plots_dir, exist_ok=True)

    # 1. Top bee-pesticide combinations
    plt.figure(figsize=(12, 8))
    top_combinations = analysis_data["top_combinations"].head(15)

    # Create combination labels
    combination_labels = [f"{row['bee_species']} + {row['pesticide']}" for _, row in top_combinations.iterrows()]

    plt.barh(range(len(combination_labels)), top_combinations["count"])
    plt.yticks(range(len(combination_labels)), combination_labels)
    plt.xlabel("Number of Studies")
    plt.title("Top 15 Bee Species - Nicotinic Cholinergic Pesticide Combinations")
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "top_bee_pesticide_combinations.png"), dpi=300, bbox_inches="tight")
    plt.close()

    # 2. Most studied bee species
    plt.figure(figsize=(10, 6))
    bee_counts = analysis_data["bee_counts"].head(15)
    bee_counts.plot(kind="bar")
    plt.title("Most Studied Bee Species (in papers with pesticide data)")
    plt.xlabel("Bee Species")
    plt.ylabel("Number of Studies")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "most_studied_bee_species.png"), dpi=300, bbox_inches="tight")
    plt.close()

    # 3. Most tested pesticides
    plt.figure(figsize=(10, 6))
    pesticide_counts = analysis_data["pesticide_counts"].head(15)
    pesticide_counts.plot(kind="bar")
    plt.title("Most Tested Nicotinic Cholinergic Pesticides (in papers with bee species data)")
    plt.xlabel("Nicotinic Cholinergic Pesticide")
    plt.ylabel("Number of Studies")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "most_tested_nicotinic_pesticides.png"), dpi=300, bbox_inches="tight")
    plt.close()

    print(f"  Visualizations saved to: {plots_dir}")


def calculate_quantitative_measures(analysis_data: Dict) -> Dict:
    """Calculate quantitative measures of co-occurrence."""
    print("\nCalculating quantitative measures...")

    if not analysis_data:
        return {}

    co_occurrence_df = analysis_data["co_occurrence_df"]
    bee_pesticide_counts = analysis_data["bee_pesticide_counts"]

    # Basic statistics
    total_combinations = len(bee_pesticide_counts)
    total_studies = len(analysis_data["papers_with_both"])
    unique_bees = co_occurrence_df["bee_species"].nunique()
    unique_pesticides = co_occurrence_df["pesticide"].nunique()

    # Average pesticides per bee species
    pesticides_per_bee = co_occurrence_df.groupby("bee_species")["pesticide"].nunique().mean()

    # Average bee species per pesticide
    bees_per_pesticide = co_occurrence_df.groupby("pesticide")["bee_species"].nunique().mean()

    # Diversity measures
    bee_shannon_diversity = -sum(
        (count / total_combinations) * np.log2(count / total_combinations)
        for count in bee_pesticide_counts["count"]
        if count > 0
    )

    # Most/least studied combinations
    max_combination = bee_pesticide_counts.loc[bee_pesticide_counts["count"].idxmax()]
    min_combination = bee_pesticide_counts.loc[bee_pesticide_counts["count"].idxmin()]

    measures = {
        "total_combinations": total_combinations,
        "total_studies": total_studies,
        "unique_bee_species": unique_bees,
        "unique_pesticides": unique_pesticides,
        "avg_pesticides_per_bee": pesticides_per_bee,
        "avg_bee_species_per_pesticide": bees_per_pesticide,
        "bee_shannon_diversity": bee_shannon_diversity,
        "most_studied_combination": {
            "bee_species": max_combination["bee_species"],
            "pesticide": max_combination["pesticide"],
            "count": max_combination["count"],
        },
        "least_studied_combination": {
            "bee_species": min_combination["bee_species"],
            "pesticide": min_combination["pesticide"],
            "count": min_combination["count"],
        },
    }

    return measures


def generate_summary_report(analysis_data: Dict, measures: Dict, output_dir: str):
    """Generate a comprehensive summary report."""
    print("\nGenerating summary report...")

    report_file = os.path.join(output_dir, "trend_analysis_report.txt")

    with open(report_file, "w") as f:
        f.write("META BEE AI DATABASE - TREND ANALYSIS REPORT\n")
        f.write("FOCUS: NICOTINIC CHOLINERGIC PESTICIDES (nAChR AGONISTS)\n")
        f.write("=" * 60 + "\n\n")

        if not analysis_data or not measures:
            f.write("No data available for analysis.\n")
            return

        f.write("OVERVIEW\n")
        f.write("-" * 20 + "\n")
        f.write(f"Total studies with both bee species and nicotinic cholinergic pesticide data: {measures['total_studies']}\n")
        f.write(f"Unique bee species studied: {measures['unique_bee_species']}\n")
        f.write(f"Unique nicotinic cholinergic pesticides tested: {measures['unique_pesticides']}\n")
        f.write(f"Total bee-nicotinic pesticide combinations: {measures['total_combinations']}\n\n")

        f.write("DIVERSITY MEASURES\n")
        f.write("-" * 20 + "\n")
        f.write(f"Average pesticides tested per bee species: {measures['avg_pesticides_per_bee']:.2f}\n")
        f.write(f"Average bee species tested per pesticide: {measures['avg_bee_species_per_pesticide']:.2f}\n")
        f.write(f"Shannon diversity index: {measures['bee_shannon_diversity']:.3f}\n\n")

        f.write("TOP COMBINATIONS\n")
        f.write("-" * 20 + "\n")
        for i, (_, row) in enumerate(analysis_data["top_combinations"].head(10).iterrows(), 1):
            f.write(f"{i:2d}. {row['bee_species']} + {row['pesticide']}: {row['count']} studies\n")
        f.write("\n")

        f.write("MOST STUDIED BEE SPECIES\n")
        f.write("-" * 30 + "\n")
        for i, (species, count) in enumerate(analysis_data["bee_counts"].head(10).items(), 1):
            f.write(f"{i:2d}. {species}: {count} studies\n")
        f.write("\n")

        f.write("MOST TESTED NICOTINIC CHOLINERGIC PESTICIDES\n")
        f.write("-" * 45 + "\n")
        for i, (pesticide, count) in enumerate(analysis_data["pesticide_counts"].head(10).items(), 1):
            f.write(f"{i:2d}. {pesticide}: {count} studies\n")
        f.write("\n")

        f.write("EXTREME CASES\n")
        f.write("-" * 15 + "\n")
        f.write(
            f"Most studied combination: {measures['most_studied_combination']['bee_species']} + {measures['most_studied_combination']['pesticide']} ({measures['most_studied_combination']['count']} studies)\n"
        )
        f.write(
            f"Least studied combination: {measures['least_studied_combination']['bee_species']} + {measures['least_studied_combination']['pesticide']} ({measures['least_studied_combination']['count']} studies)\n"
        )

    print(f"  Summary report saved to: {report_file}")


def main():
    """Main function to run the trend analysis."""
    print("MetaBeeAI Database Trend Analysis")
    print("=" * 40)

    # Set up paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "output")

    # Load data
    bee_df, pesticides_df = load_data_files(output_dir)

    if bee_df.empty or pesticides_df.empty:
        print("Error: Could not load required data files!")
        return

    # Analyze co-occurrence
    analysis_data = analyze_co_occurrence(bee_df, pesticides_df)

    if not analysis_data:
        print("Error: No co-occurrence data found!")
        return

    # Calculate quantitative measures
    measures = calculate_quantitative_measures(analysis_data)

    # Create visualizations
    create_visualizations(analysis_data, output_dir)

    # Generate summary report
    generate_summary_report(analysis_data, measures, output_dir)

    print("\nTrend analysis completed successfully!")
    print(f"Results saved to: {output_dir}")


if __name__ == "__main__":
    main()
