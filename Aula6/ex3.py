import spacy
from spacy.matcher import Matcher

nlp = spacy.load("pt_core_news_sm")
f = open("../../Dados/Harry Potter e A Pedra Filosofal.txt")
texto = f.read()
doc = nlp(texto)

matcher = Matcher(nlp.vocab)

pattern = [
  {"ENT_TYPE": "PER", "OP":"+" },
  {"POS": {"IN": ["AUX", "VERB"]}, "OP": "+"},
  {"POS": "DET", "OP": "?"},
  {"POS": "NOUN"}
]
matcher.add("match_id", [pattern])

matches = matcher(doc)

for id, start, end in matches:
    print(doc[start:end])
print(len(matches))
