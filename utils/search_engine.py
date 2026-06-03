"""
MedLex Explorer — Motores de Pesquisa Científica (IR).
Implementa pesquisa por TF-IDF (de raiz), Word2Vec e SBERT.
"""

import os
import json
import math
import pickle
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple
import numpy as np

# Caminhos de dados
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
ARTIGOS_PATH = _PROJECT_ROOT / "data" / "artigos.json"
W2V_MODEL_PATH = _PROJECT_ROOT / "data" / "medlex_w2v.model"
SBERT_CACHE_PATH = _PROJECT_ROOT / "data" / "artigos_embeddings_sbert.pkl"

# Lazy loader para SBERT (carrega apenas quando necessário)
_sbert_model = None

def get_sbert_model():
    global _sbert_model
    if _sbert_model is None:
        print("A carregar modelo SBERT (SentenceTransformer - MedLink Bi-Encoder)...")
        from sentence_transformers import SentenceTransformer
        # Modelo leve multilingue (cerca de 420MB)
        _sbert_model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    return _sbert_model

def clean_and_tokenize(text: str) -> List[str]:
    """Limpa o texto e divide-o em tokens de palavras (minúsculas)."""
    if not text:
        return []
    # Remover pontuação e converter para minúsculas
    text = text.lower()
    text = re.sub(r'\*\*([^*]+)\*\*:', r'\1', text) # remover markdown
    tokens = re.findall(r'\b\w+\b', text)
    return tokens

# ══════════════════════════════════════════════════════════════════════════════
# 1. OPÇÃO B: TF-IDF IMPLEMENTADO DE RAIZ
# ══════════════════════════════════════════════════════════════════════════════

class TFIDFSearch:
    def __init__(self, articles: List[Dict[str, Any]]):
        self.articles = articles
        self.N = len(articles)
        self.vocab = set()
        self.df = {}  # Document Frequency
        self.idf = {} # Inverse Document Frequency
        self.doc_vectors = [] # List of {word: tfidf_score} for each doc
        self._build_index()

    def _build_index(self):
        if self.N == 0:
            return
            
        # 1. Contar frequências de termos nos documentos e construir vocabulário
        doc_term_counts = []
        for art in self.articles:
            # Junta título e resumo para indexação
            text = f"{art.get('titulo', '')} {art.get('resumo', '')}"
            tokens = clean_and_tokenize(text)
            
            # Frequência de palavras no documento
            counts = {}
            for t in tokens:
                counts[t] = counts.get(t, 0) + 1
            doc_term_counts.append((counts, len(tokens)))
            
            # Adicionar ao Document Frequency (df)
            for t in set(tokens):
                self.df[t] = self.df.get(t, 0) + 1
                self.vocab.add(t)

        # 2. Calcular IDF para cada termo
        # idf(t) = log10(N / df(t))
        for t in self.vocab:
            self.idf[t] = math.log10(self.N / self.df[t])

        # 3. Construir vetores TF-IDF dos documentos
        # tf(t, d) = count(t, d) / total_words(d)
        for counts, total_words in doc_term_counts:
            vec = {}
            if total_words > 0:
                for t, count in counts.items():
                    tf = count / total_words
                    vec[t] = tf * self.idf[t]
            self.doc_vectors.append(vec)

    def search(self, query: str, top_n: int = 5) -> List[Tuple[Dict[str, Any], float]]:
        if self.N == 0:
            return []
            
        query_tokens = clean_and_tokenize(query)
        if not query_tokens:
            return []
            
        # 1. Construir vetor TF-IDF da query
        query_counts = {}
        for t in query_tokens:
            if t in self.vocab:
                query_counts[t] = query_counts.get(t, 0) + 1
                
        query_vec = {}
        total_q_words = len(query_tokens)
        for t, count in query_counts.items():
            tf = count / total_q_words
            query_vec[t] = tf * self.idf[t]

        # 2. Calcular similaridade de cosseno com cada documento
        results = []
        for i, doc_vec in enumerate(self.doc_vectors):
            score = self._cosine_similarity(query_vec, doc_vec)
            if score > 0.0:
                results.append((self.articles[i], score))
                
        # Ordenar por score descrescente
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_n]

    def _cosine_similarity(self, v1: Dict[str, float], v2: Dict[str, float]) -> float:
        # Produto escalar
        dot_product = sum(v1[w] * v2.get(w, 0.0) for w in v1)
        # Normas
        norm1 = math.sqrt(sum(x * x for x in v1.values()))
        norm2 = math.sqrt(sum(x * x for x in v2.values()))
        
        if norm1 == 0.0 or norm2 == 0.0:
            return 0.0
        return dot_product / (norm1 * norm2)


# ══════════════════════════════════════════════════════════════════════════════
# 2. OPÇÃO A: WORD2VEC TREINADO LOCALMENTE (MÉDIA DE VETORES)
# ══════════════════════════════════════════════════════════════════════════════

class Word2VecSearch:
    def __init__(self, articles: List[Dict[str, Any]]):
        self.articles = articles
        self.N = len(articles)
        self.model = None
        self.doc_vectors = []
        self._load_and_index()

    def _load_and_index(self):
        if not W2V_MODEL_PATH.exists():
            print("Aviso: Modelo Word2Vec local não encontrado. É necessário treinar primeiro.")
            return
            
        from gensim.models import Word2Vec
        self.model = Word2Vec.load(str(W2V_MODEL_PATH))
        self.vector_size = self.model.vector_size
        
        # Calcular vetor médio para cada artigo
        for art in self.articles:
            text = f"{art.get('titulo', '')} {art.get('resumo', '')}"
            tokens = clean_and_tokenize(text)
            
            # Média dos vetores das palavras do artigo que estão no vocabulário
            vecs = [self.model.wv[w] for w in tokens if w in self.model.wv]
            if vecs:
                mean_vec = np.mean(vecs, axis=0)
            else:
                mean_vec = np.zeros(self.vector_size)
            self.doc_vectors.append(mean_vec)

    def search(self, query: str, top_n: int = 5) -> List[Tuple[Dict[str, Any], float]]:
        if self.model is None or self.N == 0:
            return []
            
        query_tokens = clean_and_tokenize(query)
        if not query_tokens:
            return []
            
        # Calcular vetor médio da query
        query_vecs = [self.model.wv[w] for w in query_tokens if w in self.model.wv]
        if not query_vecs:
            return []
            
        query_vec = np.mean(query_vecs, axis=0)
        
        # Calcular similaridade de cosseno
        results = []
        for i, doc_vec in enumerate(self.doc_vectors):
            if np.all(doc_vec == 0.0) or np.all(query_vec == 0.0):
                score = 0.0
            else:
                score = self._cosine_similarity(query_vec, doc_vec)
                
            # Escalonamento discriminativo para médias de Word2Vec
            # Similaridades de cosseno cruas geralmente variam entre [0.70, 1.0] para correspondências úteis.
            # Mapeamos linearmente o intervalo [0.70, 1.0] para [0.0, 1.0]
            threshold = 0.70
            if score > threshold:
                score_scaled = float((score - threshold) / (1.0 - threshold))
            else:
                score_scaled = 0.0
                
            if score_scaled > 0.05: # filtro mínimo de relevância pós-escalonamento
                results.append((self.articles[i], score_scaled))
                
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_n]

    def _cosine_similarity(self, v1: np.ndarray, v2: np.ndarray) -> float:
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return np.dot(v1, v2) / (norm1 * norm2)


# ══════════════════════════════════════════════════════════════════════════════
# 3. OPÇÃO C: SBERT MULTILINGUE PRÉ-TREINADO (COM CACHE DE EMBEDDINGS)
# ══════════════════════════════════════════════════════════════════════════════

class SBERTSearch:
    def __init__(self, articles: List[Dict[str, Any]]):
        self.articles = articles
        self.N = len(articles)
        self.cache = {}
        self._load_cache()

    def _load_cache(self):
        if SBERT_CACHE_PATH.exists():
            try:
                with open(SBERT_CACHE_PATH, "rb") as f:
                    self.cache = pickle.load(f)
            except Exception as e:
                print(f"Erro ao carregar cache do SBERT: {e}")
                self.cache = {}

    def _save_cache(self):
        try:
            SBERT_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(SBERT_CACHE_PATH, "wb") as f:
                pickle.dump(self.cache, f)
        except Exception as e:
            print(f"Erro ao salvar cache do SBERT: {e}")

    def update_cache(self) -> int:
        """Verifica se há novos artigos e calcula os seus embeddings."""
        if self.N == 0:
            return 0
            
        # Identificar quais os PMIDs que não estão na cache
        missing_articles = [art for art in self.articles if art["pmid"] not in self.cache]
        
        if not missing_articles:
            return 0
            
        print(f"SBERT: A calcular embeddings para {len(missing_articles)} novos artigos...")
        model = get_sbert_model()
        
        # Gerar textos para os embeddings (Título + Resumo)
        texts_to_encode = [f"{art.get('titulo', '')} {art.get('resumo', '')}" for art in missing_articles]
        
        # Gerar os embeddings em lote
        embeddings = model.encode(texts_to_encode, show_progress_bar=True)
        
        # Atualizar cache
        for art, emb in zip(missing_articles, embeddings):
            self.cache[art["pmid"]] = emb
            
        self._save_cache()
        print("SBERT: Cache de embeddings atualizada com sucesso.")
        return len(missing_articles)

    def search(self, query: str, top_n: int = 5) -> List[Tuple[Dict[str, Any], float]]:
        if self.N == 0:
            return []
            
        # Garantir que a cache tem os artigos atuais carregados
        # (Se houver artigos em falta que não foram pré-computados, calculamos agora)
        missing_pmids = [art["pmid"] for art in self.articles if art["pmid"] not in self.cache]
        if missing_pmids:
            self.update_cache()
            
        # Carregar modelo SBERT para codificar a query do utilizador
        model = get_sbert_model()
        query_emb = model.encode(query)
        
        results = []
        for art in self.articles:
            pmid = art["pmid"]
            doc_emb = self.cache.get(pmid)
            if doc_emb is not None:
                score = self._cosine_similarity(query_emb, doc_emb)
                # Escalonamento discriminativo para SBERT
                # Mapeamos o intervalo típico [0.35, 0.90] para [0.0, 1.0]
                threshold = 0.35
                max_val = 0.90
                if score > threshold:
                    score_scaled = float((score - threshold) / (max_val - threshold))
                    score_scaled = min(score_scaled, 1.0) # Limitar a 100%
                else:
                    score_scaled = 0.0
                    
                if score_scaled > 0.05:
                    results.append((art, score_scaled))
                
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_n]

    def _cosine_similarity(self, v1: np.ndarray, v2: np.ndarray) -> float:
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(v1, v2) / (norm1 * norm2))


# ══════════════════════════════════════════════════════════════════════════════
# FUNÇÃO UNIFICADA DE PESQUISA
# ══════════════════════════════════════════════════════════════════════════════

def search_articles(query: str, method: str = "tfidf", top_n: int = 5) -> List[Dict[str, Any]]:
    """
    Função principal que coordena a pesquisa sobre os artigos guardados em data/artigos.json.
    Retorna a lista de artigos correspondentes, injetando um campo "score" em cada artigo.
    """
    try:
        from utils.scraper import load_articles
    except ModuleNotFoundError:
        from scraper import load_articles
    articles = load_articles()
    
    if not articles:
        return []
        
    method = method.lower()
    
    if method == "tfidf":
        searcher = TFIDFSearch(articles)
        raw_results = searcher.search(query, top_n)
    elif method == "sbert":
        searcher = SBERTSearch(articles)
        raw_results = searcher.search(query, top_n)
    else:
        # Fallback para TFIDF
        searcher = TFIDFSearch(articles)
        raw_results = searcher.search(query, top_n)
        
    # Formatar o retorno injetando o score formatado em percentagem
    formatted_articles = []
    for art, score in raw_results:
        # Fazer uma cópia para não alterar os dados globais em memória
        art_copy = art.copy()
        art_copy["score"] = round(score * 100, 1) # ex: 0.854 -> 85.4
        formatted_articles.append(art_copy)
        
    return formatted_articles

# CLI de teste rápido
if __name__ == "__main__":
    import sys
    query = "heart diseases"
    method = "tfidf"
    
    if len(sys.argv) > 1:
        query = sys.argv[1]
    if len(sys.argv) > 2:
        method = sys.argv[2]
        
    print(f"Executando pesquisa: '{query}' usando método '{method}'...")
    res = search_articles(query, method, 3)
    for art in res:
        print(f"\n[Score: {art['score']}%] {art['titulo']} (PMID: {art['pmid']})")
        print(f"Resumo: {art['resumo'][:150]}...")
