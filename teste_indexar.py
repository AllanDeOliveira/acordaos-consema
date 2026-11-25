"""Checagem rápida da extração de campos: python teste_indexar.py"""
from indexar import campos

novo = campos("Processo nº 35304/2022 Interessada - Macife Agropecuária Relator – Edilberto Gonçalves de Souza - FETIEMT "
              "Revisora - Kélita 1ª Junta de Julgamento de Recursos Data do Julgamento – 25/08/2026 Acórdão nº 104/2026 "
              "Decidiram, por maioria, nos termos do Voto Revisor I.", "x.pdf", "acórdãos-2026")
assert novo["n"] == "104/2026" and novo["proc"] == "35304/2022", novo
assert novo["int"] == "Macife Agropecuária" and novo["junta"] == "1ª Junta" and novo["data"] == "25/08/2026", novo
assert novo["rel"].startswith("Edilberto") and novo["decisao"].startswith("Decidiram"), novo

antigo = campos("Processo n. 140745/2011 Interessado – Juraci Relator(a) – Cesar 2ª Junta Acórdão 271/2022 ... "
                "Cuiabá, 07/03/2012 ... Cuiabá, 26 de Agosto de 2022.", "y.pdf", "acórdãos-2022")
assert antigo["n"] == "271/2022" and antigo["data"] == "26/08/2022", antigo

assert campos("Acórdão 480/2033", "Acrdo - 480-2022.pdf", "acórdãos-2022")["n"] == "480/2022"  # ano absurdo -> nome do arquivo
assert campos("sem número", "Acordao 164 2022.pdf", "acórdãos-2022")["n"] == "164/2022"
assert campos("sem número", "Acordao  197-19.doc", "acórdãos-2019")["n"] == "197/2019"
print("ok")
