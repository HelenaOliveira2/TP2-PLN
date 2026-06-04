#CARREGAR OS DADOS 
from datasets import Dataset

dados_medicos = {
    "id": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
    "title": ["Meningite", "Coração", "Diabetes", "Hipertensão", "Asma", "Tuberculose", "Artrite", "Alzheimer", "Enxaqueca", "Glaucoma"],
    "context": [
        "A meningite caracteriza-se por uma inflamação perigosa que causa febre alta e rigidez no pescoço.",
        "O enfarte do miocárdio bloqueia o fluxo de sangue no coração.",
        "A diabetes tipo 1 ocorre quando o pâncreas não produz insulina suficiente para o corpo.",
        "A hipertensão arterial é uma condição clínica que aumenta o risco de acidente vascular cerebral.",
        "A asma brônquica manifesta-se através de episódios recorrentes de falta de ar e pieira.",
        "A tuberculose é uma doença infeciosa grave provocada pela bactéria Mycobacterium tuberculosis.",
        "A artrite reumatoide causa uma inflamação crónica que afeta principalmente as articulações das mãos.",
        "O sintoma inicial mais comum da doença de Alzheimer é a perda de memória a curto prazo.",
        "O tratamento para as crises agudas de enxaqueca envolve frequentemente a administração de triptanos.",
        "O glaucoma resulta habitualmente de uma pressão intraocular elevada que danifica o nervo ótico."
    ],
    "question": [
        "Quais são os sintomas da meningite?",
        "O que bloqueia o enfarte do miocárdio?",
        "O que é que o pâncreas não produz na diabetes tipo 1?",
        "A hipertensão aumenta o risco de quê?",
        "Quais são as manifestações da asma?",
        "Que bactéria provoca a tuberculose?",
        "O que é que a artrite reumatoide afeta principalmente?",
        "Qual é o sintoma inicial da doença de Alzheimer?",
        "O que se administra para tratar a enxaqueca?",
        "O que causa danos ao nervo ótico no glaucoma?"
    ],
    "answers": [
        {"text": ["febre alta e rigidez no pescoço"], "answer_start": [61]},
        {"text": ["fluxo de sangue"], "answer_start": [34]},
        {"text": ["insulina"], "answer_start": [54]},
        {"text": ["acidente vascular cerebral"], "answer_start": [69]},
        {"text": ["falta de ar e pieira"], "answer_start": [66]},
        {"text": ["Mycobacterium tuberculosis"], "answer_start": [67]},
        {"text": ["articulações das mãos"], "answer_start": [77]},
        {"text": ["perda de memória a curto prazo"], "answer_start": [56]},
        {"text": ["triptanos"], "answer_start": [90]},
        {"text": ["pressão intraocular elevada"], "answer_start": [40]}
    ]
}

#raw_datasets = load_dataset("squad_v1_pt")
#squad = Dataset.from_dict(raw_datasets)

# -----------------------------------------------------------------------------
# PASSO 1: CARREGAMENTO DO DATASET
# Em vez de carregar um dataset genérico (ex: "squad" em inglês) via HuggingFace Hub,
# injetamos um dataset médico estruturado localmente para cumprir os requisitos do projeto.
# Cada entrada requer 3 componentes:
#   - question: A string de interrogação.
#   - context: O texto base onde reside a resposta.
#   - answers: Dicionário contendo o excerto da resposta exata e a posição do char inicial (answer_start).
# -----------------------------------------------------------------------------
squad = Dataset.from_dict(dados_medicos)

# Dividir estatisticamente o corpus em subconjuntos de Treino (50%) e Teste/Avaliação (50%)
squad = squad.train_test_split(test_size=0.5)

from transformers import AutoTokenizer
# -----------------------------------------------------------------------------
# PASSO 2: CARREGAMENTO DO TOKENIZADOR E MODELO PRÉ-TREINADO
# O Tokenizador converte texto legível em vetores numéricos de ID (Input IDs) e
# gera máscaras de atenção (Attention Masks) essenciais para a arquitetura Transformers.
# Utilizamos o modelo BERT pré-treinado em PT para maximizar a precisão gramatical.
# -----------------------------------------------------------------------------
model_name = "pierreguillou/bert-base-cased-squad-v1.1-portuguese"

tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=False)


# -----------------------------------------------------------------------------
# PASSO 3: PRÉ-PROCESSAMENTO VETORIAL (MAPEAR TEXTO PARA TENSORS)
# Esta função mapeia as coordenadas dos caracteres (texto humano)
# para coordenadas de tokens (IDs numéricos gerados pelo tokenizador).
# -----------------------------------------------------------------------------
def preprocess_function(examples):
    questions = [q.strip() for q in examples["question"]]
    inputs = tokenizer(
        questions,
        examples["context"],
        max_length=384,
        truncation="only_second",
        return_offsets_mapping=True,
        padding="max_length",
    )

    offset_mapping = inputs.pop("offset_mapping")
    answers = examples["answers"]
    start_positions = []
    end_positions = []

    for i, offset in enumerate(offset_mapping):
        answer = answers[i]
        start_char = answer["answer_start"][0]
        end_char = answer["answer_start"][0] + len(answer["text"][0])
        sequence_ids = inputs.sequence_ids(i)

        # Encontrar início e fim do contexto
        idx = 0
        while sequence_ids[idx] != 1:
            idx += 1
            if idx >= len(sequence_ids): break
            
        context_start = idx
        while idx < len(sequence_ids) and sequence_ids[idx] == 1:
            idx += 1
        context_end = idx - 1

        if context_start >= len(sequence_ids) or offset[context_start][0] > end_char or offset[context_end][1] < start_char:
            start_positions.append(0)
            end_positions.append(0)
        else:
            idx = context_start
            while idx <= context_end and offset[idx][0] <= start_char:
                idx += 1
            start_positions.append(idx - 1)

            idx = context_end
            while idx >= context_start and offset[idx][1] >= end_char:
                idx -= 1
            end_positions.append(idx + 1)

    inputs["start_positions"] = start_positions
    inputs["end_positions"] = end_positions
    return inputs


# -----------------------------------------------------------------------------
# PASSO 4: APLICAÇÃO EM LOTE (BATCH MAPPING)
# -----------------------------------------------------------------------------
tokenized_squad = squad.map(preprocess_function, batched=True, remove_columns=squad["train"].column_names)


# -----------------------------------------------------------------------------
# PASSO 5: DATA COLLATOR
# Prepara os lotes (batches) dinâmicos e aplica "padding" se necessário para
# garantir que todos os tensores têm o mesmo tamanho durante a época de treino.
# -----------------------------------------------------------------------------
from transformers import DefaultDataCollator
data_collator = DefaultDataCollator()


# -----------------------------------------------------------------------------
# PASSO 6: MODELO EXTRATIVO (HEAD) E HIPERPARÂMETROS DE TREINO (EPOCHS E LEARNING RATE)
# -----------------------------------------------------------------------------
from transformers import AutoModelForQuestionAnswering, TrainingArguments, Trainer
model = AutoModelForQuestionAnswering.from_pretrained(model_name)

training_args = TrainingArguments(
    output_dir="my_awesome_qa_model",
    eval_strategy="epoch",  # Avaliar o erro em cada época (epoch)
    learning_rate=2e-5,     # Taxa de aprendizagem lenta (Fine-Tuning) para não esquecer os pesos antigos
    per_device_train_batch_size=2,
    per_device_eval_batch_size=2,
    num_train_epochs=3,     # O dataset vai ser processado 3 vezes
    weight_decay=0.01,
    push_to_hub=False,      # Modelo fica apenas guardado localmente (Offline)
)


# 7. O TRAINER
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_squad["train"],
    eval_dataset=tokenized_squad["test"],
    #tokenizer=tokenizer,
    data_collator=data_collator,
)


# 8. TREINAR
if __name__ == "__main__":
    print("A iniciar o treino...")
    trainer.train()
    print("Treino concluído com sucesso!")
    
    import os
    save_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "my_awesome_qa_model"))
    trainer.save_model(save_path)
    tokenizer.save_pretrained(save_path)
    print(f"O teu modelo personalizado foi guardado na pasta '{save_path}'!")
