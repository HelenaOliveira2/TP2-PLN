"""
MedLex Explorer — Motor de Question Answering.
Utiliza a arquitetura BERT (fine-tuned localmente) para extração de respostas contextuais.
Permite aos utilizadores fazer perguntas em Português sobre os resumos traduzidos para Português.
"""

from typing import Dict, Any, Optional

import os
import torch
from transformers import AutoTokenizer, AutoModelForQuestionAnswering

# Variáveis globais para guardar o modelo na memória (lazy loading)
_tokenizer = None
_model = None

def get_qa_model():
    """
    Carrega o modelo Fine-Tuned local (caso exista na pasta 'my_awesome_qa_model')
    ou, como fallback, inicializa o modelo de base em língua portuguesa.
    """
    global _tokenizer, _model
    if _model is None:
        _PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        model_path = os.path.join(_PROJECT_ROOT, "my_awesome_qa_model")
        
        if os.path.exists(model_path):
            print("A carregar o NOSSO modelo de QA Treinado (Fine-Tuned)...")
        else:
            print("Aviso: Modelo treinado não encontrado, a carregar modelo pre-treinado tinybert...")
            model_path = "pierreguillou/bert-base-cased-squad-v1.1-portuguese"
            
        _tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=False)
        _model = AutoModelForQuestionAnswering.from_pretrained(model_path)
    return _tokenizer, _model

def answer_question(context, question):
    """
    Recebe um contexto (resumo clínico + metadados) e uma pergunta em linguagem natural.
    Executa inferência na rede BERT e retorna o fragmento textual exato (extractive QA).
    """
    if not context or not question:
        return {"error": "O contexto ou a pergunta estão vazios."}

    try:
        tokenizer, model = get_qa_model()
        
        # Prepara os dados matematicamente para a rede neuronal
        inputs = tokenizer(question, context, return_tensors="pt", max_length=512, truncation="only_second")
        
        # Inferência direta (Bypass da pipeline)
        with torch.no_grad():
            outputs = model(**inputs)
            
        # Calcular início e fim da resposta usando as probabilidades máximas dos tensores
        answer_start_idx = torch.argmax(outputs.start_logits)
        answer_end_idx = torch.argmax(outputs.end_logits) + 1
        
        answer_tokens = inputs["input_ids"][0][answer_start_idx:answer_end_idx]
        answer = tokenizer.decode(answer_tokens, skip_special_tokens=True).strip()
        
        # Calcular confiança do modelo (score) aplicando a função Softmax aos Logits brutos
        start_probs = torch.nn.functional.softmax(outputs.start_logits, dim=-1)
        end_probs = torch.nn.functional.softmax(outputs.end_logits, dim=-1)
        score = float((torch.max(start_probs) + torch.max(end_probs)) / 2) * 100
        
        if answer_start_idx >= answer_end_idx or not answer:
            answer = ""
            score = 0.0
            
        return {
            "answer": answer,
            "score": round(score, 1),
            "start": int(answer_start_idx),
            "end": int(answer_end_idx)
        }
    except Exception as e:
        print(f"Erro ao processar a pergunta: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    sample_context = "Neurodevelopmental impairments are common in children with congenital heart disease."
    sample_question = "What are the common impairments?"
    
    print("A testar motor QA com modelo treinado (BÓNUS)...")
    resposta = answer_question(sample_context, sample_question)
    print("\nResultado:")
    print(resposta)
