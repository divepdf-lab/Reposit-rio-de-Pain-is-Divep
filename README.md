# Repositório de Painéis da DIVEP

Catálogo dos painéis de monitoramento da Diretoria de Vigilância Epidemiológica (DIVEP/SES-DF),
atualizado automaticamente a partir da aba **Levantamento** da planilha “Painéis das Gerências – levantamento DIVEP”.

## Como funciona
1. A planilha do Google está publicada na web (somente leitura) em formato CSV.
2. O workflow `.github/workflows/sync.yml` roda **de hora em hora** (UTC) e também manualmente (Actions → Run workflow).
3. `scripts/sync_sheet.py` baixa o CSV e gera `data/paineis.json`. Só há commit quando o conteúdo muda.
4. `index.html` (GitHub Pages) lê `data/paineis.json` e mostra os cards, filtros e indicadores.

Não há chaves nem tokens. O endereço do CSV pode ser trocado criando a variável `SHEET_CSV_URL`
em Settings → Secrets and variables → Actions → Variables; sem ela, vale o endereço padrão do workflow.

## Configuração (uma vez)
- Settings → Actions → General → Workflow permissions → **Read and write permissions**.
- Settings → Pages → Deploy from a branch → `main` → `/ (root)`.

## Manutenção
- As colunas são lidas por posição (A a J) em `COLS`, no topo de `scripts/sync_sheet.py`. Se inserir ou apagar uma coluna na planilha, ajuste ali.
- Se o download falhar ou vier vazio, o script aborta sem sobrescrever o JSON.
- Teste local: `SHEET_CSV_URL="<endereço>" python scripts/sync_sheet.py`
- Agendamentos podem ser desativados pelo GitHub após cerca de 60 dias sem atividade; reative na aba Actions.

## Limites conhecidos
Área temática, periodicidade e data de atualização de cada painel não existem na planilha. Os painéis abrem nas plataformas originais e podem exigir permissão de acesso.
