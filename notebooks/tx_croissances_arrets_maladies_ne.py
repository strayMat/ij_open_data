# %%
# Croissances et arrêts de maladies aux Pays-Bas, données CBS
import re
from io import StringIO

import pandas as pd

# %%
# Données néérlandaises, @CBS2025
raw = """;Ziekteverzuim
2e kwartaal 2015;3,7
3e kwartaal 2015;3,5
4e kwartaal 2015;3,9
1e kwartaal 2016;4,3
2e kwartaal 2016;3,8
3e kwartaal 2016;3,5
4e kwartaal 2016;4,1
1e kwartaal 2017;4,3
2e kwartaal 2017;3,9
3e kwartaal 2017;3,7
4e kwartaal 2017;4,2
1e kwartaal 2018;4,9
2e kwartaal 2018;4,1
3e kwartaal 2018;3,9
4e kwartaal 2018;4,3
1e kwartaal 2019;4,7
2e kwartaal 2019;4,3
3e kwartaal 2019;4,0
4e kwartaal 2019;4,5
1e kwartaal 2020;5,2
2e kwartaal 2020;4,5
3e kwartaal 2020;4,4
4e kwartaal 2020;4,9
1e kwartaal 2021;4,8
2e kwartaal 2021;4,7
3e kwartaal 2021;4,6
4e kwartaal 2021;5,4
1e kwartaal 2022;6,3
2e kwartaal 2022;5,4
3e kwartaal 2022;5,0
4e kwartaal 2022;5,6
1e kwartaal 2023;5,7
2e kwartaal 2023;5,0
3e kwartaal 2023;4,8
4e kwartaal 2023;5,5
1e kwartaal 2024;5,5
2e kwartaal 2024;5,1
3e kwartaal 2024;4,9
4e kwartaal 2024;5,4
1e kwartaal 2025;5,8
2e kwartaal 2025;5,2
"""

# Charger les données comme CSV
df = pd.read_csv(StringIO(raw), sep=";")


# %%
# Nettoyage éventuel des nombres (remplacer virgules -> points, supprimer texte)
def clean_num(x):
    if pd.isna(x):
        return None
    x = str(x)
    x = x.replace(",", ".")
    x = re.sub(r"[^0-9\.]+", "", x)
    return float(x) if x != "" else None


for col in df.columns[1:]:
    df[col] = df[col].apply(clean_num)

# Créer un index temporel
quarters = []
for label in df.iloc[:, 0]:
    match = re.search(r"(\d{4})", label)
    year = int(match.group(1)) if match else None
    if "1e" in label:
        q = "Q1"
    elif "2e" in label:
        q = "Q2"
    elif "3e" in label:
        q = "Q3"
    else:
        q = "Q4"
    quarters.append(f"{year}{q}")

df.index = pd.PeriodIndex(quarters, freq="Q")

# Calcul YoY growth
for col in df.columns[1:]:
    df[f"{col}_YoY"] = df[col].pct_change(4) * 100
    # Calcul taux de croissance trimestriel (QoQ)
    df[f"{col}_QoQ"] = df[col].pct_change(1) * 100

print(df.tail(10))
# %%
# retain only Q1
df_q1 = df[df.index.quarter == 4]
print(df_q1)
