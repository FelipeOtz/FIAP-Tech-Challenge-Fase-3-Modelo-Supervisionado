"""
Definição do universo de modelagem e das features.

Centraliza as decisões tomadas na análise exploratória para que os notebooks de
modelagem e de interpretabilidade partam exatamente da mesma base.
"""

import pandas as pd

ANO_MODELAGEM = 2024
ALVO = "alfabetizado"
AGRUPADOR = "id_municipio"

FEATURES_NUMERICAS = [
    "taxa_alfabetizacao_escola_historica",
    "alunos_avaliados_escola_historica",
    "taxa_alfabetizacao_municipio_historica",
    "idhm",
    "indice_gini",
    "taxa_criancas_dom_sem_fund",
    "taxa_atraso_0_fundamental",
    "diferenca_escola_municipio",
]
FEATURES_CATEGORICAS = ["sigla_uf", "rede_nome"]


def carregar_universo(caminho: str) -> pd.DataFrame:
    """
    Alunos efetivamente avaliados no ano de modelagem, com o atributo derivado.

    O recorte temporal é obrigatório: as taxas históricas foram calculadas sobre 2023,
    e aplicá-las a alunos de 2023 descreveria o aluno por um agregado que o contém.
    """
    base = pd.read_parquet(caminho)

    universo = base[
        (base["presenca"] == 1)
        & (base["preenchimento_caderno"] == 1)
        & (base["ano"] == ANO_MODELAGEM)
    ].copy()

    universo["diferenca_escola_municipio"] = (
        universo["taxa_alfabetizacao_escola_historica"]
        - universo["taxa_alfabetizacao_municipio_historica"]
    )

    return universo


def separar_features(universo: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    """Devolve features, alvo e a coluna de agrupamento usada na divisão."""
    return (
        universo[FEATURES_NUMERICAS + FEATURES_CATEGORICAS],
        universo[ALVO],
        universo[AGRUPADOR],
    )
