#!/usr/bin/env python3
"""Sincroniza a aba "Levantamento" (Google Sheets publicada como CSV) com data/paineis.json.

- Não usa chaves nem tokens: a planilha é pública (somente leitura).
- Só reescreve o arquivo quando o conteúdo dos painéis muda (evita commits vazios).
- Aborta sem sobrescrever nada se o download falhar, vier vazio ou vier uma página de login/HTML.

Variáveis de ambiente:
  SHEET_CSV_URL  (obrigatória) URL do CSV publicado
  OUTPUT_PATH    (opcional)    padrão: data/paineis.json
"""
import csv, io, json, os, re, sys, urllib.request
from datetime import datetime, timezone

URL = os.environ.get("SHEET_CSV_URL", "").strip()
OUT = os.environ.get("OUTPUT_PATH", "data/paineis.json")

# Posição de cada coluna na aba Levantamento (A=0, B=1, ...). Ajuste aqui se a planilha mudar.
COLS = {"gerencia": 0, "nome": 1, "descricao": 2, "fontes": 3, "onde": 4,
        "link": 5, "solicitada": 6, "sei": 7, "atendida": 8, "obs": 9}
URL_RE = re.compile(r"https?://[^\s,;]+")


def clean(v):
    """Remove espaços repetidos e vazios; devolve None se não houver texto."""
    t = re.sub(r"[ \t]+", " ", (v or "")).strip()
    return t or None


def cell(row, name):
    i = COLS[name]
    return clean(row[i]) if i < len(row) else None


def tool_of(url):
    if "powerbi.com" in url: return "Power BI"
    if "info.saude.df.gov.br" in url: return "InfoSaúde"
    return "Outro"


def fetch():
    if not URL:
        sys.exit("ERRO: defina SHEET_CSV_URL (Settings > Secrets and variables > Actions > Variables).")
    req = urllib.request.Request(URL, headers={"User-Agent": "divep-sync/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        text = r.read().decode("utf-8-sig")
    if text.lstrip().lower().startswith(("<!doctype", "<html")):
        sys.exit("ERRO: recebi HTML em vez de CSV. Confirme que a aba está publicada na web como CSV.")
    return text


def parse(text):
    rows = list(csv.reader(io.StringIO(text)))[1:]  # ignora o cabeçalho
    por_nome = {}
    for row in rows:
        nome = cell(row, "nome")
        if not nome:
            continue
        nome = re.sub(r"\s*\n\s*", " ", nome)
        links = URL_RE.findall(row[COLS["link"]] if COLS["link"] < len(row) else "")
        interno = "interno" in (cell(row, "onde") or "").lower()
        chave = nome.casefold()
        if chave in por_nome:                      # evita duplicidade: une os links
            for u in links:
                if u not in por_nome[chave]["links"]:
                    por_nome[chave]["links"].append(u)
            por_nome[chave]["pendencias"].append("Nome repetido na planilha (linhas unidas)")
            continue
        obs = cell(row, "obs")
        if interno:
            ferramenta, status = "Uso interno (não publicado)", "Uso interno"
        else:
            ferramenta = cell(row, "onde") or (tool_of(links[0]) if links else "Não informada")
            status = ("Retirado para adequação" if obs and "retirada" in obs.lower()
                      else "Disponível" if links else "Sem link")
        flags = []
        if not cell(row, "gerencia"): flags.append("Gerência não informada")
        if not links and not interno: flags.append("Sem link de acesso")
        por_nome[chave] = {
            "nome": nome, "gerencia": cell(row, "gerencia"), "descricao": cell(row, "descricao"),
            "fontes": cell(row, "fontes"), "ferramenta": ferramenta, "status": status,
            "links": links, "observacao": obs, "pendencias": flags,
            "solicitada": cell(row, "solicitada"), "processo_sei": cell(row, "sei"),
            "atendida": cell(row, "atendida"),
        }
    return list(por_nome.values())


def main():
    paineis = parse(fetch())
    if not paineis:
        sys.exit("ERRO: nenhum painel encontrado. Não sobrescrevi o arquivo existente.")
    if os.path.exists(OUT):
        try:
            antigo = json.load(open(OUT, encoding="utf-8")).get("paineis")
            if antigo == paineis:
                print(f"Sem mudanças ({len(paineis)} painéis). Arquivo mantido.")
                return
        except (ValueError, OSError):
            pass
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    saida = {"atualizado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
             "total": len(paineis), "paineis": paineis}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, indent=2)
    print(f"Atualizado: {len(paineis)} painéis gravados em {OUT}.")


if __name__ == "__main__":
    main()
