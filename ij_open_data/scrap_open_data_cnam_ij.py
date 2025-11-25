import os
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

from ij_open_data.constants import DIR2CLEAN_IJ, DIR2RAW_IJ

# On va scraper la page principale des IJ de la CNAM pour retrouver les liens vers les fichiers Excel

# unit label
LABEL_MNT = "Montant des IJ\n(en Md€)"
LABEL_NB_ARR = "Nombre d'arrêts\n(en milliers)"
LABEL_NB_JOURS = "Nombre de jours d'arrêt\n(en millions)"


def get_links_from_main_page(base_url):
    resp = requests.get(base_url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]  # type: ignore
        # On ne garde que les liens internes pertinents
        if href.startswith("/etudes-et-donnees/") and "ij" in href:
            full_url = urljoin(base_url, href)
            links.append(full_url)
    return list(set(links))


def find_xlsx_url_in_page(url):
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    for a in soup.find_all("a", href=True):
        href = a["href"]  # type: ignore
        if ".xlsx" in href:
            return urljoin(url, href)
    return None


def download_xlsx(xlsx_url, dest_dir):
    filename = xlsx_url.split("/")[-1].split("?")[0]
    dest_path = os.path.join(dest_dir, filename)
    if os.path.exists(dest_path):
        print(f"Déjà téléchargé : {filename}")
        return
    resp = requests.get(xlsx_url)
    resp.raise_for_status()
    with open(dest_path, "wb") as f:
        f.write(resp.content)
    print(f"Téléchargé : {filename}")


def scrap_ameli_for_ij():
    """
    Scrape la page de la CNAM pour télécharger les fichiers Excel des IJ
    """

    base_url = "https://www.assurance-maladie.ameli.fr/etudes-et-donnees/par-theme/prestations-en-especes/indemnites-journalieres-arret-de-travail"

    os.makedirs(DIR2RAW_IJ, exist_ok=True)
    links = get_links_from_main_page(base_url)
    print(f"{len(links)} liens trouvés")
    for link in links:
        print(f"Analyse : {link}")
        xlsx_url = find_xlsx_url_in_page(link)
        if xlsx_url:
            print(f"  Fichier trouvé : {xlsx_url}")
            download_xlsx(xlsx_url, DIR2RAW_IJ)
        else:
            print("  Aucun fichier .xlsx trouvé sur cette page.")


def clean_melt_df(
    df, id_vars, type_ij, unit_label, var_name="Année", value_name="value"
):
    """Transforme le DataFrame de l'open data au format (catégoris, année) en un format long (catégorie, ). Nettoie et convertis en unité lisibles les valeurs des IJ.

    Args:
        df (pd.DataFrame): Le DataFrame à transformer.
        id_vars (list): Les colonnes à utiliser comme identifiants (ex. ["Libellé", "Tranche d'âge"] pour la série).
        type_ij (str): Le type d'indemnité journalière.
        unit_label (str): L'unité de mesure des IJ.
        var_name (str, optional): Le nom de la variable pour les années. Defaults to "Année".
        value_name (str, optional): Le nom de la variable pour les valeurs. Defaults to "value".

    Returns:
        pd.DataFrame: Le DataFrame transformé.
    """
    df_tidy = df.melt(id_vars=id_vars, var_name=var_name, value_name=value_name)
    df_tidy["Type IJ"] = type_ij
    df_tidy["unit"] = unit_label
    if unit_label == LABEL_MNT:
        df_tidy["value"] = (
            df_tidy["value"] / 1_000_000_000
        )  # convertir en millions d'euros:
    elif unit_label == LABEL_NB_ARR:
        df_tidy["value"] = df_tidy["value"] / 1_000  # convertir en milliers:
    elif unit_label == LABEL_NB_JOURS:
        df_tidy["value"] = df_tidy["value"] / 1_000_000  # convertir en millions:
    return df_tidy


# Clean the data
def clean_data_cnam():
    DIR2CLEAN_IJ.mkdir(parents=True, exist_ok=True)

    ## Données selon l'âge
    type_ijs = [
        "maladie-hors-derogatoires",
        "accident-du-travail-maladie-professionnelle",
        "maternite-adoption",
    ]
    all__ij_list = []
    for type_ij in type_ijs:
        print(f"Charge et transforme les données IJ selon l'âge de type : {type_ij}")
        # Chargement des données
        start_year = "2009"
        if type_ij == "maternite-adoption":
            start_year = "2010"  # pas de données avant 2010 pour ce type d'IJ
        for unit_label, sheet_name in [
            (LABEL_NB_ARR, "tous Nb arr, f(âge)"),
            (LABEL_NB_JOURS, "tous Nb jour, f(âge)"),
            (LABEL_MNT, "tous Mnt, f(âge)"),
        ]:
            # print(f"  - {unit_label} / {sheet_name}")
            df = pd.read_excel(
                DIR2RAW_IJ
                / f"{start_year}-a-2023_ij-{type_ij}-selon-age_serie-annuelle.xlsx",
                sheet_name=sheet_name,
                skiprows=7,
            )
            df_tidy = clean_melt_df(
                df,
                id_vars=["Libellé", "Tranche d'âge"],
                type_ij=type_ij,
                unit_label=unit_label,
            )
            all__ij_list.append(df_tidy)
    all__ij = pd.concat(all__ij_list, ignore_index=True)
    all__ij.to_csv(DIR2CLEAN_IJ / "ij_cnam_par_age.csv", index=False)

    ## Données d'arrêts maladie selon l'âge ET le sexe
    sexe_list = ["femmes", "hommes"]
    all__ij_sexe_list = []
    for sexe in sexe_list:
        print(
            f"Charge et transforme les données IJ de maladie-hors-derogatoires selon l'âge et le sexe: {sexe}"
        )
        # Chargement des données
        for unit_label, sheet_name in [
            (LABEL_NB_ARR, "tous Nb arr, f(âge)"),
            (LABEL_NB_JOURS, "tous Nb jour, f(âge)"),
            (LABEL_MNT, "tous Mnt, f(âge)"),
        ]:
            df = pd.read_excel(
                DIR2RAW_IJ
                / f"2009-a-2023_ij-maladie-hors-derogatoires-selon-age-{sexe}_serie-annuelle.xlsx",
                sheet_name=sheet_name,
                skiprows=7,
            )
            df_tidy = clean_melt_df(
                df,
                id_vars=["Libellé", "Tranche d'âge"],
                type_ij="maladie-hors-derogatoires",
                unit_label=unit_label,
            )
            all__ij_sexe_list.append(df_tidy)
    all__ij_sexe = pd.concat(all__ij_sexe_list, ignore_index=True)
    all__ij_sexe.to_csv(DIR2CLEAN_IJ / "ij_cnam_par_age_sexe.csv", index=False)

    ## Données selon le code NAF
    type_ijs_naf = [
        "maladie-hors-derogatoires",
        "accident-du-travail-maladie-professionnelle",
        "maladie-temps-partiel-therapeutique",
        "maternite-adoption",
    ]
    all__ij_naf_list = []
    for type_ij in type_ijs_naf:
        for unit_label, sheet_name in [
            (LABEL_NB_ARR, "tous Nb arr, f(sectNAF)"),
            (LABEL_NB_JOURS, "tous Nb jour, f(sectNAF)"),
            (LABEL_MNT, "tous Mnt, f(sectNAF)"),
        ]:
            # print(f"  - {unit_label} / {sheet_name}")
            df = pd.read_excel(
                DIR2RAW_IJ
                / f"2014-a-2023_ij-{type_ij}-selon-code-naf-employeur_serie-annuelle.xlsx",
                sheet_name=sheet_name,
                skiprows=7,
            )
            df_tidy = clean_melt_df(
                df,
                id_vars=["Libellé", "Code"],
                type_ij=type_ij,
                unit_label=unit_label,
            )
            all__ij_naf_list.append(df_tidy)
    all__ij_naf = pd.concat(all__ij_naf_list, ignore_index=True)
    all__ij_naf.to_csv(DIR2CLEAN_IJ / "ij_cnam_par_naf.csv", index=False)

    # données d'arrêt maladie par région
    print("Charge et transforme les données IJ selon région de type arrêt maladie")
    all__ij_region_list = []
    # pivot from wide to long format
    for unit_label, sheet_name in [
        (LABEL_NB_ARR, "tous Nb arr, f(rég)"),
        (LABEL_NB_JOURS, "tous Nb jour, f(rég)"),
        (LABEL_MNT, "tous Mnt, f(rég)"),
    ]:
        # print(f"  - {unit_label} / {sheet_name}")
        df = pd.read_excel(
            DIR2RAW_IJ
            / "2009-a-2023_ij-maladie-hors-derogatoires-selon-region_serie-annuelle.xlsx",
            sheet_name=sheet_name,
            skiprows=7,
        )
        df_tidy = clean_melt_df(
            df,
            id_vars=["Libellé", "Code"],
            type_ij="maladie-hors-derogatoires",
            unit_label=unit_label,
        )
        all__ij_region_list.append(df_tidy)
    all__ij_region = pd.concat(all__ij_region_list, ignore_index=True)
    all__ij_region.to_csv(DIR2CLEAN_IJ / "ij_cnam_par_region.csv", index=False)


if __name__ == "__main__":
    # scrap_ameli_for_ij()
    clean_data_cnam()
