"""
Métricas de avaliação do classificador.

A acurácia e o F1 da classe positiva não são usados: com 59,78% de uma classe, prever
sempre a majoritária produz F1 de 0,7645, o maior valor entre todos os modelos.
"""

import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    f1_score,
    recall_score,
    roc_auc_score,
)

LIMIAR_PADRAO = 0.60


def avaliar(nome: str, y_real, probabilidades, limiar: float = LIMIAR_PADRAO) -> dict:
    """`recall_em_risco` é a revocação da classe 0, alvo prático da intervenção."""
    predicoes = (probabilidades >= limiar).astype(int)

    return {
        "modelo": nome,
        "roc_auc": roc_auc_score(y_real, probabilidades),
        "average_precision": average_precision_score(y_real, probabilidades),
        "f1_macro": f1_score(y_real, predicoes, average="macro"),
        "acuracia_balanceada": balanced_accuracy_score(y_real, predicoes),
        "recall_em_risco": recall_score(y_real, predicoes, pos_label=0),
    }


def comparar(resultados: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(resultados).set_index("modelo").round(4)
