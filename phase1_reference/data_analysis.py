import pandas as pd
import matplotlib

# Use a non-GUI backend so Matplotlib works inside Docker
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# ============================================================
# 1. LOAD THE DATASET
# ============================================================

df = pd.read_csv("All_Diets.csv")

print("===== DATASET PREVIEW =====")
print(df.head())

print("\n===== DATASET INFORMATION =====")
df.info()


# ============================================================
# 2. CLEAN THE DATA
# ============================================================

print("\n===== MISSING VALUES BEFORE CLEANING =====")
print(df.isnull().sum())

# Standardize text columns to avoid values such as "Paleo" and "paleo"
# being treated as different categories.
df["Diet_type"] = df["Diet_type"].str.strip().str.title()
df["Cuisine_type"] = df["Cuisine_type"].str.strip().str.title()

# Nutritional columns used for analysis
numeric_columns = ["Protein(g)", "Carbs(g)", "Fat(g)"]

# Make sure nutritional columns contain numeric data.
# Invalid values are converted to NaN.
for column in numeric_columns:
    df[column] = pd.to_numeric(df[column], errors="coerce")

# Replace missing nutritional values with the mean of each column
for column in numeric_columns:
    df[column] = df[column].fillna(df[column].mean())

print("\n===== MISSING VALUES AFTER CLEANING =====")
print(df[numeric_columns].isnull().sum())


# ============================================================
# 3. AVERAGE MACRONUTRIENTS FOR EACH DIET TYPE
# ============================================================

avg_macros = (
    df.groupby("Diet_type")[numeric_columns]
    .mean()
    .round(2)
)

print("\n===== AVERAGE MACRONUTRIENTS BY DIET TYPE =====")
print(avg_macros)


# ============================================================
# 4. TOP 5 PROTEIN-RICH RECIPES FOR EACH DIET TYPE
# ============================================================

top_protein = (
    df.sort_values("Protein(g)", ascending=False)
    .groupby("Diet_type")
    .head(5)
)

print("\n===== TOP 5 PROTEIN-RICH RECIPES BY DIET TYPE =====")

for diet, group in top_protein.groupby("Diet_type"):
    print(f"\n{diet}:")
    print(
        group[
            ["Recipe_name", "Cuisine_type", "Protein(g)"]
        ].to_string(index=False)
    )


# ============================================================
# 5. DIET TYPE WITH THE HIGHEST PROTEIN CONTENT
# ============================================================

# Compare diet types using their average protein content
average_protein = df.groupby("Diet_type")["Protein(g)"].mean()

highest_protein_diet = average_protein.idxmax()
highest_protein_value = average_protein.max()

print("\n===== DIET TYPE WITH HIGHEST AVERAGE PROTEIN =====")
print(f"Diet Type: {highest_protein_diet}")
print(f"Average Protein: {highest_protein_value:.2f} g")


# ============================================================
# 6. MOST COMMON CUISINE FOR EACH DIET TYPE
# ============================================================

most_common_cuisines = (
    df.groupby("Diet_type")["Cuisine_type"]
    .agg(lambda x: x.mode().iloc[0] if not x.mode().empty else "Unknown")
)

print("\n===== MOST COMMON CUISINE FOR EACH DIET TYPE =====")
print(most_common_cuisines)


# ============================================================
# 7. CREATE NEW NUTRITIONAL METRICS
# ============================================================

# Replace zero denominators with NaN to avoid division by zero.
df["Protein_to_Carbs_ratio"] = (
    df["Protein(g)"] / df["Carbs(g)"].replace(0, np.nan)
)

df["Carbs_to_Fat_ratio"] = (
    df["Carbs(g)"] / df["Fat(g)"].replace(0, np.nan)
)

print("\n===== NEW NUTRITIONAL METRICS =====")

print(
    df[
        [
            "Recipe_name",
            "Protein_to_Carbs_ratio",
            "Carbs_to_Fat_ratio"
        ]
    ].head(10).round(2)
)


# ============================================================
# 8. BAR CHART - AVERAGE MACRONUTRIENTS
# ============================================================

avg_macros.plot(
    kind="bar",
    figsize=(12, 7)
)

plt.title("Average Macronutrient Content by Diet Type")
plt.xlabel("Diet Type")
plt.ylabel("Average Macronutrient Content (g)")
plt.xticks(rotation=45, ha="right")
plt.legend(title="Macronutrient")
plt.tight_layout()

plt.savefig("average_macronutrients_bar_chart.png", dpi=300)


# ============================================================
# 9. HEATMAP - DIET TYPES AND MACRONUTRIENTS
# ============================================================

plt.figure(figsize=(10, 7))

sns.heatmap(
    avg_macros,
    annot=True,
    fmt=".1f",
    cmap="YlGnBu"
)

plt.title("Average Macronutrient Content by Diet Type")
plt.xlabel("Macronutrient")
plt.ylabel("Diet Type")
plt.tight_layout()

plt.savefig("macronutrients_heatmap.png", dpi=300)


# ============================================================
# 10. SCATTER PLOT - TOP PROTEIN-RICH RECIPES
# ============================================================

plt.figure(figsize=(12, 8))

sns.scatterplot(
    data=top_protein,
    x="Diet_type",
    y="Protein(g)",
    hue="Cuisine_type",
    s=100
)

plt.title("Top 5 Protein-Rich Recipes by Diet Type and Cuisine")
plt.xlabel("Diet Type")
plt.ylabel("Protein (g)")
plt.xticks(rotation=45, ha="right")
plt.legend(
    title="Cuisine Type",
    bbox_to_anchor=(1.05, 1),
    loc="upper left"
)

plt.tight_layout()

plt.savefig("top_protein_recipes_scatter_plot.png", dpi=300)



# ============================================================
# 11. SAVE PROCESSED DATA
# ============================================================

df.to_csv("All_Diets_Cleaned.csv", index=False)

print("\n===== ANALYSIS COMPLETE =====")
print("Created:")
print("- average_macronutrients_bar_chart.png")
print("- macronutrients_heatmap.png")
print("- top_protein_recipes_scatter_plot.png")
print("- All_Diets_Cleaned.csv")