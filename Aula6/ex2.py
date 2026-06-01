import spacy
nlp = spacy.load("pt_core_news_sm")

f = open("../../Dados/Harry Potter e A Pedra Filosofal.txt")
texto = f.read()

doc = nlp(texto)

res = {}

for token in doc:
    if token.pos_ in ["VERB", "AUX"]:
        if token.lemma_ in res:
            res[token.lemma_] += 1
        else:
            res[token.lemma_] = 1

def ordena(elem):
    return elem[1]

sorted_dict = sorted(res.items(), key=lambda x: x[1])

print(sorted_dict)


