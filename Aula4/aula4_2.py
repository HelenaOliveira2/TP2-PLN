import re
import json
f = open("../../Dados/livrinho.txt")
texto = f.read()

f_conceitos = open("conceitos.json")
conceitos = json.load(f_conceitos)

black_list = ["de", "e", "os"]

def substituir_conceito(match):
    palavra = match[0]
    if palavra in conceitos and palavra not in black_list:
        return f"<a href='' title='{conceitos[palavra]}'>{palavra}</a>"
    else:
        return palavra 


#### encontrar /substituir conceitos
texto = re.sub(r"\w+",substituir_conceito,texto)
print(texto)

#### gerar html
texto = re.sub(r"\n", "<br>", texto)
texto = re.sub(r"\f", "<hr>", texto)
html_header="""
<html>
    <head>
        <title> Livro de doenças do aparelho digestivo </title>
        <meta charset="UTF-8">
    </head>
"""
html_body = f"<body> {texto} </body>"
html_footer = "</html>"

f_html = open("livro.html","w")
f_html.write(html_header + html_body + html_footer)




