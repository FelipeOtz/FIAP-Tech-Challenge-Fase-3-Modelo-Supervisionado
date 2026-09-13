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

O detalhamento das colunas, com origem e percentual de valores ausentes, está em [`reports/dicionario_de_dados.md`](reports/dicionario_de_dados.md).

### Universo de modelagem

A base preserva todos os registros de origem. O universo efetivamente modelado é definido dentro do pipeline: alunos presentes que preencheram a prova (`presenca = 1` e `preenchimento_caderno = 1`), totalizando 3.354.661 registros.

Alunos ausentes recebem `alfabetizado = 0` por convenção administrativa, já que não fizeram a prova. Mantê-los no universo faria o modelo aprender em parte a prever quem falta à avaliação, um fenômeno com causas próprias.

---

## Achados da Exploração de Dados (EDA)

A exploração precedeu e orientou as decisões de modelagem. Os achados abaixo foram validados contra o dado real.

| #   | Achado | Implicação para a Modelagem |
| --- | --- | --- |
| 1   | `alfabetizado` é função determinística de `proficiencia`: máximo de 742,999819 entre não alfabetizados, mínimo de 743,00 entre alfabetizados, sem sobreposição | `proficiencia` descartada das features, por ser vazamento perfeito |
| 2   | Todos os 512.153 alunos ausentes recebem rótulo 0, sem exceção | `presenca` define o universo e não entra como feature |
| 3   | Os 1.185 alunos presentes sem nota são exatamente os `preenchimento_caderno = 0` | Filtro do universo expresso como regra de negócio, não como ausência de nulo |
| 4   | `serie` é constante em toda a base (2º ano do EF) | Removida por variância zero |
| 5   | `caderno` tem 21 versões em distribuição quase uniforme, resultado da atribuição aleatória do desenho amostral, mais um código residual com 18 registros | Removida das features e usada como controle negativo na interpretabilidade |
| 6   | `rede` é praticamente binária: Municipal 88,7%, Estadual 11,3%, Privada 25 registros, Federal ausente | Privada tratada como resíduo e limitação de cobertura documentada |
| 7   | A base cobre dois anos (2023 e 2024), com cerca de 99% dos municípios de 2023 reaparecendo em 2024 | Viabiliza features defasadas e validação temporal |
| 8   | A taxa de alfabetização por escola em 2023 varia de 0% a 100%, com mediana de 58,8% e quartis em 42,3% e 74,2% | Hipótese a testar: o histórico da escola concentra boa parte do sinal disponível |
| 9   | Balanceamento do alvo no universo modelado: 59,2% alfabetizados, 40,8% não | Dispensa técnicas de reamostragem |
| 10  | Agregados municipais do ano corrente incluem o próprio aluno no cálculo | Só entram agregados do ano anterior, calculados sobre coorte distinta |
| 11  | A ausência dos 18 indicadores do Atlas ocorre em bloco, nos mesmos registros (0,04% da base) | Uma estratégia de imputação resolve o conjunto |
| 12  | Metas municipais cobrem apenas a rede Municipal, e metas estaduais cobrem a rede Pública | A meta estadual preenche a lacuna dos alunos da rede Estadual |
| 13  | `meta_alfabetizacao_brasil` é constante dentro de cada ano | Mantida na base por completude, sem poder discriminante |
| 14  | A base não traz nenhum atributo individual da criança além da rede de ensino | Define a natureza territorial do modelo e sua principal limitação |

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
│   │   ├── universo.py                   Definição do universo de modelagem
│   │   └── pipeline.py                   ColumnTransformer: imputação e encoding
│   ├── modeling
│   │   └── treino.py                     Split por município, treino e validação cruzada
│   ├── evaluation
│   │   └── metricas.py                   ROC-AUC, F1, matriz de confusão
│   └── visualization
│       └── graficos.py                   Gráficos reaproveitados entre notebooks
│
├── 📁 reports
│   └── dicionario_de_dados.md            Descrição das 45 colunas e origem de cada fonte
│
├── 📁 images                             Gráficos exportados
│
├── requirements.txt
├── README.md
└── .gitignore
```

---

## Etapas de Modelagem

_Em desenvolvimento._

---

## Escolha do Algoritmo

_Em desenvolvimento._

---

## Métricas de Avaliação

_Em desenvolvimento._

---

## Interpretação dos Resultados

_Em desenvolvimento._

---

## Insights Encontrados

_Em desenvolvimento._

---

## Limitações do Projeto

A base não traz nenhuma característica da criança além da rede de ensino. Não há sexo, idade, condição socioeconômica familiar nem trajetória escolar. Todo o poder preditivo vem do contexto escolar, municipal e territorial. Duas crianças na mesma sala recebem a mesma predição, porque o modelo não dispõe de nada que as diferencie. O que ele produz é um score de risco territorial.

Os indicadores socioeconômicos do Atlas vêm do Censo Demográfico de 2010, e o desfecho é de 2024. São catorze anos de distância. Medem condições estruturais, que se alteram devagar, mas a defasagem pesa na leitura.

A avaliação abrange essencialmente as redes Municipal (88,7%) e Estadual (11,3%). A rede Privada aparece em 25 registros e a Federal não aparece, então nada do que o modelo aprende se aplica à rede privada.

Toda a base é do 2º ano do Ensino Fundamental.

Com dois anos de dados, as features defasadas dependem de um único ano-base, e municípios ou escolas que não aparecem em 2023 ficam sem histórico.

---

## Aplicação Prática para Políticas Públicas

_Em desenvolvimento._

---

## Possíveis Evoluções Futuras

_Em desenvolvimento._

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
