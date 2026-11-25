"""Lê os acórdãos baixados, extrai texto e campos, e gera docs/dados.js para a página de busca.

Precisa de `pdftotext` (poppler) e `antiword` no PATH — ambos vêm com o Git for Windows (mingw64).
"""
import datetime, json, re, subprocess, zipfile
from pathlib import Path

RAIZ = Path(__file__).parent
PASTA = RAIZ / "acordaos"
SAIDA = RAIZ / "docs" / "dados.js"


def extrair_texto(arq: Path) -> str:
    cabeca = arq.read_bytes()[:8]
    try:
        if cabeca.startswith(b"%PDF"):
            cmd = ["pdftotext", "-enc", "UTF-8", str(arq), "-"]
        elif cabeca.startswith(b"\xd0\xcf\x11\xe0"):  # .doc antigo
            cmd = ["antiword", "-m", "UTF-8.txt", str(arq)]
        elif cabeca.startswith(b"PK"):  # .docx
            xml = zipfile.ZipFile(arq).read("word/document.xml").decode("utf-8")
            return re.sub(r"<[^>]+>", " ", xml.replace("</w:p>", "\n"))
        else:
            return ""
        return subprocess.run(cmd, capture_output=True, timeout=120).stdout.decode("utf-8", "replace")
    except Exception as e:
        print("  erro lendo", arq.name, e)
        return ""


def achar(padrao, texto):
    m = re.search(padrao, texto, re.I)
    return m.group(1).strip(" .,;:–-") if m else ""


FIM_NOME = r"(?=\s+(?:relator|revisor|advogad|procurador|auto\s+de|processo|interessad|recorrente|data\s+do|\d\s*ª|ac[oó]rd[aã]o)|$)"


MESES = {m: i for i, m in enumerate("janeiro fevereiro março abril maio junho julho agosto setembro outubro novembro dezembro".split(), 1)}
MESES["marco"] = 3
ANO_MAX = datetime.date.today().year + 1


def numero(m):
    """(número, ano) de um match, ou None se o ano não fizer sentido."""
    if not m:
        return None
    ano = int(m.group(2)) if len(m.group(2)) == 4 else 2000 + int(m.group(2))
    return (int(m.group(1)), str(ano)) if 2000 <= ano <= ANO_MAX else None


def data_julgamento(t):
    d = achar(r"data\s+do\s+julgamento\s*[:–-]?\s*(\d{1,2}/\d{1,2}/\d{4})", t)
    if d:
        return d
    # Acórdãos mais antigos: data por extenso no fecho ("Cuiabá, 26 de agosto de 2022"); usa a última.
    extenso = re.findall(r"(\d{1,2})º?\s+de\s+(" + "|".join(MESES) + r")\s+de\s+(\d{4})", t, re.I)
    if extenso:
        dia, mes, ano = extenso[-1]
        return f"{int(dia):02d}/{MESES[mes.lower()]:02d}/{ano}"
    return ""


def campos(texto, nome_arquivo, categoria):
    t = re.sub(r"\s+", " ", texto)
    cab = t[:1500]  # o cabeçalho fica no início
    n = numero(re.search(r"ac[oó]rd[aã]o\s*(?:n[º°o.]*)?\s*[–-]?\s*(\d+)\s*/\s*(\d{2,4})", cab, re.I)) \
        or numero(re.search(r"(\d+)\s*[-\s]\s*(\d{4}|\d{2}\b)", nome_arquivo))
    ano = n[1] if n else achar(r"(\d{4})", categoria)
    junta = achar(r"(\d)\s*ª\s*junta", cab)
    return {
        "n": f"{n[0]}/{ano}" if n else "",
        "ano": ano,
        "proc": achar(r"processo\s*n?[º°o.]*\s*:?\s*([\d.]+\s*/\s*\d{4})", cab).replace(" ", ""),
        "int": achar(r"(?:interessad[oa]s?|recorrentes?|autuad[oa])\s*[:–-]\s*(.{3,150}?)" + FIM_NOME, cab),
        "rel": achar(r"relator[a]?\s*[:–-]\s*(.{3,150}?)" + FIM_NOME, cab),
        "junta": f"{junta}ª Junta" if junta else "",
        "data": data_julgamento(t),
        "decisao": achar(r"((?:decidiram|acordam)\b.{0,400}?\.)(?:\s|$)", t),
        "txt": t.strip(),
    }


def ler_dados():
    if not SAIDA.exists():
        return []
    js = SAIDA.read_text("utf-8")
    return json.loads(js[js.index("window.DADOS=") + len("window.DADOS="):].rstrip().rstrip(";"))


def main():
    lista_path = PASTA / "lista.json"
    lista = json.loads(lista_path.read_text("utf-8")) if lista_path.exists() else {}
    # Mantém o que já estava indexado: na atualização automática (GitHub) só os novos são baixados.
    antigos = {d["url"]: d for d in ler_dados()}
    dados, sem_texto = [], []
    for url, info in lista.items():
        arq = PASTA / info["arquivo"]
        if not arq.exists():
            continue
        texto = extrair_texto(arq)
        if len(texto.strip()) < 200:
            sem_texto.append(info["arquivo"])
        d = campos(texto, arq.name, info["categoria"])
        d["url"] = url
        d["arq"] = arq.name
        dados.append(d)
    novos = {d["url"] for d in dados}
    dados += [d for u, d in antigos.items() if u not in novos]
    dados.sort(key=lambda d: (d["ano"], int(d["n"].split("/")[0]) if d["n"] else 0), reverse=True)
    if {d["url"]: d for d in dados} == antigos:
        print(f"nada mudou ({len(dados)} acórdãos)")
        return
    SAIDA.parent.mkdir(exist_ok=True)
    hoje = datetime.date.today().strftime("%d/%m/%Y")
    SAIDA.write_text(f'window.ATUALIZADO="{hoje}";window.DADOS='
                     + json.dumps(dados, ensure_ascii=False, separators=(",", ":")) + ";", "utf-8")
    print(f"{len(dados)} acórdãos indexados -> {SAIDA} ({SAIDA.stat().st_size / 1e6:.1f} MB)")
    for campo in ("n", "proc", "int", "rel", "junta", "data", "decisao"):
        print(f"  {campo}: {sum(1 for d in dados if d[campo])} preenchidos")
    if sem_texto:
        print(f"{len(sem_texto)} sem texto (provavelmente digitalizados, precisariam de OCR):")
        (RAIZ / "sem_texto.txt").write_text("\n".join(sem_texto), "utf-8")
        print("  lista em sem_texto.txt")


if __name__ == "__main__":
    main()
