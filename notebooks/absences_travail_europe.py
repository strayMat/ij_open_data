# %%
# Analyse des données d'Eurostat sur les absences au travail
# L'objectif est de comprendre la tendance des absences au travail dans plusieurs pays européens
# avant et après la pandémie de COVID-19.
import re

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from ij_open_data.constants import DIR2DATA, DIR2IMG

sns.set_context("poster")
sns.set_style("darkgrid")

COLNAME_COUNTRY = "Geopolitical entity (reporting)"
COLNAME_TX_CROISSANCE = "Taux de croissance moyen (%)"
COLNAME_PERIOD = "Période"
# %%

# charge les données eurostat du labor force survey (lfsi_abt_q) et les nettoie
nb_taux_absences = pd.read_csv(DIR2DATA / "eurostat_absences_2025_taux.csv", sep=",")
nb_total_absences = pd.read_csv(DIR2DATA / "eurostat_absences_2025_total.csv", sep=",")

for df in [nb_taux_absences, nb_total_absences]:
    # Build a regex to extract the year and quarter from the TIME_PERIOD column
    df["time_regex"] = df["TIME_PERIOD"].map(lambda x: re.search(r"(\d{4})-Q(\d{1})", x))
    df["datetime"] = pd.to_datetime(
        df["time_regex"].map(lambda x: str(x.group(1)))
        + "-"
        + df["time_regex"].map(lambda x: str((int(x.group(2)) - 1) * 3 + 1).zfill(2))
        + "-01",
        format="%Y-%m-%d",
        errors="coerce",
    )
# Quel est le dernier trimestre disponible pour chaque pays ?
print("Dernier trimestre disponible par pays (taux d'absences):")
print(nb_taux_absences.groupby(COLNAME_COUNTRY)["datetime"].max().sort_values(ascending=False))


# %%
# # Exploration rapide des données nettoyées
# from skrub import Cleaner, TableReport
# nb_total_absences_cleaned = Cleaner(datetime_format="%Y-").fit_transform(
#     nb_taux_absences
# )
# TableReport(nb_total_absences_cleaned)
# print(nb_taux_absences[["geo", "Geopolitical entity (reporting)"]].drop_duplicates())
# %%
def plot_absences_europe(df, countries_dict, language="fr", unite="percentage"):
    """
    Trace le taux d'absence au travail pour une sélection de pays.
    Args:
        df (pd.DataFrame): Données contenant les absences.
        countries_dict (dict): Dictionnaire des pays à tracer, ex: {"Germany": {"color": "#4ECDC4", "fr": "Allemagne"}, ...}
        language (str): Langue pour les labels (par défaut "fr").
    """
    col_country = "Geopolitical entity (reporting)"
    countries_dict_ = countries_dict.copy()
    if unite == "percentage":
        countries_dict_["European Union - 27 countries (from 2020)"] = {"color": "#000000", "fr": "UE (27)"}
    df_plot = df.loc[df[col_country].isin(countries_dict_.keys())].copy()
    df_plot["country_fr"] = df_plot[col_country].map(lambda x: countries_dict_[x]["fr"])

    if language == "fr":
        palette_country = {v["fr"]: v["color"] for v in countries_dict_.values()}
        col_country_label = "country_fr"
        eu_label = "UE (27)"
    elif language == "en":
        palette_country = {k: v["color"] for k, v in countries_dict_.items()}
        col_country_label = col_country
        eu_label = "EU (27)"
        df_plot.loc[df_plot[col_country_label] == "European Union - 27 countries (from 2020)", col_country_label] = (
            eu_label
        )
    else:
        raise ValueError("language must be 'fr' or 'en'")

    covid_year = 2020
    mean_before_covid = (
        df_plot.loc[df_plot["datetime"].dt.year < covid_year].groupby(col_country_label)["OBS_VALUE"].mean()
    ).reset_index()
    mean_after_covid = (
        df_plot.loc[df_plot["datetime"].dt.year > covid_year].groupby(col_country_label)["OBS_VALUE"].mean()
    ).reset_index()

    fig, ax = plt.subplots(figsize=(12, 7))
    sns.lineplot(
        df_plot,
        x="datetime",
        y="OBS_VALUE",
        hue=col_country_label,
        palette=palette_country,
        ax=ax,
    )
    x_min = df_plot["datetime"].min().toordinal()
    x_max = df_plot["datetime"].max().toordinal()
    covid_x = (pd.to_datetime(f"{covid_year}-01-01").toordinal() - x_min) / (x_max - x_min)
    alpha = 0.5

    # Affiche les moyennes avant et après covid
    for country_label, country_color in palette_country.items():
        mean_before_covid_to_plot = mean_before_covid.loc[
            mean_before_covid[col_country_label].values == country_label, "OBS_VALUE"
        ]
        if not mean_before_covid_to_plot.empty:
            plt.axhline(
                y=mean_before_covid_to_plot.values[0],
                color=country_color,
                linestyle="--",
                xmax=covid_x,
                alpha=alpha,
            )
        mean_after_covid_to_plot = mean_after_covid.loc[
            mean_after_covid[col_country_label].values == country_label, "OBS_VALUE"
        ]
        if not mean_after_covid_to_plot.empty:
            plt.axhline(
                y=mean_after_covid_to_plot.values[0],
                color=country_color,
                linestyle="-.",
                xmin=covid_x,
                alpha=alpha,
            )
    # affiche les ticks uniquement chaque année
    current_ticks = plt.gca().get_xticks()
    plt.gca().set_xticks(current_ticks[::4])
    plt.legend(bbox_to_anchor=(0.5, -0.35), loc="upper center", ncol=3)
    years = pd.date_range(
        start=df_plot["datetime"].min().replace(month=1, day=1),
        end=df_plot["datetime"].max().replace(month=1, day=1),
        freq="YS",
    )
    plt.gca().set_xticks(years)
    plt.gca().set_xticklabels([str(y.year) for y in years], rotation=45)
    # Ajoute la rupture de série en 2021
    plt.axvline(x=pd.to_datetime("2021-01-01"), color="grey", linestyle=":", alpha=0.7)
    plt.text(
        pd.to_datetime("2021-01-01"),
        plt.ylim()[1],
        "Rupture de série en 2021",
        ha="left",
        fontsize=16,
        color="grey",
    )
    # x et y labels
    ax.set_xlabel("Année")
    y_label = "Absences au travail toutes causes\n"
    if unite == "percentage":
        y_label += "(pourcentage des employés)"
    elif unite == "total":
        y_label += "(nombre total d'absences)"
    ax.set_ylabel(y_label)

    # Réorganise la légende pour mettre "UE (27)" en premier
    handles, labels = ax.get_legend_handles_labels()
    if unite == "percentage":
        idx = labels.index(eu_label)
        # Place "UE (27)" en premier
        handles = [handles[idx]] + handles[:idx] + handles[idx + 1 :]
        labels = [labels[idx]] + labels[:idx] + labels[idx + 1 :]
        ax.legend(handles, labels, bbox_to_anchor=(1.05, 1), loc="upper left", ncol=1, borderaxespad=0.0)
    else:
        ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left", ncol=1, borderaxespad=0.0)
    return ax


# %%
west_europe_absences = {
    "Portugal": {"color": "#45DB00", "fr": "Portugal"},
    # "United Kingdom": {"color": "#3A8E02", "fr": "Royaume-Uni"}, # not interesting since no data after 2020
    "France": {"color": "#F11A1A", "fr": "France"},
    "Spain": {"color": "#F1DA09", "fr": "Espagne"},
    "Greece": {"color": "#25CDF7", "fr": "Grèce"},
    "Netherlands": {"color": "#1714C9", "fr": "Pays-Bas"},
    "Belgium": {"color": "#DA12BF", "fr": "Belgique"},
    "Italy": {"color": "#037A2B", "fr": "Italie"},
}

nordik_absences = {
    "Norway": {"color": "#030185", "fr": "Norvège"},
    "Finland": {"color": "#FF6B6B", "fr": "Finlande"},
    "Denmark": {"color": "#645631", "fr": "Danemark"},
    "Sweden": {"color": "#4ECDC4", "fr": "Suède"},
}

east_europe_absences = {
    "Slovakia": {"color": "#F3722C", "fr": "Slovaquie"},
    "Serbia": {"color": "#F15BB5", "fr": "Serbie"},
    "Latvia": {"color": "#2533F7", "fr": "Lettonie"},
    "Estonia": {"color": "#720026", "fr": "Estonie"},
    "Lithuania": {"color": "#ECC206", "fr": "Lituanie"},
    "Romania": {"color": "#119400", "fr": "Roumanie"},
    "Bulgaria": {"color": "#00F5D4", "fr": "Bulgarie"},
}

central_europe_absences = {
    "Germany": {"color": "#FF0B0B", "fr": "Allemagne"},
    "Poland": {"color": "#4361EE", "fr": "Pologne"},
    "Hungary": {"color": "#07661B", "fr": "Hongrie"},
    "Slovenia": {"color": "#8E0202", "fr": "Slovénie"},
    "Czechia": {"color": "#3A94AF", "fr": "République tchèque"},
    "Austria": {"color": "#F9844A", "fr": "Autriche"},
}

other_absences_small = {
    "Malta": {"color": "#F3722C", "fr": "Malte"},
    # "North Macedonia": {"color": "#FF0000", "fr": "Macédoine du Nord"},not enough data points after covid
    "Luxembourg": {"color": "#00F5D4", "fr": "Luxembourg"},
    "Ireland": {"color": "#119400", "fr": "Irlande"},
    "Iceland": {"color": "#1900FF", "fr": "Islande"},
    "Croatia": {"color": "#720026", "fr": "Croatie"},
    "Cyprus": {"color": "#006EFF", "fr": "Chypre"},
    #'Montenegro' : {"color": "#D9FF00", "fr": "Monténégro"} not enough data points after covid
}
# %%
# Plot en taux d'absence
for country_dict, country_class in zip(
    [west_europe_absences, central_europe_absences, east_europe_absences, nordik_absences, other_absences_small],
    ["west_eu", "central_eu", "east_eu", "nordik", "others"],
    strict=False,
):
    print(f"Countries: {list(country_dict.keys())}")
    ax = plot_absences_europe(nb_taux_absences, country_dict)
    plt.savefig(DIR2IMG / f"eurostats_work_absences_{country_class}_taux.png", bbox_inches="tight")
    plt.show()
# %%
# Plot en nombre total d'absences
for country_dict, country_class in zip(
    [west_europe_absences, central_europe_absences, east_europe_absences, nordik_absences, other_absences_small],
    ["west_eu", "east_eu", "central_eu", "nordik", "others"],
    strict=False,
):
    print(f"Countries: {list(country_dict.keys())}")
    ax = plot_absences_europe(nb_total_absences, country_dict, unite="total")
    plt.savefig(DIR2IMG / "eurostats" / f"eurostats_work_absences_{country_class}_totaux.png", bbox_inches="tight")
    plt.show()
# %%
print(
    f"missing countries:\n {set(nb_taux_absences['Geopolitical entity (reporting)'].unique()) - set(list(west_europe_absences.keys()) + list(central_europe_absences) + list(east_europe_absences.keys()) + list(nordik_absences.keys()) + list(other_absences_small.keys()))}"
)
# %% [markdown]
# ## Calcul des taux d'absences
# %%
# calcule les taux d'absences pour tous les pays

mask_sex = nb_total_absences["sex"] == "T"
# mask_quarter = nb_total_absences["datetime"].dt.quarter == quarter
nb_total_absences_q1 = nb_total_absences[mask_sex].copy().reset_index(drop=True)

nb_total_absences_q1["year"] = nb_total_absences_q1["datetime"].dt.year
nb_total_absences_q1["quarter"] = nb_total_absences_q1["datetime"].dt.quarter

growth_rate_total_numbers = (
    nb_total_absences_q1.sort_values("year")
    .groupby([COLNAME_COUNTRY, "quarter"])
    .apply(lambda x: x.set_index("year")["OBS_VALUE"].pct_change() * 100, include_groups=True)
    .reset_index()
    .rename(columns={"OBS_VALUE": COLNAME_TX_CROISSANCE})
)

# Compute mean on periods.
start_year_p1 = 2011
end_year_p1 = 2019
start_year_p2 = 2024
end_year_p2 = 2024
# period takes into account minus one year because we are looking at growth rates (so growth rate for year N is computed using data from year N and N-1)
period_1 = f"{start_year_p1}-{end_year_p1}"
period_2 = f"{start_year_p2}-{end_year_p2}"

# pre-covid
mean_growth_rate_pre_2019 = growth_rate_total_numbers[
    (growth_rate_total_numbers["year"] <= end_year_p1) & (growth_rate_total_numbers["year"] >= start_year_p1)
]
mean_growth_rate_pre_2019[COLNAME_PERIOD] = period_1
# post-covid
mean_growth_rate_post_2020 = growth_rate_total_numbers[
    (growth_rate_total_numbers["year"] >= start_year_p2) & (growth_rate_total_numbers["year"] <= end_year_p2)
]
mean_growth_rate_post_2020[COLNAME_PERIOD] = period_2
all_growth_rates = (
    pd.concat([mean_growth_rate_pre_2019, mean_growth_rate_post_2020])
    .reset_index()
    .sort_values(by=[COLNAME_COUNTRY, "quarter", "Période"])
)

# all_growth_rates[COLNAME_PERIOD] = all_growth_rates[COLNAME_PERIOD].map(
#     lambda x: "2010-2019" if x == "2010-2019" else "2021-2024"
# )
## Histplot of growth rates
LABEL_ALL_EU_LONG = "European Union - 27 countries (from 2020)"
LABEL_ALL_EU = "UE (27)"
growth_rates_subset_countries = all_growth_rates[
    all_growth_rates[COLNAME_COUNTRY].isin([
        *west_europe_absences.keys(),
        *central_europe_absences.keys(),
        *east_europe_absences.keys(),
        *nordik_absences.keys(),
        LABEL_ALL_EU_LONG,
    ])
]
growth_rates_subset_countries.loc[
    growth_rates_subset_countries[COLNAME_COUNTRY] == LABEL_ALL_EU_LONG, COLNAME_COUNTRY
] = LABEL_ALL_EU

order = (
    growth_rates_subset_countries[(growth_rates_subset_countries[COLNAME_PERIOD] == period_2)]
    .groupby(COLNAME_COUNTRY)
    .agg(**{COLNAME_TX_CROISSANCE: pd.NamedAgg(COLNAME_TX_CROISSANCE, "mean")})
    .reset_index()
    .sort_values(by=COLNAME_TX_CROISSANCE, ascending=False)[COLNAME_COUNTRY]
    .tolist()
)
if LABEL_ALL_EU in order:
    order.remove(LABEL_ALL_EU)
order = [LABEL_ALL_EU] + order
# Sort by country order, then by period
growth_rates_subset_countries_sorted = growth_rates_subset_countries.copy()
growth_rates_subset_countries_sorted[COLNAME_COUNTRY] = pd.Categorical(
    growth_rates_subset_countries_sorted[COLNAME_COUNTRY], categories=order, ordered=True
)
growth_rates_subset_countries_sorted = growth_rates_subset_countries_sorted.sort_values([
    COLNAME_COUNTRY,
    "quarter",
    COLNAME_PERIOD,
])

plt.figure(figsize=(12, 7))
# Sort by COLNAME_TX_CROISSANCE in the last period (2020-2025)
colors = sns.color_palette()
palette = [colors[0], colors[1]]
if start_year_p2 == 2024:
    palette = [colors[0], colors[2]]
sns.barplot(
    data=growth_rates_subset_countries,
    x=COLNAME_COUNTRY,
    y=COLNAME_TX_CROISSANCE,
    hue=COLNAME_PERIOD,
    order=order,
    errorbar="se",
    palette=palette,
)
plt.xticks(rotation=90)
plt.ylabel("Taux de croissance moyen \n des absences au travail (%)")
plt.xlabel("Pays")
plt.grid(axis="x", linestyle="--", alpha=0.7)
plt.savefig(DIR2IMG / "eurostats" / f"growth_rates_work_absences_eurostats_p2_{period_2}.png", bbox_inches="tight")
plt.show()
# %%
mean_growth_rates = (
    growth_rates_subset_countries_sorted.groupby([COLNAME_COUNTRY, COLNAME_PERIOD])[COLNAME_TX_CROISSANCE]
    .agg(["mean", lambda x: np.std(x) / np.sqrt(len(x))])
    .unstack()
)

selected_countries = ["Austria", "Romania", "Bulgaria", "Denmark", "Spain", "Czechia", "Netherlands", "France"]
growth_rates_list = [
    f"{country} (+{mean_growth_rates.loc[country, ('mean', period_2)]:.2f} %)" for country in selected_countries
]
print(", ".join(growth_rates_list))
