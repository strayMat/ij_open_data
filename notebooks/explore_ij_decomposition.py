# %%
"""
Understand decomposition of the participation of each factor to IJ spending described in https://drees.solidarites-sante.gouv.fr/sites/default/files/2024-12/ER1321_0.pdf , tableaux complémentaires J et K.

Je fais l'exercice de recalculer des taux de participation pour la croissance des montants IJ de 2010 à 2023.
"""
import pandas as pd
# %%
# Taux de croissance des montants IJ 
growth_ij = 28.9
print(f"Tx croissance IJ entre 2010 et 2019: {growth_ij}")
# %% 
# Effet 1: effectifs de la population salariée
pop_salariee_growth_rate = 100*((19540665 / 18212909) - 1)
print(f"Tx de croissance de la pop salariee entre 2010 et 2023 : {pop_salariee_growth_rate:.1f} %")
# Ils concluent que l'effet 1 des effectifs de la population salariée vaut +7.3 %
# NB: Quand on calcule le taux de croissance des salariés qui bénéfinet d'un IJ, on trouve +10.9 %. Cela signifie que les IJ sont pris par plus de monde qu'avant. 
# %% 
# Effet 2 : vieillissement ie. changement dans la structure des populations

#Montants moyens par individus
age_groups = [
    "0-19", "20-24", "25-29", "30-34", "35-39", "40-44", "45-49",
    "50-54", "55-59", "60-64", "65-69", "70+"
]

montants_moyen_par_individu = pd.DataFrame({
    "2010": [232, 600, 859, 1021, 1178, 1359, 1561, 1843, 2285, 2474, 2277, 2459],
    "2019": [285, 666, 999, 1230, 1429, 1617, 1786, 1969, 2281, 2490, 2301, 2057],
    "2023": [300, 713, 1160, 1408, 1575, 1768, 1978, 2215, 2535, 2770, 2260, 1109]
}, index=age_groups)
# Structure d’âge data as percentages (remove % and convert to float)
structure_df = pd.DataFrame({
    "2010": [2.4, 9.8, 13.0, 12.7, 13.5, 13.3, 12.8, 11.3, 8.3, 2.2, 0.4, 0.2],
    "2019": [2.8, 9.5, 11.9, 12.5, 12.5, 11.6, 12.5, 11.7, 10.1, 3.7, 0.8, 0.4],
    "2023": [3.3, 10.5, 11.7, 11.9, 12.0, 11.9, 11.0, 11.6, 10.3, 4.6, 0.9, 0.4]
}, index=age_groups)
# %% 
growth_vieillissement = 100 * (
    (montants_moyen_par_individu["2019"] * structure_df["2023"] / 100).sum() /
    (montants_moyen_par_individu["2019"] * structure_df["2019"] / 100).sum() - 1
)
print(f"Tx de croissance de l'effet vieillissement entre 2010 et 2019 : {growth_vieillissement:.1f} %")
# Ils concluent que l'effet 2 du vieillissement vaut +4.1 % alors que moi j'ai +3.6 %. Même ordre de grandeur mais pas exactement pareil donc je dois me planter quelque part. Mais je pense que j'ai tout de même compris le principe.