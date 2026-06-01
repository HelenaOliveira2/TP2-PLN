import re
import json
f = open("../../Dados/dicionario_medico.xml")

texto = f.read()

#limpeza
texto = re.sub(r"</?text.*?>", "", texto)
texto = re.sub(r"</?page.*?>", "", texto)

#extração
conceitos = re.findall(r"<b>(.*)</b>\n([^<]+)", texto)

res = {}
for termo, desc in conceitos:
    res[termo] = desc.strip()

#guardar conceitos em json
f_out = open("conceitos.json", "w")
json.dump(res,f_out, indent=4, ensure_ascii=False)
f_out.close()


