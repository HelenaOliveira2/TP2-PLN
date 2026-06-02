"""
MedLex Explorer — Script de Bónus (Fase 4): Fine-Tuning do modelo QA
Este ficheiro é a cópia EXATA do tutorial oficial do HuggingFace (passo a passo):
Link: https://huggingface.co/docs/transformers/tasks/question_answering

As únicas adaptações foram: 
1. Em vez de usar o dataset "squad" genérico, usamos um pequeno dicionário com dados médicos (para cumprir o vosso enunciado).
2. O nome do modelo que vamos afinar é o nosso multilingue ("deepset/xlm-roberta-base-squad2").
"""

# 1. CARREGAR OS DADOS (No tutorial fazem: load_dataset("squad"))
from datasets import Dataset

# Criamos um "squad" médico simulado para cumprir o requisito de dataset clínico
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
squad = Dataset.from_dict(dados_medicos)
# Dividir em treino e teste (Exatamente como no tutorial)
squad = squad.train_test_split(test_size=0.5)


# 2. CARREGAR TOKENIZADOR
from transformers import AutoTokenizer
# No tutorial usam distilbert, nós usamos o nosso
tokenizer = AutoTokenizer.from_pretrained("deepset/xlm-roberta-base-squad2")


# 3. FUNÇÃO DE PRÉ-PROCESSAMENTO (Exatamente igual ao tutorial)
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


# 4. APLICAR PRÉ-PROCESSAMENTO AO DATASET
tokenized_squad = squad.map(preprocess_function, batched=True, remove_columns=squad["train"].column_names)


# 5. DATA COLLATOR (Passo do tutorial que faltava!)
from transformers import DefaultDataCollator
data_collator = DefaultDataCollator()


# 6. MODELO E ARGUMENTOS DE TREINO (Exatamente como no tutorial)
from transformers import AutoModelForQuestionAnswering, TrainingArguments, Trainer
model = AutoModelForQuestionAnswering.from_pretrained("deepset/xlm-roberta-base-squad2")

training_args = TrainingArguments(
    output_dir="my_awesome_qa_model",
    evaluation_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=16,
    num_train_epochs=3,
    weight_decay=0.01,
    push_to_hub=False, # Não queremos publicar no site da HuggingFace
)


# 7. O TRAINER
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_squad["train"],
    eval_dataset=tokenized_squad["test"],
    tokenizer=tokenizer,
    data_collator=data_collator,
)


# 8. TREINAR!
if __name__ == "__main__":
    print("A iniciar o treino exatamente como no tutorial do HuggingFace...")
    # trainer.train()
    print("Para correr o treino a sério, descomenta a linha 'trainer.train()'.")
