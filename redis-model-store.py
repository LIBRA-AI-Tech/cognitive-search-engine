#!/usr/bin/env python
import os
from transformers import AutoTokenizer, AutoModel
import torch
from redisai import Client

try:
    r = Client(host=os.getenv('REDIS_HOST'), port=os.getenv('REDIS_PORT'))
    if r.exists('model_details') == 1 and r.hexists('model_details', 'name') and r.hget('model_details', 'name').decode() == os.getenv('MODEL_NAME'):
        exit(0)
    # Sentence-transformers model to TorchScript
    model_name = os.getenv('MODEL_NAME')
    model_path = os.getenv('MODEL_PATH')
    tag = os.getenv('MODEL_TAG')
    elastic_index = os.getenv('ELASTIC_INDEX')
    device = os.getenv('ML_DEVICE', 'CPU')

    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModel.from_pretrained(model_path, torchscript=True).eval()

    encoded_input = tokenizer(
        "prompt text",
        max_length=int(os.getenv("MAX_TOKEN", 512)),
        padding=True,
        truncation=True,
        return_tensors="pt"
    )
    torchscript = "/var/local/traced_model.pt"
    with torch.no_grad():
        traced_model = torch.jit.trace(model, (encoded_input['input_ids'], encoded_input['attention_mask']))
    torch.jit.save(traced_model, torchscript)

    # Store to RedisAI
    with open(torchscript, 'rb') as f:
        model = f.read()
    response = r.modelstore("model", 'TORCH', device, model, tag=tag)
    r.hset('model_details', mapping={'name': model_name, 'path': model_path, 'index': elastic_index, 'tag': tag})
except Exception as e:
    print(str(e))
    exit(1)
if response != 'OK':
    print('NOK')
    exit(1)
