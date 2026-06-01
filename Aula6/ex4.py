import spacy

nlp = spacy.load("pt_core_news_sm")
f = open("../../Dados/Harry Potter e A Pedra Filosofal.txt")
texto = f.read()
doc = nlp(texto)

for entity in doc.ents:
    if entity.label_ == "PER":
        print(entity, entity.label_)