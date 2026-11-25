"""Baixa todos os acórdãos do CONSEMA (SEMA-MT) para ./acordaos/<categoria>/.

Rodar de novo baixa só o que é novo. Gera ./acordaos/lista.json (url -> arquivo local).
"""
import json, re, time, html
from pathlib import Path
from urllib.parse import quote, unquote
from urllib.request import Request, urlopen

BASE = "https://www.sema.mt.gov.br"
INDICE = BASE + "/site/index.php/decisao-colegiada/conselho-estadual-do-meio-ambiente/ac%C3%B3rd%C3%A3os"
PASTA = Path(__file__).parent / "acordaos"
PAUSA = 0.3  # segundos entre requisições, para não sobrecarregar o site


def url_segura(caminho):
    caminho = html.unescape(caminho)
    return BASE + quote(unquote(caminho), safe="/?=&")


def get(url):
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 (busca-acordaos-consema)"})
    for tentativa in range(3):
        try:
            with urlopen(req, timeout=60) as r:
                return r.read()
        except Exception as e:
            if tentativa == 2:
                raise
            print("  erro, tentando de novo:", e)
            time.sleep(5)


def main():
    PASTA.mkdir(exist_ok=True)
    lista_path = PASTA / "lista.json"
    lista = json.loads(lista_path.read_text("utf-8")) if lista_path.exists() else {}
    # Já indexados (docs/dados.js) não são baixados de novo — é o que permite a atualização automática no GitHub.
    dados_js = PASTA.parent / "docs" / "dados.js"
    ja_indexados = set(re.findall(r'"url":"([^"]+)"', dados_js.read_text("utf-8"))) if dados_js.exists() else set()

    pagina = get(INDICE).decode("utf-8", "replace")
    categorias = sorted(set(re.findall(r'href="(/site/index.php/decisao-colegiada/conselho-estadual-do-meio-ambiente/[^"/]+/category/(\d+-[^"?]+))"', pagina)))
    for href, slug in categorias:
        nome_cat = unquote(slug).split("-", 1)[1]  # ex.: "acórdãos-2019"
        vistos, start = set(), 0
        while True:
            time.sleep(PAUSA)
            html_cat = get(url_segura(href) + f"?start={start}").decode("utf-8", "replace")
            arquivos = [a for a in re.findall(r'href="(/site/phocadownload/[^"]+)"', html_cat) if a not in vistos]
            if not arquivos:
                break
            for a in arquivos:
                vistos.add(a)
                url = url_segura(a)
                if url in ja_indexados or (url in lista and (PASTA / lista[url]["arquivo"]).exists()):
                    continue
                local = Path(nome_cat) / Path(unquote(html.unescape(a))).name
                destino = PASTA / local
                destino.parent.mkdir(parents=True, exist_ok=True)
                print("baixando", local)
                time.sleep(PAUSA)
                try:
                    destino.write_bytes(get(url))
                except Exception as e:
                    print("  FALHOU:", e)
                    continue
                lista[url] = {"arquivo": local.as_posix(), "categoria": nome_cat}
                lista_path.write_text(json.dumps(lista, ensure_ascii=False, indent=1), "utf-8")
            start += 20
        print(f"{nome_cat}: {len(vistos)} arquivos")
    print("total:", len(lista))


if __name__ == "__main__":
    main()
