import re
# ler ficheiro txt
f = open("../../Dados/dicionario_medico.txt", "r") #encoding="utf8"
texto = f.read()

# limpar texto

texto = re.sub(r"\f","", texto)

# marcar conceitos

texto = re.sub(r"\n\n", "\n\n@", texto)

# capturar conceitos
conceitos = re.split(r"@", texto)
#print(conceitos)


def limpa_descricao(descricao):
    descricao = re.sub(r"\n"," ", descricao)
    descricao = descricao.strip()
    return descricao

conceitos_dict = {}

for c in conceitos[1:]:
    elems = re.split(r"\n", c, maxsplit=1)
    if len(elems) > 1:
        designacao = elems[0]
        #print("designacao: ",designacao)
        descricao = elems[1]
        #print("descricao: ", descricao)
        #print("-"*20)
        conceitos_dict[designacao] = limpa_descricao(descricao)
    else: 
        #Fixe me
        continue

print(conceitos_dict)

import json
def gera_json(filename, conceitos_dict):
    f_out = open(filename, "w")
    json.dump(conceitos_dict, f_out, indent= 4, ensure_ascii=False)

#gera_json("dicionario_medico.json", conceitos_dict)

def gera_html(filename, conceitos_dict):
    html = """
<html>
    <head>
        <title> Dicionário Médico </title>
        <meta charset="UTF-8"/>
    </head>
    <body>"""

    for c in conceitos_dict:
        html = html + f"""
        <div>
            <p><b> {c} </b></p>
            <p> {conceitos_dict[c]} </p>
        </div>
        <hr>
        """

    html =  html +"""</body>
</html>"""

    f_out = open(filename, "w")
    f_out.write(html) 

gera_html("dicionario_medico.html", conceitos_dict)