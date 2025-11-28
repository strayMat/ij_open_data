# %%

# Explore les données opendata de la CNAM sur les IJ, ayant servie à l'Etude et Résultats 2024 de la DREES
# Objectif: avoir les taux de croissance annuels (non renseignés dans l'ER)
import os
import re

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.ticker import MultipleLocator

from ij_open_data.constants import DIR2CLEAN_IJ, DIR2IMG_CNAM, DIR2RESULTS
from ij_open_data.scrap_open_data_cnam_ij import LABEL_NB_JOURS

os.makedirs(DIR2IMG_CNAM, exist_ok=True)
sns.set_theme(style="whitegrid", context="talk")


# utils
def age_key(age):
    """Key function to sort age classes numerically."""
    m = re.search(r"\d+", str(age))
    return int(m.group()) if m else 999


LABEL_MAP = {
    "maladie-hors-derogatoires": "Maladie",
    "accident-du-travail-maladie-professionnelle": "AT-MP",
    "maternite-adoption": "Maternité",
}
# %%
# Analyse tout âge
# %% Plotting
# Paramètres
category = "TOUT_AGE"
all_ij = pd.read_csv(DIR2CLEAN_IJ / "ij_cnam_par_age.csv")
ij_tt_age = all_ij[all_ij["Tranche d'âge"] == category]

for unit in ij_tt_age["unit"].unique():
    df_unit = ij_tt_age[ij_tt_age["unit"] == unit]
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.lineplot(data=df_unit, x="Année", y="value", hue="Type IJ", marker="o")
    plt.xlabel("Année")
    plt.ylabel(unit)
    # Add a minor tick for each year
    ax.xaxis.set_minor_locator(MultipleLocator(1))
    ax.tick_params(axis="x", which="minor", labelbottom=False)
    ax.grid(which="minor", linestyle=":", linewidth="0.7", color="gray")
    # Replace legend labels and position
    handles, labels = ax.get_legend_handles_labels()
    new_labels = [LABEL_MAP.get(l, l) for l in labels]
    ax.legend(handles, new_labels, title="Type d'IJ", loc="upper left", ncol=2)
    plt.savefig(
        DIR2IMG_CNAM / f"ij_cnam_tout_age_{unit.replace(' ', '_').replace('\n', '_')}.png",
        bbox_inches="tight",
    )
# %%
# Analyse par âge
for type_ij in all_ij["Type IJ"].unique():
    df_type_ij = all_ij[all_ij["Type IJ"] == type_ij]

    # plt.savefig(DIR2IMG_CNAM / f"ij_cnam_par_age_{type_ij}.png", bbox_inches='tight')

# %% Plotting by ij_type and unit, lignes par classe d'âge (hors inconnu et TOUT_AGE)
# Palette cohérente pour les classes d'âge (du plus jeune au plus âgé)
age_classes = [a for a in all_ij["Tranche d'âge"].unique() if a not in ["inconnu", "TOUT_AGE"]]


age_classes_sorted = sorted(age_classes, key=age_key)
palette = sns.color_palette("viridis", n_colors=len(age_classes_sorted))
palette.reverse()  # Inverser pour que les couleurs sombres soient pour les âges élevés
for type_ij in all_ij["Type IJ"].unique():
    for unit in all_ij["unit"].unique():
        df = all_ij[
            (all_ij["Type IJ"] == type_ij)
            & (all_ij["unit"] == unit)
            & (all_ij["Tranche d'âge"].isin(age_classes_sorted))
        ]
        if df.empty:
            continue
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.lineplot(
            data=df,
            x="Année",
            y="value",
            hue="Tranche d'âge",
            marker="o",
            palette=dict(zip(age_classes_sorted, palette, strict=False)),
            hue_order=age_classes_sorted,
        )
        # Ajoute le label sur le dernier point de chaque ligne
        for age in age_classes_sorted:
            df_age = df[df["Tranche d'âge"] == age]
            if df_age.empty:
                continue
            last_row = df_age.loc[df_age["Année"].idxmax()]
            ax.text(
                last_row["Année"] + 0.2,
                last_row["value"],
                str(age),
                color=dict(zip(age_classes_sorted, palette, strict=False))[age],
                fontsize=20,
                fontweight="bold",
                va="center",
                ha="left",
            )
        plt.title(f"{type_ij} - {unit}")
        plt.xlabel("Année")
        plt.ylabel(unit)
        ax.xaxis.set_minor_locator(MultipleLocator(1))
        ax.tick_params(axis="x", which="minor", labelbottom=False)
        ax.grid(which="minor", linestyle=":", linewidth="0.7", color="gray")
        # ax.legend(loc='center left', bbox_to_anchor=(1, 0.5), ncol=2, title="Tranche d'âge")
        ax.legend_.remove()  # Supprime la légende pour éviter la surcharge visuelle
        plt.savefig(
            DIR2IMG_CNAM
            / f"ij_cnam_par_age_{type_ij.replace(' ', '_')}_{unit.replace(' ', '_').replace('\n', '_')}.png",
            bbox_inches="tight",
        )
        # plt.close(fig)
# %%
# Analyse par âge et sexe pour les arrêts maladie
all_ij_sexe = pd.read_csv(DIR2CLEAN_IJ / "ij_cnam_par_age_sexe.csv")

age_classes = [a for a in all_ij_sexe["Tranche d'âge"].unique() if a not in ["inconnu", "TOUT_AGE"]]
age_classes_sorted = sorted(age_classes, key=age_key)
palette = sns.color_palette("viridis", n_colors=len(age_classes_sorted))
palette.reverse()  # Inverser pour que les couleurs sombres soient pour les âges élevés

# Visualisation du nombre total de jours d'arrêts maladie par sexe
df_sexe = all_ij_sexe[
    (all_ij_sexe["unit"] == "Nombre de jours d'arrêt\n(en millions)") & (all_ij_sexe["Tranche d'âge"].isin(age_classes))
]

fig, ax = plt.subplots(figsize=(10, 6))
sns.lineplot(
    data=df_sexe,
    x="Année",
    y="value",
    hue="Tranche d'âge",
    style="Sexe",  # Différencie le sexe par le type de ligne
    markers=True,
    dashes=True,
    palette=dict(zip(age_classes_sorted, palette, strict=False)),
    hue_order=age_classes_sorted,
)
# Ajoute le label sur le dernier point de chaque ligne (seulement pour les femmes)
df_one_sexe = df_sexe[df_sexe["Sexe"] == "femmes"]
for i, age in enumerate(age_classes_sorted):
    df_age = df_one_sexe[df_one_sexe["Tranche d'âge"] == age]
    if df_age.empty:
        continue
    last_row = df_age.loc[df_age["Année"].idxmax()]
    x_offset = 0.2
    y_offset = 1 * (i % 2)  # Décalage vertical pour éviter le chevauchement
    if age == "35-39":
        y_offset = 0  # Décalage spécifique
        x_offset = 2
    # Ajoute une ligne horizontale pour relier le texte au point
    ax.hlines(
        y=last_row["value"],
        xmin=last_row["Année"] + 0.2,
        xmax=last_row["Année"] + x_offset,
        colors=dict(zip(age_classes_sorted, palette, strict=False))[age],
        linewidth=0.7,
    )
    ax.text(
        last_row["Année"] + x_offset,
        last_row["value"] + y_offset,
        str(age),
        color=dict(zip(age_classes_sorted, palette, strict=False))[age],
        fontsize=20,
        fontweight="bold",
        va="center",
        ha="left",
    )
# Affiche une légende uniquement pour le style de ligne (Sexe)
handles, labels = ax.get_legend_handles_labels()
sex_labels = df_sexe["Sexe"].unique()
sex_handles = [h for h, lab in zip(handles, labels, strict=False) if lab in sex_labels]
ax.legend(sex_handles, sex_labels, title="Sexe", loc="upper left")
plt.xlabel("Année")
plt.ylabel("Nombre de jours d'arrêt (en millions)")
ax.xaxis.set_minor_locator(MultipleLocator(1))
ax.tick_params(axis="x", which="minor", labelbottom=False)
ax.grid(which="minor", linestyle=":", linewidth="0.7", color="gray")
plt.savefig(
    DIR2IMG_CNAM / "ij_cnam_par_sexe_Nombre_de_jours_d'arrêt_(en_millions).png",
    bbox_inches="tight",
)
# TODO: Add on the right of this graph, the mean growth rate level for the period 2010-2019 and 2019-2023  for male/female and age group
# %%

# Exploration par NAF
all_ij_naf = pd.read_csv(DIR2CLEAN_IJ / "ij_cnam_par_naf.csv")

# Plotting NAF data - filter to specific Type IJ only
target_type_ij = [
    "accident-du-travail-maladie-professionnelle",
    "maladie-hors-derogatoires",
]

# Filter to only target Type IJ categories
ij_naf_filtered = all_ij_naf[(all_ij_naf["Type IJ"].isin(target_type_ij)) & (all_ij_naf["Libellé"] != "Ensemble")]
for unit in ij_naf_filtered["unit"].unique():
    for type_ij in target_type_ij:
        df_plotted = ij_naf_filtered[(ij_naf_filtered["unit"] == unit) & (ij_naf_filtered["Type IJ"] == type_ij)]

        # df_plotted["code_libelle"] = (
        #     df_plotted["Libellé"] + " - " + df_plotted["Type IJ"]
        # )
        fig, ax = plt.subplots(figsize=(12, 8))
        sns.lineplot(
            data=df_plotted,
            x="Année",
            y="value",
            hue="Libellé",
            marker="o",
            palette=sns.husl_palette(n_colors=21),
        )
        plt.xlabel("Année")
        plt.ylabel(unit)
        plt.title(f"Évolution par Type IJ : {type_ij}")
        # Add a minor tick for each year
        ax.xaxis.set_minor_locator(MultipleLocator(1))
        ax.tick_params(axis="x", which="minor", labelbottom=False)
        ax.grid(which="minor", linestyle=":", linewidth="0.7", color="gray")
        plt.legend(title="Libellé Naf", loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=3)
        plt.savefig(
            DIR2IMG_CNAM / f"ij_cnam_par_naf_{unit.replace(' ', '_').replace('\n', '_')}.png",
            bbox_inches="tight",
        )
        plt.show()

# %%
# Plotly version for interactive plot
# pl_unit = "Nombre de jours d'arrêt\n(en millions)"
# plt_type_ij = "maladie-hors-derogatoires"
# fig = px.line(
#     ij_naf_filtered[
#         (ij_naf_filtered["unit"] == pl_unit)
#         & (ij_naf_filtered["Type IJ"].isin([plt_type_ij]))
#     ],
#     x="Année",
#     y="value",
#     color="Libellé",
#     # line_dash="Type IJ",
#     facet_col="unit",
#     facet_col_wrap=1,
#     title="Évolution des IJ par NAF et Type IJ",
# )
# fig.update_layout(showlegend=False)
# fig.update_layout(height=800, width=1000)
# # fig.write_html(DIR2IMG_CNAM / "ij_cnam_par_naf.html")
# fig.show()

# %%

# # Calcul des taux de croissance annuels moyens par période

# Question 1 : Vérifier les chiffres de l'ER selon lequel le taux de croissance annuel moyen des arrêts maladie a changé après 2019 (avant et après la pandémie) ?
# Question 2 : Est-ce ce que le changement est encore visible si on exclut le taux de croissance 2019-2020 (année de la pandémie) ?
#
# FIXME: Je ne trouve pas en terme de montants, de nombre d'arrêt ou de nombre de jours d'arrêt exactement le même chiffre que dans l'ER. J'ai vérifié mon code ligne à ligne et j'ai l'impression que ça fait bien ce que je pense. De plus, ça ne peut pas être qu'ils ont utilisé une série différente de la mienne car les chiffres aggrégés sur l'ensemble de la population sont les mêmes dans leurs différents tableaux.
category = "age"
df_ij = pd.read_csv(DIR2CLEAN_IJ / f"ij_cnam_par_{category}.csv")
if category == "age":
    df_ij_tt_category = df_ij[df_ij["Tranche d'âge"] == "TOUT_AGE"]
elif category == "region":
    df_ij_tt_category = df_ij[df_ij["Libellé"] == "Ensemble"]
df_arret_maladie_tt_category = df_ij_tt_category[df_ij_tt_category["Type IJ"] == "maladie-hors-derogatoires"]
# df_arret_maladie_tt_category[df_arret_maladie_tt_category["unit"] == LABEL_NB_JOURS]
# If we input the arret derogatoire, this does fix the discrepancy between our results and the ER results
w_derogatoire = False
if w_derogatoire:
    derogatoires_millions = pd.DataFrame([32_881_839, 16_199_804, 40_801_818, 349_694]) // 1e6
    mask_post_covid = (df_ij_tt_category["unit"] == LABEL_NB_JOURS) & (df_ij_tt_category["Année"] >= 2020)
    df_arret_maladie_tt_category.loc[mask_post_covid, "value"] += derogatoires_millions.values.flatten()


# Calculate annual growth rates for each unit
growth_rate_arret_maladie_tt_category = (
    df_arret_maladie_tt_category.sort_values("Année")
    .groupby("unit")
    .apply(lambda x: x.set_index("Année")["value"].pct_change())
    .melt(ignore_index=False, value_name="growth_rate")
    .reset_index()
)
# remove all parentheses in unit values
growth_rate_arret_maladie_tt_category["unit"] = growth_rate_arret_maladie_tt_category["unit"].str.replace(
    r"\s*\(.*\)\s*", "", regex=True
)
# %%
agg_dict = {
    "Taux de croissance moyen (%)": pd.NamedAgg(column="growth_rate", aggfunc=lambda x: x.mean() * 100),
    "Période": pd.NamedAgg(
        column="Année", aggfunc=lambda x: str(min(x)) + "-" + str(max(x))
    ),  # -1 because we are looking at the data of the year N-1 to compute the growth rate for year N which is included, so the studied period is min(years)-1 to max(years)
}
start_year_p1 = 2010
end_year_p1 = 2019
start_year_p2 = 2020
end_year_p2 = 2023
start_year_p3 = 2021
end_year_p3 = 2023

mean_growth_rate_pre_2019 = (
    growth_rate_arret_maladie_tt_category[
        (growth_rate_arret_maladie_tt_category["Année"] >= start_year_p1)
        & (growth_rate_arret_maladie_tt_category["Année"] <= end_year_p1)
    ]
    .groupby("unit")
    .agg(**agg_dict)
)
mean_growth_rate_post_2019 = (
    growth_rate_arret_maladie_tt_category[growth_rate_arret_maladie_tt_category["Année"] >= start_year_p2]
    .groupby("unit")
    .agg(**agg_dict)
)
# exclude 2020
mean_growth_rate_post_2020 = (
    growth_rate_arret_maladie_tt_category[growth_rate_arret_maladie_tt_category["Année"] >= start_year_p3]
    .groupby("unit")
    .agg(**agg_dict)
)
# growth_rate_2023 = (
#     growth_rate_arret_maladie_tt_category[
#         growth_rate_arret_maladie_tt_category["Année"] >= 2023
#     ]
#     .groupby("unit")
#     .agg(**agg_dict)
# )
all_growth_rates = pd.concat(
    [mean_growth_rate_pre_2019, mean_growth_rate_post_2019, mean_growth_rate_post_2020],
    axis=0,
).reset_index()
# pivot by units
all_growth_rates = all_growth_rates.pivot(index="unit", columns="Période", values="Taux de croissance moyen (%)")
all_growth_rates.round(2).to_csv(DIR2RESULTS / "mean_growth_rate_arret_maladie_tt_age.csv")
all_growth_rates
# %%}")
#
# taux de croissance pour les arrêts maladies:
# Valeurs de 2010 à 2019 extraites du fichier : 2009-a-2023_ij-maladie-hors-derogatoires-selon-age_serie-annuelle.xlsx, onglet Graph2.

nb_beneficiaires = [4592431, 4700234, 4607437, 4691446, 4582189, 4773240, 4868392, 4928043, 5035167, 5078020]
nb_jours_arrets = [
    200567081,
    202946590,
    205076919,
    204256953,
    211665940,
    217877165,
    226581529,
    233718607,
    239553911,
    245124624,
]
nb_arrets = [6433056, 6577668, 6445983, 6544544, 6420422, 6729644, 6896297, 6973811, 7106484, 7180525]


def compute_mean_growth_rate(values):
    growth_rates = [(values[i + 1] / values[i] - 1) for i in range(len(values) - 1)]
    print(growth_rates)
    return 100 * sum(growth_rates) / len(growth_rates)


for label, values in [("Bénéficiaires", nb_beneficiaires), ("Arrêts", nb_arrets), ("Jours d'arrêt", nb_jours_arrets)]:
    mean_growth_rate = compute_mean_growth_rate(values)
    print(f"Taux de croissance moyen annuel {label} 2010-2019: {mean_growth_rate:.2f}%")

# %%
