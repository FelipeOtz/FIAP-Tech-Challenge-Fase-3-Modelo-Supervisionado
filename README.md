# Tech Challenge Fase 3

## Predição e Inteligência Analítica para Alfabetização no Brasil

Projeto integrador da Fase 3 da pós-graduação. Constrói um modelo supervisionado de Machine Learning para prever se um aluno do 2º ano do Ensino Fundamental será considerado alfabetizado, a partir de variáveis educacionais, territoriais e socioeconômicas.

---

## Sumário

- [Contexto do Problema](#contexto-do-problema)
- [Objetivo Analítico](#objetivo-analítico)
- [Fontes de Dados](#fontes-de-dados)
- [Base Analítica](#base-analítica)
- [Achados da Exploração de Dados (EDA)](#achados-da-exploração-de-dados-eda)
- [Decisões Analíticas e Trade-offs](#decisões-analíticas-e-trade-offs)
- [Tratamento de Data Leakage](#tratamento-de-data-leakage)
- [Estrutura do Repositório](#estrutura-do-repositório)
- [Etapas de Modelagem](#etapas-de-modelagem)
- [Escolha do Algoritmo](#escolha-do-algoritmo)
- [Métricas de Avaliação](#métricas-de-avaliação)
- [Interpretação dos Resultados](#interpretação-dos-resultados)
- [Insights Encontrados](#insights-encontrados)
- [Limitações do Projeto](#limitações-do-projeto)
- [Aplicação Prática para Políticas Públicas](#aplicação-prática-para-políticas-públicas)
- [Possíveis Evoluções Futuras](#possíveis-evoluções-futuras)
- [Como Executar](#como-executar)
- [Replicabilidade](#replicabilidade)

---

## Contexto do Problema

O Compromisso Nacional Criança Alfabetizada mobiliza União, estados, Distrito Federal e municípios para que as crianças estejam alfabetizadas até o final do 2º ano do ensino fundamental. Cada município e cada estado tem metas pactuadas ano a ano, de 2024 a 2030.

O indicador informa o que já aconteceu. Para agir antes, gestores públicos precisam de estimativas de risco, de saber onde a vulnerabilidade se concentra e de entender quais fatores mais pesam sobre o resultado.

Na Fase 2, este projeto construiu o pipeline de engenharia de dados que integrou as fontes do Indicador Criança Alfabetizada em uma arquitetura Medalhão na AWS. Esta fase parte da camada Gold resultante e a usa para treinar modelos preditivos.

---

## Objetivo Analítico

Prever, para um aluno do 2º ano, se ele atingirá o nível de alfabetização medido pela Avaliação Criança Alfabetizada, usando o contexto da escola, do município, da rede de ensino e as condições socioeconômicas do território.

A variável alvo é `alfabetizado` (0/1), definida pelo corte de 743 pontos na escala de proficiência do Saeb, parâmetro estabelecido pela Pesquisa Alfabetiza Brasil do INEP. Trata-se de atingimento de nível em avaliação padronizada. Aprovação escolar é outra coisa, medida por outros critérios.

A base não contém atributos individuais da criança. O resultado se lê, portanto, como um score de risco territorial aplicado a cada aluno: alunos da mesma escola e rede recebem predição idêntica. A seção [Limitações](#limitações-do-projeto) trata dessa característica, e [Aplicação Prática](#aplicação-prática-para-políticas-públicas) propõe como usá-la.

---

## Fontes de Dados

A base analítica deriva da camada Gold construída na Fase 2, com acréscimo de fontes externas de domínio público.

| Fonte | Grão | Contribuição |
| --- | --- | --- |
| Avaliação Criança Alfabetizada (INEP, via Base dos Dados) | Aluno | Variável alvo, proficiência, rede de ensino, presença |
| Indicador municipal (Gold Fase 2) | Município × ano × rede | Taxa de alfabetização e média de português do ano-base |
| Metas municipais, estaduais e nacional (Gold Fase 2) | Município / UF / Brasil | Metas pactuadas 2024–2030 e percentual de participação |
| Atlas do Desenvolvimento Humano (PNUD/Ipea/FJP) | Município | IDHM e dimensões, renda, desigualdade, pobreza infantil, indicadores educacionais e populacionais |
| Divisão Territorial Brasileira (IBGE) | Município | Unidade federativa e macrorregião |

A construção da base ocorre em etapa anterior a este projeto, executada localmente sobre a camada Gold da Fase 2. A Fase 3 parte do arquivo já consolidado. Todas as decisões de modelagem são aplicadas aqui, não na preparação.

---

## Base Analítica

`data/base_gold_alunos.parquet` tem 3.867.999 registros e 45 colunas, cobrindo 2023 e 2024, alunos do 2º ano do Ensino Fundamental.

O detalhamento das colunas, com origem e percentual de valores ausentes, está em [`reports/documentacao_tecnica.md`](reports/documentacao_tecnica.md).

### Universo de modelagem

A base preserva todos os registros de origem. O universo efetivamente modelado é definido dentro do pipeline, por dois filtros com motivos distintos.

**Alunos efetivamente avaliados.** Ausentes e quem compareceu sem preencher o caderno recebem `alfabetizado = 0` por convenção administrativa, já que não fizeram a prova. Mantê-los faria o modelo aprender em parte a prever quem falta à avaliação, um fenômeno com causas próprias. Restam 3.354.661 registros.

**Apenas o ano de 2024.** As features de contexto histórico foram calculadas sobre 2023. Aplicá-las a alunos de 2023 significaria descrever o aluno com um agregado que o contém. Restam **1.851.852 registros**, 47,9% da base.

---

## Achados da Exploração de Dados (EDA)

A exploração precedeu e orientou as decisões de modelagem. Os achados abaixo foram validados contra o dado real.

| # | Achado | Implicação para a Modelagem |
|---|---|---|
| 1 | `alfabetizado` é função determinística de `proficiencia` no corte de 743 pontos: um classificador que aplica apenas o limiar atinge acurácia 1,000000 | Remover `proficiencia` das features |
| 2 | Todos os 512.153 alunos ausentes recebem rótulo 0, sem exceção. O rótulo mede ausência, não aprendizagem | `presenca` e `preenchimento_caderno` definem o universo, não entram como features |
| 3 | A taxa histórica da escola correlaciona 0,4321 com o alvo em 2023 e 0,1003 em 2024. A diferença é o vazamento de incluir o próprio aluno no agregado | Universo restrito a 2024, com 2023 como histórico. Redução de 3,35M para 1,85M registros |
| 4 | `serie` é constante e `caderno` é aleatório por desenho amostral | Ambas removidas. O controle negativo da interpretabilidade é feito com ruído sintético, e não com `caderno` |
| 5 | O contexto municipal correlaciona mais com o alvo (0,25) que o contexto escolar (0,10), apesar de ser o grão mais distante do aluno | A mediana de 35 alunos avaliados por escola torna a taxa escolar ruidosa. `alunos_avaliados_escola_historica` entra como indicador de confiabilidade |
| 6 | `taxa_alfabetizacao_municipio_historica` e `media_portugues_municipio_historica` correlacionam 0,94 entre si; as três dimensões do IDHM correlacionam entre 0,95 e 0,97 com o índice composto | Manter um representante por bloco, para que o SHAP não divida importância entre variáveis redundantes |
| 7 | O IDHM separa apenas o quintil inferior (56,8% contra 60% a 61% nos demais) | Relação em degrau, não linear. Modelos de árvore capturam o corte; modelos lineares perdem o efeito |
| 8 | A taxa da escola em 2023 tem 21,03% de ausência em 2024, contra 1,92% do contexto municipal | Imputação obrigatória. A ausência é estrutural: escolas sem participação no ano anterior |
| 9 | Balanceamento de 59,78% contra 40,22% | Dispensa reamostragem ou ponderação de classe |
| 10 | 45,6% dos municípios ficaram abaixo da meta pactuada para 2024 | Alvo alternativo viável no grão município, e recorte natural para a aplicação estratégica |
| 11 | O risco se concentra no Nordeste (28% dos municípios abaixo de 40% de alfabetização) e no Norte (22%), contra 1% no Sudeste | Região e UF entram como features categóricas |
| 12 | Municípios com perfil socioeconômico praticamente idêntico (IDHM 0,58 e 0,59, pobreza infantil 57% e 56%) apresentam 47% e 75% de alfabetização | As variáveis do Atlas não explicam a diferença. O fator determinante está fora do que a base mede |
| 13 | A maior correlação individual com o alvo é 0,25 | Expectativa de desempenho moderado. Modelos lineares e de árvore tendem a empatar |
| 14 | Nenhum atributo individual da criança existe na base além da rede de ensino | Alunos da mesma escola recebem predição idêntica. O resultado é score de risco territorial |


---

## Decisões Analíticas e Trade-offs

### Grão aluno em vez de grão município

O edital define o alvo no nível do aluno. A camada Gold da Fase 2 foi construída no grão município, UF e Brasil, e a tabela `alunos` permaneceu na Bronze por decisão de escopo daquela fase. A alternativa de reformular o problema para o nível município foi considerada e descartada: o grão aluno atende ao objetivo do desafio, e o enriquecimento contextual preserva a linhagem com a Gold.

### Construção da base fora do escopo do projeto

O edital determina que os dados venham da camada Gold da Fase 2, o que faz dela insumo deste projeto. A preparação da base ocorre em etapa anterior e local, e o repositório da Fase 3 parte do arquivo consolidado. Limpeza, decodificação e joins ficam na preparação. Filtro de universo, seleção de features e tudo que afeta o modelo fica aqui.

### Processamento local em vez de conexão à AWS

A camada Gold da Fase 2 foi construída em ambiente AWS Academy Learner Lab, de acesso temporário e com restrições de criação de perfis IAM. O consumo dos dados nesta fase ocorre a partir de arquivo local versionado, alternativa validada com a coordenação do curso.

### Features defasadas em vez de agregados contemporâneos

Indicadores de escola e município do próprio ano de referência contêm o resultado do aluno no cálculo. A solução adotada usa o ano anterior como histórico. Como toda a base é de 2º ano, alunos de 2023 e 2024 são coortes distintas, e a taxa histórica da escola foi medida sobre outras crianças.

### Seleção enxuta de indicadores socioeconômicos

O Atlas do Desenvolvimento Humano disponibiliza mais de 200 indicadores municipais, muitos deles fortemente correlacionados entre si. Só de renda são dezenas de variantes. Foram selecionados 18, escolhidos por cobrirem dimensões distintas. Incluir o conjunto completo não aumentaria o poder preditivo e comprometeria a interpretabilidade, porque os valores SHAP se dividiriam entre colunas que medem o mesmo fenômeno.

---

## Tratamento de Data Leakage

Foram identificadas e tratadas três fontes de vazamento.

`proficiencia` determina `alfabetizado` pelo corte de 743 pontos. Os valores observados não deixam margem: 742,999819 é o máximo entre os não alfabetizados e 743,00 o mínimo entre os alfabetizados. Um classificador que aplicasse só esse limiar reproduziria o rótulo inteiro. A variável foi descartada das features, e a análise exploratória documenta a relação.

Quanto à presença, todos os alunos ausentes recebem rótulo 0 por convenção administrativa. `presenca` e `preenchimento_caderno` servem para definir o universo de modelagem, e ficam constantes depois do filtro.

Os agregados contemporâneos formam o terceiro caso. Taxas de alfabetização do ano de referência incluem o próprio aluno no cálculo. Apenas agregados do ano anterior entram como features, calculados sobre coortes distintas.

O tratamento não se esgota na seleção de variáveis. A separação entre treino, validação e teste também considera o agrupamento territorial, para evitar que registros do mesmo município apareçam nos dois lados da divisão.

---

## Estrutura do Repositório

```
tech-challenge-fase3
│
├── 📁 data
│   └── base_gold_alunos.parquet          Base analítica no grão aluno (3,87M registros)
│
├── 📁 notebooks
│   ├── 01_eda.ipynb                      Análise exploratória e formulação de hipóteses
│   ├── 02_modelagem.ipynb                Pipeline de ML, treinamento e validação
│   └── 03_interpretabilidade.ipynb       Feature Importance e SHAP
│
├── 📁 src
│   ├── preprocessing
│   │   ├── universo.py                   Universo de modelagem, features e atributo derivado
│   │   └── pipeline.py                   ColumnTransformer: imputação e encoding
│   ├── modeling
│   │   └── treino.py                     Divisão agrupada e montagem do estimador
│   └── evaluation
│       └── metricas.py                   Métricas de avaliação e tabela comparativa
│
├── 📁 models
│   └── pipeline_alfabetizacao.joblib     Pipeline treinada, consumida pela interpretabilidade
│
├── 📁 reports
│   └── documentacao_tecnica.md           Dicionário de dados, regras de modelagem e reprodução
│
├── 📁 images                             Gráficos exportados
│
├── requirements.txt
├── README.md
└── .gitignore
```

Não há módulo de visualização: cada gráfico é gerado uma única vez no notebook que o contextualiza, e extrair função de uso único acrescentaria indireção sem reduzir duplicação.

---

## Etapas de Modelagem

### Seleção de variáveis

Das 45 colunas da base, nove são aproveitadas e uma é derivada, totalizando dez variáveis no modelo. Cada exclusão tem um motivo documentado.

| Critério | Variáveis excluídas |
| --- | --- |
| Vazamento direto | `proficiencia` |
| Definem o universo, constantes após o filtro | `presenca`, `preenchimento_caderno` |
| Variância zero | `serie` |
| Aleatória por desenho amostral | `caderno` |
| Peso amostral, não atributo explicativo | `peso_aluno` |
| Identificadores | `id_aluno`, `id_escola`, `id_municipio`, `nome_municipio` |
| Redundância com variável mantida | `media_portugues_municipio_historica` (0,94), dimensões e componentes do IDHM (0,95 a 0,97), `prop_pobreza_criancas` e `taxa_analfabetismo_18_mais` (0,84 a 0,91), `meta_alfabetizacao_municipio` (0,98), `regiao` (determinada por `sigla_uf`) |
| Correlação nula com o alvo | `populacao`, `populacao_urbana`, `populacao_rural`, demais indicadores do Atlas |

Variáveis mantidas:

- **Numéricas:** `taxa_alfabetizacao_escola_historica`, `alunos_avaliados_escola_historica`, `taxa_alfabetizacao_municipio_historica`, `idhm`, `indice_gini`, `taxa_criancas_dom_sem_fund`, `taxa_atraso_0_fundamental`
- **Categóricas:** `sigla_uf`, `rede_nome`
- **Derivada:** `diferenca_escola_municipio`

O critério de redundância é motivado pela interpretabilidade. Variáveis que medem o mesmo fenômeno dividem entre si a importância atribuída pelo SHAP, e nenhuma aparece como relevante no resultado final.

### Engenharia de atributos

A taxa da escola e a do município medem contextos aninhados, e nenhuma das duas informa a posição relativa entre eles. Uma escola com 45% de alfabetização em um município de 40% está acima do próprio contexto; a mesma taxa em um município de 70% está bem abaixo. `diferenca_escola_municipio` expressa essa posição.

A derivação é linha a linha, sem agregação, e portanto não introduz vazamento ao ser calculada antes da divisão entre treino e teste.

O efeito medido é marginal. O ROC-AUC no teste passou de 0,6548 para 0,6546, diferença menor que a variação entre dobras da validação cruzada. No limiar de operação houve ganho pequeno mas consistente: a revocação da classe em risco subiu de 0,6673 para 0,6749, o equivalente a 958 crianças a mais identificadas. O atributo foi mantido, e o resultado registrado como está: a posição relativa da escola acrescenta pouco além do que as duas taxas absolutas já carregam.

`rede_nome` é mantida apesar da diferença modesta entre redes (59% na Municipal contra 63% na Estadual): é a única característica do próprio aluno disponível na base, e sua ausência tornaria o modelo exclusivamente territorial.

### Pipeline de pré-processamento

Imputação pela mediana e padronização para as numéricas, codificação one-hot com `handle_unknown="ignore"` para as categóricas. Todas as etapas são componentes do estimador, não transformações aplicadas à base antes da divisão: a mediana e a média são calculadas apenas sobre a partição de treino de cada dobra.

### Divisão e validação

A divisão treino e teste é agrupada por município com `GroupShuffleSplit`, e a validação cruzada usa `GroupKFold` com três dobras. Alunos do mesmo município compartilham todas as features contextuais, de modo que uma divisão aleatória colocaria registros praticamente idênticos nos dois lados.

São três conjuntos distintos. O treino ajusta o modelo, as dobras do `GroupKFold` dentro dele funcionam como validação na seleção de hiperparâmetros, e o teste fica reservado até a avaliação final.

O conjunto de teste contém 330.836 alunos de 1.104 municípios, nenhum deles presente no treino. Essa é a condição real de uso: estimar risco onde ainda não há medição.

### Otimização de hiperparâmetros

`RandomizedSearchCV` com oito configurações sobre uma amostra de 40% dos municípios de treino, mantendo o agrupamento dentro da validação cruzada. O modelo final é treinado sobre todo o conjunto de treino com a configuração vencedora.

### Hipóteses analíticas

**H1 — O histórico educacional supera o contexto socioeconômico.** As variáveis de desempenho passado apresentam correlação uma ordem de grandeza acima das socioeconômicas do Atlas. Espera-se que o SHAP confirme essa hierarquia.

**H2 — A defasagem do Atlas limita seu poder preditivo.** As variáveis socioeconômicas são do Censo de 2010 e apresentam correlação próxima de zero com o desfecho de 2024. O teste indireto é a comparação com `taxa_atraso_0_fundamental`, também de 2010, que mantém correlação de 0,09.

**H3 — A confiabilidade da taxa escolar modera seu efeito.** A mediana de 35 alunos avaliados por escola torna a taxa escolar ruidosa. Espera-se maior peso de `taxa_alfabetizacao_escola_historica` quando `alunos_avaliados_escola_historica` é alto.

---

## Escolha do Algoritmo

Três candidatos foram comparados sobre o conjunto de teste. As métricas dependentes de limiar usam 0,60, o limiar de operação adotado.

| Modelo | ROC-AUC | Average precision | Acurácia balanceada | Revocação em risco |
| --- | --- | --- | --- | --- |
| Trivial (classe majoritária) | 0,5000 | 0,6188 | 0,5000 | 0,0000 |
| Regressão logística | 0,6523 | 0,7479 | 0,6044 | 0,6586 |
| Gradient boosting | 0,6545 | 0,7496 | 0,6043 | 0,6737 |

**Gradient boosting e regressão logística empataram.** A diferença de 0,0022 em ROC-AUC é menor que o desvio padrão observado entre dobras da validação cruzada. A relação entre contexto territorial e alfabetização é essencialmente aditiva: não há interações que justifiquem um modelo mais complexo.

A acurácia balanceada é praticamente idêntica (0,6043 contra 0,6044), e a única vantagem consistente do boosting está na revocação da classe em risco (0,6737 contra 0,6586). O gradient boosting foi adotado por essa diferença e por permitir o uso de `TreeExplainer` na etapa de interpretabilidade, não por desempenho global superior. A configuração vencedora da busca é a mais regularizada do espaço testado — `max_depth=4`, `learning_rate=0.05`, `max_iter=200`, `min_samples_leaf=50` — o que é coerente com um sinal fraco, em que capacidade adicional serviria apenas para memorizar ruído.

---

## Métricas de Avaliação

### Por que não usar acurácia nem F1 da classe positiva

Com 59,78% de uma classe, prever sempre "alfabetizado" produz F1 de 0,7645 na classe positiva, o maior valor entre todos os modelos testados. A métrica premia quem não discrimina nada. Por isso a avaliação usa ROC-AUC e average precision, que independem do limiar, além de F1 macro, acurácia balanceada e revocação da classe em risco, que dão peso igual às duas classes.

### Escolha do limiar de decisão

O limiar padrão de 0,50 pressupõe custos simétricos. Neste problema eles não são: sinalizar como em risco uma criança que seria alfabetizada custa uma parcela de atenção desperdiçada, enquanto deixar de sinalizar quem precisa custa a ausência de intervenção.

| Limiar | Acurácia balanceada | Revocação em risco |
| --- | --- | --- |
| 0,50 | 0,5782 | 0,2689 |
| 0,55 | 0,6006 | 0,4259 |
| **0,60** | **0,6051** | **0,6749** |
| 0,65 | 0,6032 | 0,7594 |
| 0,70 | 0,5868 | 0,8481 |

O limiar adotado é 0,60, máximo empírico da acurácia balanceada e portanto não arbitrário. Em relação ao padrão, a revocação da classe em risco passa de 27% para 67% sem perda de acurácia balanceada.

### Desempenho final

| Métrica | Valor |
| --- | --- |
| ROC-AUC (validação cruzada) | 0,6643 |
| ROC-AUC (teste) | 0,6546 |
| Average precision (teste) | 0,7494 |
| Acurácia balanceada (limiar 0,60) | 0,6051 |
| Revocação da classe em risco | 0,6749 |
| Precisão da classe em risco | 0,4722 |

A diferença de 0,0097 entre validação cruzada e teste indica ausência de sobreajuste relevante.

No conjunto de teste, o modelo identifica 85.121 das 126.128 crianças que não atingiram o nível de alfabetização.

**Sobre a magnitude do ganho.** Entre os alunos sinalizados como em risco, 47,2% de fato não se alfabetizaram, contra 38,1% que se obteria sinalizando ao acaso. É um ganho de 1,24 vez sobre o acaso: real, verificável e modesto. É o que os dados permitem sem nenhum atributo individual da criança, e o projeto prefere declarar esse número a apresentar apenas o ROC-AUC.

---

## Interpretação dos Resultados

A interpretabilidade combina duas medidas. A importância por permutação embaralha cada variável e mede a queda de ROC-AUC no conjunto de teste. Os valores SHAP atribuem a cada predição a contribuição de cada variável, revelando direção e intensidade do efeito.

### Controle negativo

Antes de ler o ranking, a leitura foi validada. Um modelo de controle foi treinado com os valores de `indice_gini` substituídos por ruído aleatório. O ruído ficou na sétima posição entre dez variáveis, com queda de -0,00000.

Isso estabelece a régua: qualquer variável com importância abaixo de aproximadamente 0,001 é estatisticamente indistinguível de aleatório.

### O modelo usa duas variáveis

| Variável | Queda de ROC-AUC |
| --- | --- |
| `taxa_alfabetizacao_municipio_historica` | 0,0995 |
| `sigla_uf` | 0,0437 |
| `indice_gini` | 0,0011 |
| `taxa_atraso_0_fundamental` | 0,0009 |
| `rede_nome` | 0,0003 |
| `taxa_criancas_dom_sem_fund` | 0,0002 |
| `taxa_alfabetizacao_escola_historica` | 0,00009 |
| `alunos_avaliados_escola_historica` | 0,00009 |
| `diferenca_escola_municipio` | 0,00003 |
| `idhm` | -0,0003 |

O histórico de alfabetização do município e a unidade federativa respondem por praticamente todo o desempenho. As outras oito variáveis estão no patamar do ruído, incluindo o IDHM, a taxa histórica da escola e o atributo derivado.

No SHAP a unidade federativa aparece fragmentada em 27 colunas codificadas. Somadas, alcançam cerca de 0,30, contra 0,35 do histórico municipal: as duas variáveis dominantes têm peso comparável.

### Por que SHAP e permutação discordam

As duas medidas divergem em `taxa_atraso_0_fundamental`: importância SHAP de 0,056 contra queda de 0,0009 na permutação. A divergência é esperada.

O SHAP mede quanto a variável desloca a saída do modelo; a permutação mede quanto o desempenho cai sem ela. Uma variável redundante desloca a saída, mas não faz falta quando removida, porque as correlacionadas compensam. `taxa_atraso_0_fundamental` correlaciona 0,70 com o IDHM e 0,32 com a taxa histórica municipal. O modelo usa a variável, mas não depende dela.

### Teste das hipóteses

**H1, confirmada.** Importância SHAP somada de 0,363 para as variáveis educacionais contra 0,052 para as socioeconômicas, razão de sete para um.

**H2, refutada.** O indicador educacional de 2010 (0,056) supera todas as socioeconômicas de 2010 somadas (0,052). Como compartilham a mesma vintage, a defasagem de catorze anos não é o fator limitante: a natureza da variável é. Indicadores educacionais predizem educação melhor que indicadores de renda, mesmo desatualizados.

**H3, refutada e na direção oposta.** O SHAP da taxa escolar é 0,0033 em escolas pequenas e 0,0026 nas grandes. Ambos irrelevantes, já que a taxa da escola não contribui para o modelo.

### Efeitos estaduais

Os valores SHAP mostram efeitos de unidade federativa que persistem depois de o modelo já considerar o histórico do município e os indicadores socioeconômicos.

Ceará e Minas Gerais empurram a predição para alfabetizado, com contribuições entre 0,3 e 0,8. O Rio Grande do Sul apresenta o efeito negativo mais forte do conjunto, próximo de -0,8, apesar de figurar entre as unidades federativas de maior IDHM.

O resultado do Rio Grande do Sul é registrado como achado a investigar, não como conclusão: pode refletir desempenho real na avaliação, diferenças de participação ou composição da amostra de municípios sorteados para o teste.

### Desempenho no grão que interessa à decisão

No grão aluno o ROC-AUC é 0,6546. Agregando as predições por município, a correlação entre taxa prevista e taxa observada é **0,8449**.

A diferença não é contradição. O ruído individual, que nenhuma variável contextual poderia explicar, se cancela na média. O município é a unidade em que a gestão pública decide, e é nela que o modelo é preciso.

---

## Insights Encontrados

### Vulnerabilidade socioeconômica não determina o resultado

O agrupamento de municípios por perfil produziu dois grupos com condições socioeconômicas praticamente idênticas e desempenho educacional oposto.

| | Grupo A | Grupo B |
| --- | --- | --- |
| IDHM | 0,58 | 0,59 |
| Renda per capita | R$ 270 | R$ 277 |
| Pobreza infantil | 57,5% | 56,1% |
| Crianças em domicílio sem fundamental completo | 51,3% | 49,1% |
| **Taxa de alfabetização em 2024** | **47%** | **75%** |
| Participação do Nordeste | 74,0% | 70,8% |

Vinte e oito pontos percentuais de diferença entre municípios com a mesma pobreza, a mesma renda e a mesma escolaridade familiar. As variáveis do Atlas não explicam a divergência: o fator determinante está fora do que a base socioeconômica mede, no campo da gestão educacional.

A leitura precisa de uma ressalva: o agrupamento inclui o histórico de alfabetização entre suas variáveis, de modo que parte da separação é esperada. O achado não é que existem dois grupos distintos, e sim que **as variáveis socioeconômicas isoladamente não os separam**.

### O risco é geograficamente concentrado

Entre os municípios com ao menos cem alunos avaliados, 28% dos nordestinos e 22% dos nortistas ficaram abaixo de 40% de alfabetização, contra 1% dos municípios do Sudeste. Os quinze piores resultados nacionais estão todos na Bahia, em Sergipe, no Amazonas e no Amapá.

### Quase metade dos municípios não alcançou a meta

Dos 5.232 municípios com meta pactuada disponível, 45,6% ficaram abaixo do valor acordado para 2024.

### A meta pactuada reproduz o desempenho passado

A meta municipal correlaciona 0,98 com a taxa de alfabetização do ano anterior. Municípios com histórico ruim recebem metas baixas e municípios com histórico bom recebem metas altas. Para o modelo isso é redundância; para a gestão pública, indica que as metas são calibradas pelo ponto de partida, não por ambição uniforme.

### O contexto municipal prediz melhor que o escolar

Contra a intuição, a taxa do município correlaciona mais com o resultado do aluno (0,25) do que a taxa da própria escola (0,10). A explicação está na escala: com mediana de 35 alunos avaliados por escola, a taxa escolar é dominada por ruído amostral, enquanto o agregado municipal mede o mesmo fenômeno com muito menos variância.

---

## Limitações do Projeto

A base não traz nenhuma característica da criança além da rede de ensino. Não há sexo, idade, condição socioeconômica familiar nem trajetória escolar. Todo o poder preditivo vem do contexto escolar, municipal e territorial. Duas crianças na mesma sala recebem a mesma predição, porque o modelo não dispõe de nada que as diferencie. O que ele produz é um score de risco territorial.

Os indicadores socioeconômicos do Atlas vêm do Censo Demográfico de 2010, e o desfecho é de 2024. São catorze anos de distância. Medem condições estruturais, que se alteram devagar, mas a defasagem pesa na leitura.

A avaliação abrange essencialmente as redes Municipal (88,7%) e Estadual (11,3%). A rede Privada aparece em 25 registros e a Federal não aparece, então nada do que o modelo aprende se aplica à rede privada.

Toda a base é do 2º ano do Ensino Fundamental.

Com dois anos de dados, as features defasadas dependem de um único ano-base, e municípios ou escolas que não aparecem em 2023 ficam sem histórico.

As probabilidades previstas são discretas, e não contínuas. Alunos da mesma escola e rede recebem scores idênticos, o que concentra cerca de 54 mil registros do conjunto de teste em torno de 0,55, imediatamente abaixo do limiar adotado. Entre 0,55 e 0,60 a revocação da classe em risco salta de 0,42 para 0,67: a escolha do limiar reclassifica dezenas de milhares de alunos de uma vez, o que exige cautela ao transportar o limiar para outro conjunto de dados.

---

## Aplicação Prática para Políticas Públicas

### O que o modelo entrega

Uma estimativa de risco por município, aplicável antes da avaliação do ano corrente. Com correlação de 0,8449 entre previsto e observado no grão municipal, o modelo permite ordenar territórios por risco e alocar recursos antes que o resultado se confirme.

No conjunto de teste, os quinze municípios de maior risco previsto estão todos na Bahia, com probabilidade média de alfabetização entre 28,5% e 31,0%.

### Três leituras acionáveis

**Vulnerabilidade socioeconômica não determina o resultado.** O IDHM é ruído dentro do modelo, e o agrupamento de municípios identificou dois grupos com renda, pobreza infantil e escolaridade familiar equivalentes e 28 pontos percentuais de diferença na alfabetização. Municípios pobres alcançam resultados muito distintos entre si, o que desloca o foco da política de compensação da pobreza para a atuação sobre a gestão educacional.

**O efeito estadual é comparável ao histórico do município.** Depois de considerar o desempenho passado e as condições socioeconômicas, permanece um efeito de unidade federativa de magnitude equivalente. Isso sugere que políticas de alfabetização em âmbito estadual produzem diferença mensurável, e indica onde procurar práticas que funcionaram.

**As metas pactuadas reproduzem o ponto de partida.** A meta municipal correlaciona 0,98 com a taxa do ano anterior, e 45,6% dos municípios ficaram abaixo dela em 2024. Metas calibradas pelo desempenho passado tendem a pedir menos esforço de quem já ia bem.

### Como usaria o resultado

O modelo serve à priorização, não ao diagnóstico individual. Alunos da mesma escola e rede recebem a mesma predição, de modo que o produto útil é uma lista ordenada de territórios, não de crianças.

O limiar de 0,60 foi escolhido por essa razão. Identifica 67% das crianças que não atingirão o nível de alfabetização, ao custo de sinalizar também parte das que atingiriam. Entre os sinalizados, 47,2% de fato não se alfabetizam, contra 38,1% de uma seleção aleatória.

### O que o modelo não resolve

O ganho sobre o acaso é de 1,24 vez. O modelo ordena territórios por risco com utilidade real, mas não substitui diagnóstico local nem identifica quais crianças precisam de apoio dentro de uma mesma escola. Para isso seriam necessários dados individuais que a base pública não contém.

---

## Possíveis Evoluções Futuras

**Dados individuais da criança.** A limitação central do projeto. Idade, trajetória escolar, frequência e condição socioeconômica familiar permitiriam distinguir crianças dentro de uma mesma escola, transformando o score territorial em risco individual.

**Censo Escolar.** A base traz `id_escola`, que permite juntar infraestrutura, formação docente, porte e jornada. É a fonte mais promissora entre as não utilizadas, e a que poderia explicar por que municípios socioeconomicamente idênticos divergem tanto.

**Indicadores socioeconômicos atualizados.** O Censo de 2022 substituiria a base de 2010 do Atlas. O teste da H2 sugere que o ganho seria limitado, mas a hipótese merece verificação direta.

**Série histórica mais longa.** Com apenas 2023 e 2024, as features defasadas dependem de um único ano-base. Ciclos adicionais permitiriam medir tendência, e não apenas nível.

**Investigação do efeito estadual.** O contraste entre Ceará e Rio Grande do Sul, persistente após controlar por histórico e condição socioeconômica, sugere que há informação sobre gestão educacional que a base não captura diretamente.

**Modelagem no grão município.** Dado que o desempenho útil aparece na agregação, um modelo treinado diretamente sobre municípios, com o alvo definido como atingir ou não a meta pactuada, pode ser mais adequado ao uso pretendido que a agregação de predições individuais.

---

## Como Executar

```bash
python -m venv .venv
source .venv/Scripts/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
jupyter notebook
```

Execute os notebooks na ordem numérica. A análise exploratória orienta as decisões implementadas na modelagem, e a interpretabilidade consome o modelo treinado na etapa anterior.

---

## Replicabilidade

Todos os processos com componente aleatório usam `random_state` fixo: divisão dos conjuntos, inicialização dos modelos e busca de hiperparâmetros. Executar os notebooks na mesma ordem, com as versões declaradas em `requirements.txt`, reproduz os resultados apresentados.
