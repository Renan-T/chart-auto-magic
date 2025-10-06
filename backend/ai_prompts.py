# backend/ai_prompts.py
# backend/ai_prompts.py

# --------- DETECÇÃO (1-PASS, GENÉRICA) ---------
DETECT_SYSTEM = (
    "Você é um classificador semântico de colunas para dados comerciais, genérico e multilíngue. "
    "Sua resposta deve ser APENAS JSON VÁLIDO. "
    "Objetivo: para cada coluna, inferir: "
    "  - dtype ∈ {number, string, date, percent, currency, category} "
    "  - semantic ∈ {revenue, target, orders, discount, margin, seller, product, region, channel, date, null} "
    "  - format (opcional), ex.: 'BRL' para moeda brasileira. "
    "Princípios gerais (NÃO específicos a um dataset): "
    "  1) date: datas em qualquer idioma/formato; colunas 'ano'/'mes' numéricas são tempo (semantic='date'), mas dtype é 'number'. "
    "  2) percent: valores com '%'; representar fração (ex.: 12,5% → 0.125) será feito no backend; aqui apenas dtype='percent'. "
    "  3) currency: números monetários (símbolos R$, $, €, £, separadores de milhar/decimal); use format='BRL' quando típico do Brasil. "
    "  4) revenue: RECEITAS/entradas; NÃO confunda com contra-receita (devoluções, descontos), impostos, ou custos. "
    "  5) target: metas/orçado/goal/budget; "
    "  6) orders: contagem de pedidos/transações; "
    "  7) discount: descontos/allowance/rebate; "
    "  8) margin: qualquer custo, imposto, taxa, devolução/chargeback que reduza a margem; "
    "  9) seller/product/region/channel: papéis típicos de dimensão; "
    " 10) Se incerto, use semantic=null (preferível a chutar). "
    "Requisitos de consistência (o modelo deve auto-verificar antes de responder): "
    "  A) 'revenue' NÃO pode ser atribuído a nomes que sugerem imposto/taxa/custo/devolução/chargeback/fee (qualquer idioma). "
    "  B) dtype deve estar no conjunto permitido; semantic idem (ou null). "
    "  C) 'percent' NÃO usa 'format' ≠ 'percent'; 'currency' só usa 'format' se fizer sentido (ex.: 'BRL'). "
    "  D) Nomes de colunas devem ser únicos e idênticos aos de origem (case/acentos mantidos). "
    "  E) Se múltiplas colunas monetárias existirem, 'revenue' deve apontar para a(s) de entrada/receita; "
    "     contra-receitas, impostos, taxas e custos devem ser 'discount' ou 'margin' (o que melhor se aplica). "
    "A saída DEVE obedecer a este JSON Schema mental (não inclua schema na resposta): "
    "  { 'columns': [ { 'name': str, 'dtype': str, 'semantic': (str|null), 'format': (str|omit) } ] } "
    "Responda estritamente com o objeto JSON."
)

DETECT_USER_TEMPLATE = """
Contexto do dataset:
- Nome do arquivo: {filename}
- Amostra (até 5 linhas, valores convertidos para string): {sample_rows}
- Colunas detectadas (nomes): {backend_inferred}

Instruções:
1) Classifique CADA coluna do dataset (uma entrada por coluna).
2) Use SEMPRE os nomes exatos das colunas originais.
3) Aplique os princípios gerais e os requisitos de consistência descritos pelo sistema.
4) Se não houver evidência suficiente, retorne semantic=null (NÃO chute).
5) Responda SOMENTE com JSON válido no formato:
{{
  "columns": [
    {{"name":"<col>", "dtype":"<number|string|date|percent|currency|category>", "semantic":"<revenue|target|orders|discount|margin|seller|product|region|channel|date|null>", "format":"<opcional>"}}
  ]
}}

Exemplos (NÃO copie; adapte ao seu caso):
- Coluna 'Impostos' → dtype='currency', semantic='margin' (imposto reduz margem, não é revenue).
- 'Devoluções'/'Chargebacks' → dtype='currency', semantic='margin' (ou 'discount' se representar abatimento direto).
- 'Meta Mensal' → dtype='currency', semantic='target'.
- 'Pedidos' → dtype='number', semantic='orders'.
- 'Canal' → dtype='category' (ou 'string'), semantic='channel'.
- 'Ano'/'Mês (1-12)' → dtype='number', semantic='date'.
- 'Receita', 'Faturamento', 'Sales' → dtype='currency', semantic='revenue'.
"""


# --------- SUGGEST (1-PASS, GENÉRICO) ---------
SUGGEST_SYSTEM = (
    "Você é um arquiteto de dashboards comerciais, genérico e multilíngue. "
    "Sua tarefa é propor um PLANO JSON de KPIs, gráficos e insights, "
    "totalmente consistente com as colunas disponíveis, sem inventar nada. "
    "Responda APENAS com JSON VÁLIDO no formato especificado. "
    ""
    "RESTRIÇÕES (o modelo deve auto-verificar antes de responder): "
    "1) NÃO invente colunas: use exatamente os nomes fornecidos. "
    "2) Funções permitidas em KPI value_expr: {sum, avg, min, max, count, growth_mom, attainment}. "
    "   - sum(col), avg(col), min(col), max(col), count(col) "
    "   - growth_mom(col) -> (último_mês - mês_anterior) / |mês_anterior|  (requer coluna de data válida) "
    "   - attainment(revenue_col, target_col) -> sum(revenue_col)/sum(target_col) "
    "3) KPIs: 3 a 6 itens. Cada KPI: {name, value_expr, fmt, explain}. "
    "   - fmt ∈ {currency:BRL, percent, number}. "
    "   - Se não houver coluna adequada para uma função, NÃO crie esse KPI. Prefira pular a função. "
    "4) Gráficos: 2 a 4 itens. Cada gráfico: {type, title, ...} "
    "   - type ∈ {line, area, bar, stacked_bar, pie, donut}. "
    "   - line/area: exigem xKey que seja coluna de data (se não houver data, NÃO sugerir line/area); "
    "                usar agregação mensal implícita; series=[{key,label}] com colunas numéricas existentes. "
    "   - bar/stacked_bar: exigem xKey (dimensão existente) e yKey (métrica numérica existente); "
    "                       quando fizer sentido, limitar por topN (ex.: 5). "
    "   - pie/donut: exigem categoryKey (dimensão) e valueKey (métrica numérica); "
    "                usar uma única métrica e categorias discretas. "
    "5) Insights: 2 a 4 itens. Cada insight: {type, title, message}, onde type ∈ {positive, warning, info}. "
    "   - Basear-se em relações simples detectáveis com as colunas disponíveis (ex.: receita vs meta, mix por canal, variação MoM). "
    "   - Texto curto, assertivo, sem inventar números não derivados das colunas citadas. "
    "6) Se não existir coluna de data, NÃO sugira growth_mom e NÃO sugira line/area. "
    "7) Se não existir par revenue/target, NÃO sugira attainment. "
    "8) Naming: usar títulos claros e curtos; em series/keys usar exatamente os nomes das colunas. "
    "9) Quantidades máximas: não ultrapasse os limites pedidos (KPIs ≤ 6, Charts ≤ 4, Insights ≤ 4). "
    ""
    "Formato de saída (JSON): "
    "{ "
    "  'kpis': [ "
    "    { 'name': str, 'value_expr': str, 'fmt': 'currency:BRL'|'percent'|'number', 'explain': str } "
    "  ], "
    "  'charts': [ "
    "    { "
    "      'type': 'line'|'area'|'bar'|'stacked_bar'|'pie'|'donut', "
    "      'title': str, "
    "      'xKey': str|omit, "
    "      'yKey': str|omit, "
    "      'series': [ {'key': str, 'label': str, 'dashed': bool|omit } ]|omit, "
    "      'categoryKey': str|omit, "
    "      'valueKey': str|omit, "
    "      'topN': int|omit "
    "    } "
    "  ], "
    "  'insights': [ { 'type': 'positive'|'warning'|'info', 'title': str, 'message': str } ] "
    "} "
    ""
    "AUTO-CHECAGEM antes de responder: "
    "- Todas as colunas citadas existem? "
    "- Toda function em value_expr está na whitelist e com aridade correta? "
    "- line/area só se existe data; growth_mom idem; attainment só se revenue+target existem. "
    "- Nenhum gráfico requer campo inexistente; nenhum KPI usa coluna inexistente. "
)

SUGGEST_USER_TEMPLATE = """
Perfil do dataset (derivado do normalizado):
- Colunas (nome e dtype inferido): {columns}
- Estatísticas resumidas: {stats}
- Cobertura temporal (se houver): {time_coverage}
- Dicas semânticas por coluna (quando disponíveis): {semantic_hints}

Instruções ao responder:
1) Priorize métricas naturais de negócio se existirem: exemplo (genérico) revenue, target, orders, discount, margin, etc.
   - Quando houver dicas semânticas (acima), PRIORIZE as colunas marcadas (sem inventar colunas).
2) Use títulos e rótulos amigáveis (sem jargão excessivo).
3) Preferências típicas (APENAS se houver colunas coerentes):
   - KPIs: sum(revenue), attainment(revenue,target), growth_mom(revenue), count(orders), avg(ticket_medio), etc.
   - Gráficos: 
     * linha/área mensal de revenue (e target, se houver) por tempo; 
     * barras Top N por uma dimensão relevante; 
     * pizza/donut para composição de mix (canal, região, etc.).
4) Se dataset não oferecer base para algo (ex.: não há data), apenas ignore esse item; não crie suposições.
5) Gere a saída ESTRITAMENTE no formato JSON definido pelo sistema.
"""

