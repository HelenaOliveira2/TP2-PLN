"""
MedLex Explorer — Módulo de Importação de Artigos Científicos.
Realiza Web Scraping no PubMed (via API Entrez) para importar novos artigos e gere a inicialização da base de dados local com os Casos Clínicos da SPMI.
"""

import os
import json
import re
from pathlib import Path
from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup

# Caminhos para os ficheiros
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
ARTIGOS_PATH = _PROJECT_ROOT / "data" / "artigos.json"
DATASET_PATH = _PROJECT_ROOT / "dataset_articles.json"

def clean_html(text):
    """Remove tags HTML, CSS injetado de SVGs, links e normaliza os espaços em branco."""
    if not text:
        return ""
    
    # 1. Remover lixo CSS injetado de SVGs (ex: .st0{fill:#A6CE39;})
    text = re.sub(r'\.st\d+\{.*?\}', '', text)
    
    # 2. Remover links indesejados (ex: https://orcid.org/...)
    text = re.sub(r'https?://[^\s]+', '', text)
    
    # 3. Remover tags HTML
    clean = re.compile('<.*?>')
    text = re.sub(clean, '', text)
    
    # 4. Normalizar espaços
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def initialize_from_dataset():
    """
    Inicializa a base de dados local (artigos.json) com os artigos do dataset_articles.json,
    filtrando e limpando os dados.
    """
    if not DATASET_PATH.exists():
        print(f"Aviso: dataset_articles.json não encontrado em {DATASET_PATH}")
        return
        
    try:
        with open(DATASET_PATH, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
            
        filtered_data = []
        for doc in raw_data:
            abstract = doc.get("abstract", "")
            keywords = doc.get("keywords", "")
            
            # Filtros de qualidade: abstract > 50 e keywords > 1
            if abstract and len(abstract) > 50 and keywords and len(keywords) > 1:
                # Filtrar placeholders de resumos não disponíveis
                if abstract.strip().lower() in ["não aplicável", "na", "não disponivel", "não disponível", "."]:
                    continue
                    
                link = doc.get("link", "")
                match = re.search(r"id=(\d+)", link)
                pmid = match.group(1) if match else link
                
                filtered_data.append({
                    "pmid": pmid,
                    "titulo": clean_html(doc.get("title", "Sem título")),
                    "autores": clean_html(doc.get("authors", "Autor desconhecido")),
                    "revista": clean_html(doc.get("journal", "Revista desconhecida")),
                    "data": clean_html(doc.get("publication Date", "Data desconhecida")),
                    "resumo": clean_html(abstract),
                    "termo_pesquisa": clean_html(keywords),
                    "link": link
                })
                
        save_articles(filtered_data)
        print(f"Sucesso: {len(filtered_data)} artigos inicializados a partir de dataset_articles.json.")
        
        # Eliminar a cache antiga do SBERT para forçar a re-computação com os novos artigos
        cache_sbert = _PROJECT_ROOT / "data" / "artigos_embeddings_sbert.pkl"
        if cache_sbert.exists():
            try:
                cache_sbert.unlink()
                print("Cache antiga de embeddings do SBERT eliminada.")
            except Exception as e:
                print(f"Erro ao eliminar cache SBERT: {e}")
                
    except Exception as e:
        print(f"Erro ao inicializar artigos a partir do dataset: {e}")

def load_articles():
    """Carrega a lista de artigos salvos localmente, inicializando se necessário."""
    need_init = True
    if ARTIGOS_PATH.exists():
        try:
            with open(ARTIGOS_PATH, "r", encoding="utf-8") as f:
                articles = json.load(f)
                # Se já tiver artigos e pelo menos um contiver o campo 'link', já está inicializado
                if articles and any("link" in art for art in articles):
                    need_init = False
        except Exception:
            pass

    if need_init:
        print("A inicializar base de dados de artigos a partir do dataset da SPMI...")
        initialize_from_dataset()

    try:
        with open(ARTIGOS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Erro ao carregar artigos: {e}")
        return []

def save_articles(articles):
    """Guarda a lista de artigos no ficheiro JSON."""
    ARTIGOS_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(ARTIGOS_PATH, "w", encoding="utf-8") as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Erro ao guardar artigos: {e}")

def scrape_and_save_articles(query, max_results=10):
    """
    Realiza o web scraping real no PubMed utilizando a API Entrez E-utilities
    e processa o XML retornado com o BeautifulSoup, extraindo os metadados do artigo.
    """
    try:
        existing_articles = load_articles()
        existing_pmids = {art["pmid"] for art in existing_articles}
        
        # 1. Pesquisa no PubMed para obter IDs de artigos (PMIDs) correspondentes à query
        search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        # é pedido o dobro de max_results para o caso de termos IDs repetidos
        search_params = {
            "db": "pubmed",
            "term": query,
            "retmode": "json",
            "retmax": max_results * 2
        }
        
        r_search = requests.get(search_url, params=search_params, timeout=10)
        r_search.raise_for_status()
        search_data = r_search.json()
        pmids = search_data.get("esearchresult", {}).get("idlist", [])
        
        if not pmids:
            print(f"Nenhum artigo encontrado no PubMed para a pesquisa: '{query}'")
            return 0
            
        new_articles = []
        
        # 2. Para cada PMID, ir buscar os detalhes em XML e extrair metadados
        for pmid in pmids:
            if pmid in existing_pmids:
                continue
                
            fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
            fetch_params = {
                "db": "pubmed",
                "id": pmid,
                "retmode": "xml"
            }
            
            try:
                r_fetch = requests.get(fetch_url, params=fetch_params, timeout=10)
                r_fetch.raise_for_status()
                
                # Usamos BeautifulSoup com parser 'xml'  (BeautifulSoup + requests)
                soup = BeautifulSoup(r_fetch.text, "xml")
                
                # Extrair o Título (ArticleTitle)
                title_node = soup.find("ArticleTitle")
                title = title_node.text.strip() if title_node else "Sem título"
                
                # Extrair o Resumo (AbstractText)
                abstract_nodes = soup.find_all("AbstractText")
                abstract = " ".join([node.text.strip() for node in abstract_nodes if node.text])
                
                # Filtro de qualidade: se não tiver resumo ou se for muito curto, ignorar
                if not abstract or len(abstract) <= 50:
                    continue
                    
                # ---------------- TRADUÇÃO AUTOMÁTICA ----------------
                try:
                    from deep_translator import GoogleTranslator
                    translator = GoogleTranslator(source='en', target='pt')
                    title = translator.translate(title)
                    
                    # O Google Translate tem um limite de ~5000 caracteres, mas os abstracts raramente passam disso
                    if len(abstract) > 4900:
                        abstract = abstract[:4900]
                    abstract = translator.translate(abstract)
                except Exception as e:
                    print(f"Erro ao traduzir (mantendo em Inglês): {e}")
                # ------------------------------------------------------------------
                
                # Extrair Autores (AuthorList)
                authors_list = []
                author_nodes = soup.find_all("Author")
                for auth in author_nodes:
                    last = auth.find("LastName")
                    fore = auth.find("ForeName")
                    initials = auth.find("Initials")
                    
                    if last and initials:
                        authors_list.append(f"{last.text} {initials.text}")
                    elif last and fore:
                        authors_list.append(f"{last.text} {fore.text}")
                    elif last:
                        authors_list.append(last.text)
                    elif fore:
                        authors_list.append(fore.text)
                        
                authors = ", ".join(authors_list) if authors_list else "Autor desconhecido"
                
                # Extrair Revista (Journal Title)
                journal_node = soup.find("Journal")
                journal = journal_node.find("Title").text.strip() if journal_node and journal_node.find("Title") else "Revista desconhecida"
                
                # Extrair Data de Publicação (PubDate)
                pub_date = soup.find("PubDate")
                date_str = "Data desconhecida"
                if pub_date:
                    year = pub_date.find("Year")
                    month = pub_date.find("Month")
                    if year:
                        date_str = year.text.strip()
                        if month:
                            date_str += f"-{month.text.strip()}"
                    else:
                        medline = pub_date.find("MedlineDate")
                        if medline:
                            date_str = medline.text.strip()
                            
                # Extrair Palavras-chave (Keyword)
                keyword_nodes = soup.find_all("Keyword")
                keywords_list = [k.text.strip() for k in keyword_nodes if k.text]
                # Se não houver palavras-chave na API, usa a própria query de pesquisa como tópico
                keywords = ", ".join(keywords_list) if keywords_list else query
                
                # Adicionar artigo estruturado
                new_articles.append({
                    "pmid": pmid,
                    "titulo": clean_html(title),
                    "autores": clean_html(authors),
                    "revista": clean_html(journal),
                    "data": clean_html(date_str),
                    "resumo": clean_html(abstract),
                    "termo_pesquisa": clean_html(keywords),
                    "link": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                })
                
                # Se já atingimos o limite pretendido, paramos
                if len(new_articles) >= max_results:
                    break
                    
            except Exception as e:
                print(f"Erro ao extrair metadados do artigo {pmid}: {e}")
                continue
                
        if not new_articles:
            return 0
            
        all_articles = existing_articles + new_articles
        save_articles(all_articles)
        
        # Eliminar a cache antiga do SBERT para forçar a re-computação com os novos artigos
        cache_sbert = _PROJECT_ROOT / "data" / "artigos_embeddings_sbert.pkl"
        if cache_sbert.exists():
            try:
                cache_sbert.unlink()
                print("Cache antiga de embeddings do SBERT eliminada.")
            except Exception as e:
                print(f"Erro ao eliminar cache SBERT: {e}")
                
        return len(new_articles)
        
    except Exception as e:
        print(f"Erro ao realizar web scraping do PubMed: {e}")
        return 0

# CLI interface para testes diretos
if __name__ == "__main__":
    print("Inicializando base de artigos...")
    articles = load_articles()
    print(f"Total de artigos carregados: {len(articles)}")
