# Documentação Técnica

Referência técnica do projeto: esquema da base analítica, regras de modelagem e procedimento de reprodução. O contexto do problema, as decisões analíticas e a interpretação dos resultados estão no [README](../README.md).

---

# Dicionário de Dados

Base analítica no grão aluno, construída a partir da camada Gold do Tech Challenge Fase 2,
enriquecida com o Atlas do Desenvolvimento Humano (IDHM) e a Divisão Territorial Brasileira (IBGE).

**Dimensões:** 3.867.999 linhas × 45 colunas
**Cobertura:** 2023 e 2024, alunos do 2º ano do Ensino Fundamental
**Formato:** Parquet (gzip), 28,9 MB

---

## Identificadores

| Coluna | Tipo | Origem | Descrição |
| --- | --- | --- | --- |
| `ano` | int16 | `alunos` | Ano da avaliação (2023 ou 2024) |
| `id_municipio` | int32 | `alunos` | Código IBGE do município, 7 dígitos |
| `id_escola` | int32 | `alunos` | Código da escola |
| `id_aluno` | int32 | `alunos` | Identificador do aluno |

## Atributos da avaliação

| Coluna | Tipo | Origem | Descrição |
| --- | --- | --- | --- |
| `caderno` | int8 | `alunos` | Versão do caderno de prova (1 a 21). Atribuição por desenho amostral |
| `serie` | int8 | `alunos` | Série avaliada. Constante: 2 (2º ano do EF) |
| `rede` | int8 | `alunos` | Rede de ensino codificada: 1 Federal, 2 Estadual, 3 Municipal, 4 Privada |
| `rede_nome` | str | derivada | Rede decodificada via `dicionario.csv` |
| `presenca` | int8 | `alunos` | 0 Ausente, 1 Presente |
| `preenchimento_caderno` | int8 | `alunos` | 0 Prova não preenchida, 1 Prova preenchida |
| `peso_aluno` | float32 | `alunos` | Peso amostral do desenho de avaliação |

## Variável alvo e derivadas

| Coluna | Tipo | Origem | Descrição |
| --- | --- | --- | --- |
| `alfabetizado` | int8 | `alunos` | **Variável alvo.** 0 Não, 1 Sim |
| `proficiencia` | float32 | `alunos` | Nota de proficiência em leitura. Determina `alfabetizado` pelo corte de 743 pontos |

## Contexto histórico (ano-base 2023)

| Coluna | Tipo | Origem | Descrição |
| --- | --- | --- | --- |
| `taxa_alfabetizacao_escola_historica` | float32 | calculada | Percentual de alunos alfabetizados na escola em 2023, sobre os efetivamente avaliados |
| `alunos_avaliados_escola_historica` | float32 | calculada | Número de alunos avaliados na escola em 2023 |
| `taxa_alfabetizacao_municipio_historica` | float32 | Gold `municipio` | Taxa de alfabetização do município e rede em 2023 |
| `media_portugues_municipio_historica` | float32 | Gold `municipio` | Média de proficiência em português do município e rede em 2023 |

## Metas pactuadas

| Coluna | Tipo | Origem | Descrição |
| --- | --- | --- | --- |
| `meta_alfabetizacao_municipio` | float32 | Gold `meta_alfabetizacao_municipio` | Meta pactuada do município para o ano da linha. Cobre apenas a rede Municipal |
| `percentual_participacao_municipio` | float32 | Gold `meta_alfabetizacao_municipio` | Percentual de participação municipal na avaliação |
| `meta_alfabetizacao_uf` | float32 | Gold `meta_alfabetizacao_uf` | Meta pactuada estadual, referente à rede Pública (Municipal e Estadual) |
| `percentual_participacao_uf` | float32 | Gold `meta_alfabetizacao_uf` | Percentual de participação estadual na avaliação |
| `meta_alfabetizacao_brasil` | float32 | Gold `meta_alfabetizacao_brasil` | Meta pactuada nacional. Constante dentro de cada ano |

## Território

| Coluna | Tipo | Origem | Descrição |
| --- | --- | --- | --- |
| `nome_municipio` | str | DTB/IBGE | Nome do município |
| `codigo_uf` | int8 | DTB/IBGE | Código IBGE da unidade federativa |
| `sigla_uf` | str | derivada | Sigla da unidade federativa |
| `nome_uf` | str | DTB/IBGE | Nome da unidade federativa |
| `regiao` | str | derivada | Macrorregião, derivada do código da UF |

## Socioeconômico — Atlas do Desenvolvimento Humano (Censo 2010)

| Coluna | Tipo | Origem | Descrição |
| --- | --- | --- | --- |
| `idhm` | float32 | Atlas/ADH | Índice de Desenvolvimento Humano Municipal |
| `idhm_e` | float32 | Atlas/ADH | IDHM — dimensão Educação |
| `idhm_r` | float32 | Atlas/ADH | IDHM — dimensão Renda |
| `renda_pc` | float32 | Atlas/ADH | Renda per capita média |
| `indice_gini` | float32 | Atlas/ADH | Índice de Gini (desigualdade de renda) |
| `prop_pobreza_criancas` | float32 | Atlas/ADH | Proporção de crianças pobres |
| `taxa_criancas_dom_sem_fund` | float32 | Atlas/ADH | Percentual de crianças em domicílios onde nenhum morador tem fundamental completo |
| `taxa_analfabetismo_18_mais` | float32 | Atlas/ADH | Taxa de analfabetismo da população de 18 anos ou mais |
| `taxa_agua_esgoto_inadequados` | float32 | Atlas/ADH | Percentual de pessoas em domicílios com água e esgoto inadequados |
| `taxa_mulheres_chefe_filho_15m` | float32 | Atlas/ADH | Percentual de mães chefes de família sem fundamental completo com filho menor de 15 anos |
| `razao_dependencia` | float32 | Atlas/ADH | Razão entre população dependente e população em idade ativa |

## Educacional complementar — Atlas do Desenvolvimento Humano (Censo 2010)

| Coluna | Tipo | Origem | Descrição |
| --- | --- | --- | --- |
| `taxa_criancas_fora_escola_6_14` | float32 | Atlas/ADH | Percentual de crianças de 6 a 14 anos fora da escola |
| `expectativa_anos_estudo` | float32 | Atlas/ADH | Expectativa de anos de estudo aos 18 anos de idade |
| `taxa_freq_liquida_fundamental` | float32 | Atlas/ADH | Taxa de frequência líquida ao ensino fundamental |
| `taxa_atraso_0_fundamental` | float32 | Atlas/ADH | Percentual de crianças de 6 a 14 anos no fundamental sem atraso idade-série |

## Populacional — Atlas do Desenvolvimento Humano (Censo 2010)

| Coluna | Tipo | Origem | Descrição |
| --- | --- | --- | --- |
| `populacao` | float32 | Atlas/ADH | População residente total do município |
| `populacao_urbana` | float32 | Atlas/ADH | População residente urbana |
| `populacao_rural` | float32 | Atlas/ADH | População residente rural |

---

## Valores ausentes

| Coluna | % nulo | Causa |
| --- | --- | --- |
| Indicadores do Atlas (18 colunas) | 0,04% | Municípios criados após o Censo 2010. Ausência em bloco: mesmo conjunto de registros em todas as colunas |
| `taxa_alfabetizacao_municipio_historica`, `media_portugues_municipio_historica` | 1,17% | Município sem registro no indicador de 2023 |
| `taxa_alfabetizacao_escola_historica`, `alunos_avaliados_escola_historica` | 11,50% | Escolas que não participaram da avaliação de 2023 |
| `proficiencia`, `peso_aluno` | 13,27% | Alunos ausentes ou que não preencheram a prova |
| `percentual_participacao_municipio` | 13,82% | Ausente na fonte para parte dos municípios |
| `meta_alfabetizacao_brasil` | 45,18% | Metas começam em 2024: todas as linhas de 2023 ficam sem meta |
| `meta_alfabetizacao_uf` | 46,22% | Mesma causa acima, mais estados sem meta pactuada na fonte |
| `meta_alfabetizacao_municipio` | 54,07% | Mesma causa acima, mais a cobertura restrita à rede Municipal |

## Observações

- A base preserva todas as linhas e colunas de origem. O filtro do universo de modelagem e o
  descarte de variáveis com vazamento são decisões de modelagem, aplicadas no pipeline do projeto.
- Os indicadores do Atlas referem-se ao Censo Demográfico de 2010, enquanto o desfecho é de
  2023/2024. A defasagem é assumida como limitação: medem condições estruturais que se alteram
  lentamente.
- As taxas de alfabetização do próprio ano, presentes nas fontes de meta, foram deliberadamente
  omitidas: por serem agregados que incluem o próprio aluno, constituiriam vazamento.
- A avaliação cobre essencialmente as redes Municipal (88,7%) e Estadual (11,3%). A rede Privada
  aparece em 25 registros e a Federal não aparece.

---

# Regras de Modelagem

Restrições que definem o comportamento da pipeline. Alterá-las invalida os resultados publicados.

## Universo

O universo modelado é definido dentro da pipeline, não na base:

```python
universo = base[
    (base["presenca"] == 1)
    & (base["preenchimento_caderno"] == 1)
    & (base["ano"] == 2024)
]
```

Resulta em 1.851.852 registros de 5.517 municípios.

## Variáveis excluídas

| Variável | Motivo |
| --- | --- |
| `proficiencia` | Determina o alvo pelo corte de 743 pontos. Um classificador que aplica apenas o limiar atinge acurácia 1,000000 |
| `presenca`, `preenchimento_caderno` | Definem o universo; constantes após o filtro |
| `serie` | Constante em toda a base (2º ano do Ensino Fundamental) |
| `caderno` | Versão do caderno de prova, atribuída aleatoriamente por desenho amostral |
| `peso_aluno` | Peso amostral do desenho de avaliação, não atributo explicativo |
| `id_aluno`, `id_escola`, `nome_municipio` | Identificadores |
| `id_municipio` | Identificador. Usado como agrupador na divisão e na validação, nunca como feature |
| `media_portugues_municipio_historica` | Correlação de 0,94 com `taxa_alfabetizacao_municipio_historica` |
| `idhm_e`, `idhm_r`, `renda_pc` | Correlação de 0,95 a 0,97 com `idhm` |
| `prop_pobreza_criancas`, `taxa_analfabetismo_18_mais` | Correlação de 0,84 a 0,91 com `taxa_criancas_dom_sem_fund` |
| `meta_alfabetizacao_municipio` | Correlação de 0,98 com `taxa_alfabetizacao_municipio_historica` |
| `regiao` | Determinada por `sigla_uf` |
| `populacao`, `populacao_urbana`, `populacao_rural` | Correlação nula com o alvo |

## Variáveis utilizadas

Numéricas: `taxa_alfabetizacao_escola_historica`, `alunos_avaliados_escola_historica`, `taxa_alfabetizacao_municipio_historica`, `idhm`, `indice_gini`, `taxa_criancas_dom_sem_fund`, `taxa_atraso_0_fundamental`, `diferenca_escola_municipio`.

Categóricas: `sigla_uf`, `rede_nome`.

`diferenca_escola_municipio` é derivada dentro da pipeline, linha a linha:

```python
universo["diferenca_escola_municipio"] = (
    universo["taxa_alfabetizacao_escola_historica"]
    - universo["taxa_alfabetizacao_municipio_historica"]
)
```

## Vazamento temporal

Todo agregado histórico refere-se a 2023. A correlação da taxa histórica da escola com o alvo é 0,4321 nas linhas de 2023 e 0,1003 nas de 2024: a diferença mede o viés de incluir o próprio aluno no agregado que o descreve.

Nenhum agregado do ano corrente entra como feature.

## Divisão e validação

`GroupShuffleSplit` agrupado por `id_municipio` separa 20% para teste. A validação cruzada usa `GroupKFold` com três dobras dentro do treino.

O agrupamento é obrigatório: alunos do mesmo município compartilham todas as features contextuais, e uma divisão aleatória colocaria registros idênticos nos dois lados.

## Pré-processamento

Integrado ao estimador via `Pipeline` e `ColumnTransformer`:

- Numéricas: `SimpleImputer(strategy="median")` seguido de `StandardScaler`
- Categóricas: `OneHotEncoder(handle_unknown="ignore", sparse_output=False, dtype=np.float32)`

O `float32` no encoder reduz pela metade a memória da matriz codificada. Com `float64` e `n_jobs=-1`, a busca de hiperparâmetros esgota a memória disponível.

## Modelo e limiar

`HistGradientBoostingClassifier` com `max_depth=4`, `learning_rate=0.05`, `max_iter=200`, `min_samples_leaf=50`.

O limiar de decisão é 0,60, e não o padrão de 0,50. É o máximo empírico da acurácia balanceada e reflete a assimetria de custo entre os dois erros.

## Replicabilidade

`random_state=42` em `GroupShuffleSplit`, no estimador e em `RandomizedSearchCV`.

---

# Reprodução

## Ambiente

```bash
python -m venv .venv
source .venv/Scripts/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Ordem de execução

| Notebook | Produz | Depende de |
| --- | --- | --- |
| `01_eda.ipynb` | Gráficos em `images/` | `data/base_gold_alunos.parquet` |
| `02_modelagem.ipynb` | `models/pipeline_alfabetizacao.joblib` | a base |
| `03_interpretabilidade.ipynb` | Gráficos de SHAP e permutação | a pipeline serializada |

O notebook de interpretabilidade reconstrói a divisão treino e teste com a mesma semente, o que reproduz exatamente a partição usada na modelagem.

## Custo de execução

A busca de hiperparâmetros treina 24 modelos sobre uma amostra de 40% dos municípios de treino. A importância por permutação faz cinco repetições sobre 100 mil registros, e o cálculo de SHAP roda sobre 20 mil.

## Origem da base

`data/base_gold_alunos.parquet` é produzido fora deste repositório, a partir da camada Gold do Tech Challenge Fase 2, do Atlas do Desenvolvimento Humano e da Divisão Territorial Brasileira. A Fase 3 parte do arquivo consolidado.
