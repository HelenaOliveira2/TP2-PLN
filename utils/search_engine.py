"""
MedLex Explorer — Motores de Pesquisa Científica (IR).
Implementa pesquisa por TF-IDF (de raiz) e SBERT.
"""

import math
import pickle
import re
from pathlib import Path
import numpy as np

# Caminhos de dados
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
SBERT_CACHE_PATH = _PROJECT_ROOT / "data" / "artigos_embeddings_sbert.pkl"

# Lazy loader para SBERT (carrega apenas quando necessário)
_sbert_model = None

def get_sbert_model():
    global _sbert_model
    if _sbert_model is None:
        print("A carregar modelo SBERT (SentenceTransformer - MedLink Bi-Encoder)...")
        from sentence_transformers import SentenceTransformer
        _sbert_model = SentenceTransformer("lfcc/medlink-bi-encoder")
    return _sbert_model

def clean_and_tokenize(text):
    """Limpa o texto e divide-o em tokens de palavras (minúsculas)."""
    if not text:
        return []
    # Remover pontuação e converter para minúsculas
    text = text.lower()
    text = re.sub(r'\*\*([^*]+)\*\*:', r'\1', text) # remover markdown
    tokens = re.findall(r'\b\w+\b', text)
    return tokens

# ══════════════════════════════════════════════════════════════════════════════
# 1. OPÇÃO A: TF-IDF IMPLEMENTADO DE RAIZ
# ══════════════════════════════════════════════════════════════════════════════

class TFIDFSearch:
    def __init__(self, articles):
        self.articles = articles
        self.N = len(articles)
        self.vocab = set()
        self.df = {}  # Document Frequency
        self.idf = {} # Inverse Document Frequency
        self.doc_vectors = [] # List of {word: tfidf_score} for each doc
        self._build_index()

    def _build_index(self):
        """
        Gera a representação vetorial dispersa (Sparse Vectors) para todos os documentos da coleção.
        Etapas:
        1. Tokenização e cálculo das frequências de termo locais (TF).
        2. Construção do vocabulário global e cálculo da frequência inversa de documento (IDF).
        3. Multiplicação cruzada (TF * IDF) para gerar os vetores finais indexados.
        """
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

    def search(self, query, top_n=5):
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

    def _cosine_similarity(self, v1, v2):
        # Produto escalar
        dot_product = sum(v1[w] * v2.get(w, 0.0) for w in v1)
        # Normas
        norm1 = math.sqrt(sum(x * x for x in v1.values()))
        norm2 = math.sqrt(sum(x * x for x in v2.values()))
        
        if norm1 == 0.0 or norm2 == 0.0:
            return 0.0
        return dot_product / (norm1 * norm2)


# ══════════════════════════════════════════════════════════════════════════════
# 2. OPÇÃO B: SBERT MULTILINGUE PRÉ-TREINADO (COM CACHE DE EMBEDDINGS)
# ══════════════════════════════════════════════════════════════════════════════

class SBERTSearch:
    """
    Motor de Pesquisa Semântica Profunda baseado em Transformers (Sentence-BERT).
    Utiliza arquiteturas siamesas de Deep Learning para gerar representações vetoriais densas (Dense Embeddings),
    permitindo a recuperação de informação com base no significado médico em vez de palavras isoladas.
    
    Implementa caching serializado (pickle) para evitar a recomputação exaustiva dos vetores na CPU.
    """
    def __init__(self, articles):
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

    def update_cache(self):
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

    def search(self, query, top_n=5):
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
                score = float(self._cosine_similarity(query_emb, doc_emb))
                # Usamos a Similaridade de Cosseno pura (como ensinado nas aulas e nos tutoriais oficiais Hugging Face)
                # Adicionamos apenas um filtro mínimo (> 0.10) para excluir lixo matemático.
                if score > 0.10:
                    results.append((art, score))
                
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_n]

    def _cosine_similarity(self, v1, v2):
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(v1, v2) / (norm1 * norm2))


# ══════════════════════════════════════════════════════════════════════════════
# FUNÇÃO UNIFICADA DE PESQUISA
# ══════════════════════════════════════════════════════════════════════════════

def search_articles(query, method="tfidf", top_n=5):
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
