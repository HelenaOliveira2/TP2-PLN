import spacy

nlp = spacy.load("pt_core_news_sm")

texto = """José Luís Carneiro confirmou à Sic Notícias que teve uma conversa com Luís Montenegro, mas sem acordo: "Tivemos uma reunião leal e muito prática sobre o que está em causa e os princípios que estão em causa e agora é tempo de refletir e de reflexão". O secretário-geral quis "manter as reservas" e não divulgou o que se falou na conversa, mas revelou que "não foi conclusiva", ou seja, ainda não há acordo. "Para a generalidade das representações externas já há acordo, só não há acordo para o Tribunal Constitucional", revelou ainda.

Para José Luís Carneiro, aceitar a substituição de um juiz nomeado pelo PS por outro escolhido pelo Chega: "Seria violar um princípio com 44 anos e há princípios que nós juramos defender quando assumimos responsabilidades políticas"."""

doc = nlp(texto)

for ent in doc.ents:
    if ent.label_ in ["ORG", "PER"]:
        print(ent, ent.label_)