"""
MedLex Explorer — Motor de Question Answering (Fase 4).
Utiliza um modelo BERT multilingue pré-treinado no HuggingFace.
Permite aos utilizadores fazer perguntas em Português sobre textos em Inglês.
"""

from typing import Dict, Any, Optional

# Variável global para guardar o modelo na memória (lazy loading)
_qa_pipeline = None

def get_qa_pipeline():
    """
    Carrega o modelo de Question Answering.
    Usa 'deepset/xlm-roberta-base-squad2' que é multilingue e da arquitetura BERT.
    """
    global _qa_pipeline
    if _qa_pipeline is None:
        print("A carregar modelo de Question Answering (Multilingue)...")
        from transformers import pipeline
        
        # Este modelo XLM-RoBERTa permite perguntas em PT e contexto em EN
        _qa_pipeline = pipeline(
            "question-answering",
            model="deepset/xlm-roberta-base-squad2",
            tokenizer="deepset/xlm-roberta-base-squad2"
        )
    return _qa_pipeline

def answer_question(context: str, question: str) -> Dict[str, Any]:
    """
    Recebe um contexto (resumo do artigo) e uma pergunta.
    Retorna a resposta exata extraída do texto.
    """
    if not context or not question:
        return {"error": "O contexto ou a pergunta estão vazios."}

    try:
        qa_pipeline = get_qa_pipeline()
        
        # A pipeline devolve um dicionário com: score, start, end, answer
        result = qa_pipeline(question=question, context=context)
        
        return {
            "answer": result.get("answer", ""),
            "score": round(result.get("score", 0.0) * 100, 1), # Converter para percentagem
            "start": result.get("start", 0),
            "end": result.get("end", 0)
        }
    except Exception as e:
        print(f"Erro ao processar a pergunta: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    # Teste rápido do script
    sample_context = "Neurodevelopmental impairments are common in children with congenital heart disease."
    sample_question = "Quais as doenças mais comuns em crianças com problemas de coração?"
    
    print("A testar motor QA Multilingue...")
    print(f"Contexto (EN): {sample_context}")
    print(f"Pergunta (PT): {sample_question}")
    
    resposta = answer_question(sample_context, sample_question)
    print("\nResultado:")
    print(resposta)
