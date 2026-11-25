# Busca de Acórdãos do CONSEMA-MT

Busca no texto integral dos acórdãos do Conselho Estadual do Meio Ambiente de Mato Grosso
([fonte: SEMA-MT](https://www.sema.mt.gov.br/site/index.php/decisao-colegiada/conselho-estadual-do-meio-ambiente/ac%C3%B3rd%C3%A3os)).

## Para usar

Abra `docs/index.html` no navegador (ou o endereço publicado). Não precisa instalar nada.

- Digite qualquer assunto: palavras separadas precisam aparecer todas.
- `"frase exata"`, `queimada OU incêndio`, `-palavra` para excluir.
- Acentos e maiúsculas são ignorados; `queima` também acha "queimada".
- Botões de tema (Desmatamento, Nascentes/APP, Queimadas…) filtram com um clique.
- Filtros por ano, junta e relator. O link da barra de endereço guarda a pesquisa — dá para mandar para alguém.

## Para atualizar (quem mantém)

Requer Python 3 e Git for Windows (traz `pdftotext` e `antiword`).

```
python baixar.py     # baixa só os acórdãos novos para ./acordaos
python indexar.py    # regenera docs/dados.js
```

Depois publique a pasta `docs/` (ou faça commit/push, se estiver no GitHub Pages).
Os temas ficam no topo do script em `docs/index.html` (constante `TEMAS`).
