"""
Módulo de Enriquecimento de Dados — MedLex Explorer.
Comunica com as APIs públicas do Wikidata e Wikipedia para enriquecer termos médicos.
"""

import requests
import json
import time
from typing import Dict, List, Any, Optional

# Cabeçalho User-Agent recomendado pelas políticas da Wikimedia/Wikidata
HEADERS = {
    "User-Agent": "MedLexExplorer/1.0 (saraa@example.com; estudante de Engenharia Biomédica) python-requests/2.31"
}

WIKIDATA_URL = "https://www.wikidata.org/w/api.php"
WIKIPEDIA_URL = "https://pt.wikipedia.org/w/api.php"

def search_wikidata_entity(term: str) -> Optional[str]:
    """Procura uma entidade no Wikidata pelo termo em português e retorna o ID (Qid)."""
    params = {
        "action": "wbsearchentities",
        "search": term,
        "language": "pt",
        "format": "json"
    }
    try:
        r = requests.get(WIKIDATA_URL, params=params, headers=HEADERS, timeout=8)
        r.raise_for_status()
        data = r.json()
        search_results = data.get("search", [])
        if search_results:
            # Retorna o ID da primeira correspondência
            return search_results[0].get("id")
    except Exception as e:
        print(f"Erro ao pesquisar Wikidata para '{term}': {e}")
    return None

def get_entity_labels(entity_ids: List[str]) -> Dict[str, str]:
    """Obtém os rótulos em português para uma lista de IDs de entidades."""
    if not entity_ids:
        return {}
    params = {
        "action": "wbgetentities",
        "ids": "|".join(entity_ids),
        "props": "labels",
        "languages": "pt",
        "format": "json"
    }
    labels = {}
    try:
        r = requests.get(WIKIDATA_URL, params=params, headers=HEADERS, timeout=8)
        r.raise_for_status()
        data = r.json()
        entities = data.get("entities", {})
        for qid, entity in entities.items():
            pt_label = entity.get("labels", {}).get("pt", {}).get("value")
            if pt_label:
                labels[qid] = pt_label.lower()
    except Exception as e:
        print(f"Erro ao obter rótulos para {entity_ids}: {e}")
    return labels

def fetch_wikidata_details(qid: str) -> Dict[str, Any]:
    """Recupera detalhes da entidade Wikidata: descrição, sinónimos, traduções e categorias."""
    params = {
        "action": "wbgetentities",
        "ids": qid,
        "props": "labels|descriptions|aliases|claims",
        "languages": "pt|en|es",
        "format": "json"
    }
    res = {
        "definicao": None,
        "sinonimos": [],
        "traducoes": {"en": [], "es": []},
        "categorias": []
    }
    
    try:
        r = requests.get(WIKIDATA_URL, params=params, headers=HEADERS, timeout=8)
        r.raise_for_status()
        data = r.json()
        entity = data.get("entities", {}).get(qid, {})
        
        # 1. Definição (Descrição em Português)
        desc_pt = entity.get("descriptions", {}).get("pt", {}).get("value")
        if desc_pt:
            res["definicao"] = desc_pt
            
        # 2. Sinónimos (Aliases em Português)
        aliases_pt = entity.get("aliases", {}).get("pt", [])
        res["sinonimos"] = [item.get("value") for item in aliases_pt if item.get("value")]
        
        # 3. Traduções (Rótulos e aliases em EN e ES)
        for lang in ["en", "es"]:
            label = entity.get("labels", {}).get(lang, {}).get("value")
            if label:
                res["traducoes"][lang].append(label)
            aliases = entity.get("aliases", {}).get(lang, [])
            for item in aliases:
                val = item.get("value")
                if val and val not in res["traducoes"][lang]:
                    res["traducoes"][lang].append(val)
                    
        # 4. Categorias (Baseado em P31 - instance of, e P279 - subclass of)
        claims = entity.get("claims", {})
        category_qids = []
        
        # P31 (instância de) e P279 (subclasse de)
        for prop in ["P31", "P279"]:
            for claim in claims.get(prop, []):
                mainsnak = claim.get("mainsnak", {})
                datavalue = mainsnak.get("datavalue", {})
                value = datavalue.get("value", {})
                if isinstance(value, dict) and value.get("entity-type") == "item":
                    cat_qid = value.get("numeric-id")
                    if cat_qid:
                        category_qids.append(f"Q{cat_qid}")
                        
        if category_qids:
            # Obter os nomes amigáveis em português destas categorias
            labels_map = get_entity_labels(category_qids[:5])  # limitar a 5 para não sobrecarregar
            res["categorias"] = list(labels_map.values())
            
    except Exception as e:
        print(f"Erro ao obter detalhes de Wikidata para {qid}: {e}")
        
    return res

def fetch_wikipedia_summary(term: str) -> Optional[str]:
    """Obtém o resumo introdutório de um artigo na Wikipedia em Português."""
    params = {
        "action": "query",
        "prop": "extracts",
        "exintro": True,
        "explaintext": True,
        "titles": term,
        "format": "json",
        "redirects": 1
    }
    try:
        r = requests.get(WIKIPEDIA_URL, params=params, headers=HEADERS, timeout=8)
        r.raise_for_status()
        data = r.json()
        pages = data.get("query", {}).get("pages", {})
        for page_id, page in pages.items():
            if page_id != "-1": # Página encontrada
                extract = page.get("extract")
                if extract:
                    return extract.strip()
    except Exception as e:
        print(f"Erro ao obter resumo da Wikipedia para '{term}': {e}")
    return None

def enrich_term_data(term: str) -> Dict[str, Any]:
    """
    Enriquece um termo combinando Wikidata e Wikipedia.
    Retorna um dicionário com os campos enriquecidos.
    """
    enrichment = {
        "definicao": None,
        "sinonimos": [],
        "traducoes": {"en": [], "es": []},
        "categorias": []
    }
    
    # 1. Tentar encontrar no Wikidata
    qid = search_wikidata_entity(term)
    if qid:
        details = fetch_wikidata_details(qid)
        enrichment["definicao"] = details["definicao"]
        enrichment["sinonimos"] = details["sinonimos"]
        enrichment["traducoes"] = details["traducoes"]
        enrichment["categorias"] = details["categorias"]
        
    # 2. Tentar na Wikipedia se a definição ainda estiver vazia ou for muito curta (< 20 caracteres)
    if not enrichment["definicao"] or len(enrichment["definicao"]) < 20:
        wiki_desc = fetch_wikipedia_summary(term)
        if wiki_desc:
            enrichment["definicao"] = wiki_desc
            
    return enrichment

# ══════════════════════════════════════════════════════════════════════════════
# Script CLI para enriquecimento em lote (Batch Mode)
# ══════════════════════════════════════════════════════════════════════════════

def batch_enrich(limit: int = 10, force: bool = False):
    """
    Enriquece termos no dicionário JSON local que não têm definições.
    Limita o número de termos processados de cada vez para respeitar as APIs.
    """
    from pathlib import Path
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from utils.data_manager import get_data, save_data
    
    data = get_data()
    count = 0
    
    print(f"A iniciar enriquecimento em lote (limite={limit}, forçar={force})...")
    
    for key, entry in data.items():
        if count >= limit:
            break
            
        term = entry.get("termo_principal", key)
        has_def = bool(entry.get("definicoes"))
        has_syn = bool(entry.get("sinonimos"))
        
        # Enriquecer se não tiver definição, ou se a opção force=True estiver ativa
        if not has_def or force:
            print(f"A processar termo: '{term}'...")
            enrichment = enrich_term_data(term)
            
            updated = False
            
            # Adicionar definição se obtida
            if enrichment["definicao"]:
                # Manter definição antiga se existir e não forçarmos
                if not entry.get("definicoes"):
                    entry["definicoes"] = [enrichment["definicao"]]
                elif force:
                    # Colocar à cabeça
                    if enrichment["definicao"] not in entry["definicoes"]:
                        entry["definicoes"].insert(0, enrichment["definicao"])
                updated = True
                
            # Adicionar sinónimos
            if enrichment["sinonimos"]:
                existing_syns = entry.get("sinonimos", [])
                for syn in enrichment["sinonimos"]:
                    if syn.lower() != term.lower() and syn not in existing_syns:
                        existing_syns.append(syn)
                entry["sinonimos"] = existing_syns
                updated = True
                
            # Adicionar categorias
            if enrichment["categorias"]:
                existing_cats = entry.get("categorias", [])
                for cat in enrichment["categorias"]:
                    # Dividir e limpar termos
                    clean_cat = cat.strip()
                    if clean_cat and clean_cat not in existing_cats:
                        existing_cats.append(clean_cat)
                entry["categorias"] = existing_cats
                updated = True
                
            # Adicionar traduções
            for lang in ["en", "es"]:
                if enrichment["traducoes"][lang]:
                    trads = entry.setdefault("traducoes", {})
                    existing_lang_trads = trads.setdefault(lang, [])
                    # Se for string em vez de lista por algum motivo
                    if isinstance(existing_lang_trads, str):
                        existing_lang_trads = [x.strip() for x in existing_lang_trads.split(",") if x.strip()]
                    
                    for t in enrichment["traducoes"][lang]:
                        if t not in existing_lang_trads:
                            existing_lang_trads.append(t)
                    trads[lang] = existing_lang_trads
                    updated = True
            
            if updated:
                count += 1
                # Pequena pausa para respeitar limites da API
                time.sleep(0.5)
                
    if count > 0:
        save_data(data)
        print(f"Sucesso: {count} termos enriquecidos e guardados em DICIONARIO_GIGANTE_FINAL.json.")
    else:
        print("Nenhum termo a enriquecer ou limite atingido sem modificações.")

if __name__ == "__main__":
    # Teste rápido do script
    import sys
    if len(sys.argv) > 1:
        term_to_test = sys.argv[1]
        print(f"Testando enriquecimento de: '{term_to_test}'")
        res = enrich_term_data(term_to_test)
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        # Por defeito testa com "fémur"
        print("Testando com termo padrão 'fémur':")
        res = enrich_term_data("fémur")
        print(json.dumps(res, indent=2, ensure_ascii=False))
