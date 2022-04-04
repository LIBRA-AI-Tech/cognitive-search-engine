import torch
from sentence_transformers import SentenceTransformer
from sentence_transformers.LoggingHandler import install_logger
from typing import List
import numpy as np
from .settings import settings

class ModelInference:
    def __init__(self, model_name: str, quantize: bool=False, threads: int=1) -> None:
        # Set the number of threads to be 1 for better parallelisation
        torch.set_num_threads(threads)
        torch.set_grad_enabled(False)
        
        model = SentenceTransformer(model_name)
        
        if quantize:
            # fbgemm is the default quantization engine and is the desired one in non-mobile builds
            # if fbgemm is not available then engine is set to none
            if torch.backends.quantized.engine == 'none' and 'qnnpack' in torch.backends.quantized.supported_engines:
                # quantization issue https://github.com/pytorch/pytorch/issues/29327#issuecomment-552774174
                torch.backends.quantized.engine = 'qnnpack'
                model = torch.quantization.quantize_dynamic(model, {torch.nn.Linear}, dtype=torch.qint8)
        
        self.model = model

    def encode_text(self, input_text: str) -> List[np.float32]:
        with torch.no_grad():
            embeddings = self.model.encode(input_text).tolist()
        return embeddings

def predict(text: str) -> ModelInference.encode_text:
    model = ModelInference(settings.model_path, settings.quantize_model)
    return model.encode_text(text)

def get_dims() -> int:
    return len(predict('test'))
