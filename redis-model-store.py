#!/usr/bin/env python
import os
from transformers import AutoTokenizer, AutoModel
import torch
from redisai import Client

try:
    # Sentence-transformers model to TorchScript
    model_path = '/var/local/model'
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModel.from_pretrained(model_path, torchscript=True).eval()

    encoded_input = tokenizer("prompt text", padding=True, truncation=True, return_tensors="pt")
    torchscript = "var/local/traced_model.pt"
    with torch.no_grad():
        traced_model = torch.jit.trace(model, (encoded_input['input_ids'], encoded_input['attention_mask']))
    torch.jit.save(traced_model, torchscript)

    # Store to RedisAI
    con = Client(host=os.getenv('REDIS_HOST'), port=os.getenv('REDIS_PORT'))
    with open(torchscript, 'rb') as f:
        model = f.read()
    response = con.modelstore("model", 'TORCH', 'CPU', model, tag='v1.0.0')
except Exception:
    exit(1)
if response != 'OK':
    exit(1)
