import spacy

nlp = spacy.load("pt_core_news_sm")

texto = "O gato comeu a sardinha. A sardinha do Sr. João estava boa."

doc = nlp(texto)

for token in doc:
    print(token.text, token.lemma_, token.pos_, token.ent_type_, token.head.text, token.dep_, token.morph, sep ="|")

print("="*20, "Sentences", "="*20)

for sent in doc.sents:
    print(sent)

print("="*20, "Entities", "="*20)

for entity in doc.ents:
    print(entity, entity.label_)





