"""
Montagem do estimador e divisão dos conjuntos.

A divisão é agrupada por município: alunos do mesmo município compartilham todas as
features contextuais, e uma divisão aleatória colocaria registros praticamente
idênticos em treino e teste.
"""

import pandas as pd
from sklearn.base import BaseEstimator
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline

from preprocessing.pipeline import criar_preprocessador

SEMENTE = 42
PROPORCAO_TESTE = 0.2


def construir_pipeline(estimador: BaseEstimator) -> Pipeline:
    return Pipeline([("preprocessamento", criar_preprocessador()), ("modelo", estimador)])


def dividir_agrupado(X: pd.DataFrame, y: pd.Series, grupos: pd.Series):
    """Índices de treino e teste, sem nenhum município presente nos dois lados."""
    divisor = GroupShuffleSplit(n_splits=1, test_size=PROPORCAO_TESTE, random_state=SEMENTE)
    return next(divisor.split(X, y, groups=grupos))
