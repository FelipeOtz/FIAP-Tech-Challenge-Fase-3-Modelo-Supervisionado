"""
Pré-processamento integrado ao estimador.

As transformações são componentes do modelo, não etapas anteriores: a mediana da
imputação e a média da padronização são calculadas apenas sobre a partição de treino
de cada dobra.
"""

import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .universo import FEATURES_CATEGORICAS, FEATURES_NUMERICAS


def criar_preprocessador() -> ColumnTransformer:
    """
    O `float32` no encoder reduz pela metade a memória da matriz codificada, que com
    1,8 milhão de registros inviabiliza a busca de hiperparâmetros em paralelo.
    """
    return ColumnTransformer(
        [
            (
                "numericas",
                Pipeline([
                    ("imputacao", SimpleImputer(strategy="median")),
                    ("escala", StandardScaler()),
                ]),
                FEATURES_NUMERICAS,
            ),
            (
                "categoricas",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False, dtype=np.float32),
                FEATURES_CATEGORICAS,
            ),
        ]
    )
