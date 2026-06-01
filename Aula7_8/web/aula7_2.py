from flask import Flask, render_template, request
import json
app = Flask(__name__)

f_db = open("../../Aula3/dicionario_medico.json")
db = json.load(f_db)

@app.get("/")
def home_page():
    return render_template("home.html")

@app.get("/conceitos")
def listar_conceitos():
    return render_template("conceitos.html", conceitos = db.keys())

@app.get("/tabela")
def tabela():
    return render_template("tabela.html", conceitos = db)


@app.get("/conceitos/<designacao>")
def conceito(designacao):
    if designacao in db:
        descricao = db[designacao]
        return render_template("conceito.html", designacao= designacao, descricao= descricao)
    else:
        return render_template("erro.html", erro = "O conceito introduzido não existe")



@app.post("/conceitos")
def adicionar_conceito():
    designacao = request.form["designacao"] #request.args
    descricao = request.form["descricao"]
    db[designacao] = descricao
    f_out = open("bd.json","w")
    json.dump(db, f_out, indent=4, ensure_ascii=False)
    f_out.close()

    return render_template("conceitos.html", conceitos = db.keys())

@app.delete("/conceitos/<designacao>")
def apagar_conceito(designacao):
    del db[designacao]
    f_out = open("bd.json","w")
    json.dump(db, f_out, indent=4, ensure_ascii=False)
    f_out.close()
    return {"redirect_url": "/conceitos", "message": "Conceito apagado com sucesso!"}





@app.get("/api/conceitos")
def conceitos_api():

    return db


app.run(host="localhost", port=4003, debug=True)