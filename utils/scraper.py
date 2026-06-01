"""
MedLex Explorer — Módulo de Web Scraping do PubMed.
Recolhe artigos científicos da base de dados médica PubMed do NCBI.
"""

import os
import json
import requests
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any

# Caminho para o ficheiro de artigos na pasta 'data'
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
ARTIGOS_PATH = _PROJECT_ROOT / "data" / "artigos.json"

HEADERS = {
    "User-Agent": "MedLexExplorer/1.0 (saraa@example.com; estudante de Engenharia Biomédica) python-requests/2.31"
}

def load_articles() -> List[Dict[str, Any]]:
    """Carrega a lista de artigos salvos localmente."""
    if not ARTIGOS_PATH.exists():
        return []
    try:
        with open(ARTIGOS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Erro ao carregar artigos: {e}")
        return []

def save_articles(articles: List[Dict[str, Any]]) -> None:
    """Guarda a lista de artigos no ficheiro JSON."""
    ARTIGOS_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(ARTIGOS_PATH, "w", encoding="utf-8") as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Erro ao guardar artigos: {e}")

def search_pubmed(query: str, max_results: int = 10) -> List[str]:
    """
    Pesquisa no PubMed usando a API ESearch.
    Retorna uma lista de PubMed IDs (PMIDs).
    """
    search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": query,
        "retmode": "json",
        "retmax": max_results
    }
    try:
        r = requests.get(search_url, params=params, headers=HEADERS, timeout=10)
        r.raise_for_status()
        data = r.json()
        return data.get("esearchresult", {}).get("idlist", [])
    except Exception as e:
        print(f"Erro ao pesquisar PubMed para '{query}': {e}")
        return []

def fetch_pubmed_abstracts(pmids: List[str]) -> List[Dict[str, Any]]:
    """
    Recupera metadados e resumos do PubMed usando a API EFetch (XML).
    Retorna uma lista de dicionários com os dados estruturados de cada artigo.
    """
    if not pmids:
        return []
        
    fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml"
    }
    
    articles_list = []
    try:
        r = requests.get(fetch_url, params=params, headers=HEADERS, timeout=15)
        r.raise_for_status()
        
        # Fazer parse do XML retornado
        root = ET.fromstring(r.content)
        
        for pubmed_article in root.findall(".//PubmedArticle"):
            # 1. PMID
            pmid_el = pubmed_article.find(".//PMID")
            pmid = pmid_el.text if pmid_el is not None else ""
            if not pmid:
                continue
                
            # 2. Título (Title)
            title_el = pubmed_article.find(".//ArticleTitle")
            title = "".join(title_el.itertext()).strip() if title_el is not None else "Sem título"
            
            # 3. Autores (Authors)
            authors = []
            for author in pubmed_article.findall(".//Author"):
                last_name_el = author.find("LastName")
                fore_name_el = author.find("ForeName")
                initials_el = author.find("Initials")
                
                last_name = last_name_el.text if last_name_el is not None else ""
                initials = initials_el.text if initials_el is not None else ""
                
                if last_name:
                    authors.append(f"{last_name} {initials}".strip())
            
            authors_str = ", ".join(authors) if authors else "Autor desconhecido"
            
            # 4. Revista (Journal)
            journal_el = pubmed_article.find(".//Journal/Title")
            journal = journal_el.text if journal_el is not None else "Revista desconhecida"
            
            # 5. Data de Publicação (Publication Date)
            pub_date_el = pubmed_article.find(".//JournalIssue/PubDate")
            pub_year = ""
            if pub_date_el is not None:
                year_el = pub_date_el.find("Year")
                medline_date_el = pub_date_el.find("MedlineDate")
                if year_el is not None:
                    pub_year = year_el.text
                elif medline_date_el is not None:
                    pub_year = medline_date_el.text.split()[0] # ex: '2024 Spring' -> '2024'
            
            pub_year = pub_year or "Data desconhecida"
            
            # 6. Resumo (Abstract)
            abstract_els = pubmed_article.findall(".//AbstractText")
            abstract_parts = []
            for ab in abstract_els:
                # PubMed abstracts podem ter secções rotuladas (ex: Background, Methods, Results, Conclusion)
                label = ab.get("Label")
                text = "".join(ab.itertext()).strip()
                if text:
                    if label:
                        abstract_parts.append(f"**{label}**: {text}")
                    else:
                        abstract_parts.append(text)
            
            abstract = "\n\n".join(abstract_parts) if abstract_parts else "Resumo não disponível."
            
            articles_list.append({
                "pmid": pmid,
                "titulo": title,
                "autores": authors_str,
                "revista": journal,
                "data": pub_year,
                "resumo": abstract
            })
            
    except Exception as e:
        print(f"Erro ao ler detalhes dos PMIDs {pmids}: {e}")
        
    return articles_list

def scrape_and_save_articles(query: str, max_results: int = 10) -> int:
    """
    Pesquisa e descarrega artigos do PubMed.
    Filtra duplicados e guarda os novos artigos na coleção local.
    Retorna o número de novos artigos adicionados.
    """
    print(f"Pesquisando PubMed para query='{query}' (max={max_results})...")
    pmids = search_pubmed(query, max_results)
    
    if not pmids:
        print("Nenhum artigo encontrado.")
        return 0
        
    existing_articles = load_articles()
    existing_pmids = {art["pmid"] for art in existing_articles}
    
    # Filtrar PMIDs que ainda não foram descarregados
    new_pmids = [pmid for pmid in pmids if pmid not in existing_pmids]
    
    if not new_pmids:
        print("Todos os artigos encontrados já existem na coleção local.")
        return 0
        
    print(f"A descarregar {len(new_pmids)} novos artigos...")
    new_articles = fetch_pubmed_abstracts(new_pmids)
    
    # Adicionar a informação do termo de pesquisa aos novos artigos
    for art in new_articles:
        art["termo_pesquisa"] = query.lower()
        
    # Combinar e guardar
    all_articles = existing_articles + new_articles
    save_articles(all_articles)
    
    print(f"Sucesso: {len(new_articles)} novos artigos adicionados à coleção local!")
    return len(new_articles)

# CLI interface para testes diretos
if __name__ == "__main__":
    import sys
    query_term = "hypertension"
    limit = 5
    if len(sys.argv) > 1:
        query_term = sys.argv[1]
    if len(sys.argv) > 2:
        try:
            limit = int(sys.argv[2])
        except ValueError:
            pass
            
    print(f"Executando CLI scraper para '{query_term}' (limite={limit})...")
    new_added = scrape_and_save_articles(query_term, limit)
    print(f"Novos artigos adicionados: {new_added}")
