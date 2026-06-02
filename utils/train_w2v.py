"""
MedLex Explorer — Script para treino do modelo Word2Vec local.
Utiliza o dicionário médico e os resumos de artigos para treinar embeddings semânticos.
"""

import json
import re
from pathlib import Path
from typing import List
from gensim.models import Word2Vec

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
DICT_PATH = _PROJECT_ROOT / "DICIONARIO_GIGANTE_FINAL.json"
ARTICLES_PATH = _PROJECT_ROOT / "data" / "artigos.json"
MODEL_PATH = _PROJECT_ROOT / "data" / "medlex_w2v.model"

def clean_and_tokenize(text: str) -> List[str]:
    """Limpa o texto e divide-o em tokens de palavras (minúsculas)."""
    if not text:
        return []
    # Remover tags markdown se existirem (ex: **IMPORTANCE**)
    text = re.sub(r'\*\*([^*]+)\*\*:', r'\1', text)
    # Dividir por caracteres não-alfanuméricos
    tokens = re.findall(r'\b\w+\b', text.lower())
    return tokens

def prepare_corpus() -> List[List[str]]:
    """Gera o corpus de treino juntando definições do dicionário e resumos de artigos."""
    sentences = []
    
    # 1. Carregar Dicionário Médico
    if DICT_PATH.exists():
        print(f"A ler dicionário médico de '{DICT_PATH.name}'...")
        try:
            with open(DICT_PATH, "r", encoding="utf-8") as f:
                dict_data = json.load(f)
                for entry in dict_data.values():
                    # Adicionar termo principal
                    term = entry.get("termo_principal", "")
                    if term:
                        sentences.append(clean_and_tokenize(term))
                        
                    # Adicionar sinónimos
                    for syn in entry.get("sinonimos", []):
                        sentences.append(clean_and_tokenize(syn))
                        
                    # Adicionar definições (frases completas - muito importante para contexto)
                    for def_text in entry.get("definicoes", []):
                        # Se a definição for grande, podemos dividi-la por frases (ponto final)
                        for sentence in def_text.split("."):
                            tokens = clean_and_tokenize(sentence)
                            if len(tokens) > 1:
                                sentences.append(tokens)
        except Exception as e:
            print(f"Erro ao ler dicionário para treino: {e}")
            
    # 2. Carregar Artigos do PubMed
    if ARTICLES_PATH.exists():
        print(f"A ler artigos do PubMed de '{ARTICLES_PATH.name}'...")
        try:
            with open(ARTICLES_PATH, "r", encoding="utf-8") as f:
                articles = json.load(f)
                for art in articles:
                    # Adicionar título
                    title = art.get("titulo", "")
                    if title:
                        sentences.append(clean_and_tokenize(title))
                    # Adicionar resumo dividido por frases
                    resumo = art.get("resumo", "")
                    if resumo:
                        for sentence in resumo.split("."):
                            tokens = clean_and_tokenize(sentence)
                            if len(tokens) > 1:
                                sentences.append(tokens)
        except Exception as e:
            print(f"Erro ao ler artigos para treino: {e}")
            
    print(f"Corpus preparado com {len(sentences)} frases/sentenças para treino.")
    return sentences

def train_w2v_model() -> bool:
    """Treina o modelo Word2Vec e guarda-o no disco."""
    sentences = prepare_corpus()
    if not sentences:
        print("Erro: Nenhum dado disponível para treino.")
        return False
        
    print("A treinar modelo Word2Vec (pode demorar alguns segundos)...")
    try:
        MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        # Treinar o modelo
        model = Word2Vec(
            sentences=sentences,
            vector_size=100,  # dimensão dos vetores
            window=5,         # janela de contexto
            min_count=1,      # considerar todas as palavras
            workers=4,        # threads de execução
            epochs=15         # número de iterações
        )
        model.save(str(MODEL_PATH))
        print(f"Modelo Word2Vec guardado com sucesso em '{MODEL_PATH.name}'!")
        return True
    except Exception as e:
        print(f"Erro ao treinar Word2Vec: {e}")
        return False

if __name__ == "__main__":
    train_w2v_model()
