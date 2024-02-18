import pandas as pd
from utils import (
    load_toml,
    prepare_training_conversation,
    write_jsonl,
    num_tokens_from_string,
    print_fine_tune_status,
    print_training_process
)

import openai
import tiktoken

config = load_toml("fine_tune_specification.toml")
df = pd.read_csv(config['data']['dataset'])
model_name = config["model"]["model_name"]
system_message = config['system_message']['system_message']
train_ratio = config['training']['train_ratio']

print("System_message for your prompt: ", system_message)

client = openai.OpenAI(api_key=config['model']['OPENAI_API_KEY'])

data = df.apply(lambda x: prepare_training_conversation(x, system_message), axis=1).tolist()

write_jsonl(data[:int(len(data)*train_ratio)], config["data"]["train_json"])
write_jsonl(data[int(len(data)*train_ratio):], config["data"]["val_json"])

encoder = tiktoken.encoding_for_model(model_name)
lengths = []
for answer in df.assistant:
    lengths.append(num_tokens_from_string(answer, encoder))
print("The max token length of the assistant responses is ", max(lengths))

print("\n")

with open(config["data"]["train_json"], "rb") as training_fd:
    training_response = client.files.create(
        file=training_fd, purpose="fine-tune"
    )

training_file_id = training_response.id

with open(config["data"]["val_json"], "rb") as validation_fd:
    validation_response = client.files.create(
        file=validation_fd, purpose="fine-tune"
    )
validation_file_id = validation_response.id

response = client.fine_tuning.jobs.create(
    training_file=training_file_id,
    validation_file=validation_file_id,
    model=model_name,
    suffix=config['model']['finetune_model_suffix'],
    hyperparameters={
    "n_epochs":config['training']['n_epochs'],
    "batch_size": config['training']['batch_size']
  }
)


print_fine_tune_status(response)
print("\n")

print_training_process(response.id, client)
print("\n")



