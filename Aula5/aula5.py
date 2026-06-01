from bs4 import BeautifulSoup
import requests
import json
import string

url = "https://www.atlasdasaude.pt/doencasAaZ/"


def extrair_página(url):
    html = requests.get(url).text

    soup = BeautifulSoup(html, "html.parser")


    div_doencas = soup.find_all("div", class_= "views-row")

    res = {}
    for div in div_doencas:
        designacao = div.div.h3.a.text
        descricao = div.find("div", class_ ="views-field-body").div.text
        res[designacao] = descricao.strip()
    return res

res = {}
for letra in string.ascii_lowercase:
    res = res | extrair_página(url+letra)

f_out = open("doencas.json", "w")
json.dump(res,f_out, indent=4, ensure_ascii=False)
f_out.close()





# <div class="views-row views-row-29 views-row-odd">
#   <div class="views-field views-field-title"> 
#       <h3 class="field-content">
#           <a href="/content/ataque-epileptico">Ataque epiléptico</a>
#       </h3> 
#   </div>
#   <div class="views-field views-field-body"> 
#       <div class="field-content"> 
#           <p>Os sintomas da epilepsia, ou dito correctamente, de uma crise epiléptica, são definidos pelos doentes como singulares impressões sensoriais. Na prática o doente exibe sintomas convulsivos, contracções musculares involuntárias e desmaios.</p>
#       </div> 
#   </div> 
# </div>