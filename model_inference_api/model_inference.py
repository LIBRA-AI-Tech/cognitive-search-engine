from sentence_transformers import SentenceTransformer
from typing import List, Optional
import torch
from fastapi import FastAPI
import numpy as np
import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# Parse args
class ModelInference:
    def __init__(self, args):
        # Set the number of threads to be 1 for better parallelisation
        torch.set_num_threads(1)
        torch.set_grad_enabled(False)
        
        model = SentenceTransformer(args['model'])
        
        if args['quantize']:
            model = torch.quantization.quantize_dynamic(model, {torch.nn.Linear}, dtype=torch.qint8)
        
        self.model = model

    
    def encode_text(self, input_text: str) -> List[np.float32]:
        with torch.no_grad():
            embeddings = self.model.encode(input_text).tolist()

            print(embeddings)

        return embeddings


class InputText(BaseModel):
    text: Optional[str] = 'This is some sample text'

# Parameters are passed using environment variables
args = {
    'model': os.environ['MODEL_NAME'],
    'quantize': os.environ['QUANTIZE_MODEL']
}
model_class = ModelInference(args)

app = FastAPI()


@app.post('/encode')
def run_prediction(input: InputText):
    prediction = model_class.encode_text(input.text)
    return {'embedding': prediction}


@app.get('/health_check')
async def run_health_check():
    return {'status': 'Healthy'}