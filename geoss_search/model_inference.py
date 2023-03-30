import os
import torch
import torch.nn.functional as F
from redisai import Client
from transformers import AutoTokenizer

from sentence_transformers import SentenceTransformer
from sentence_transformers.LoggingHandler import install_logger
from typing import List, Union
import numpy as np
from .settings import settings

class ModelInferenceOld:
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

    def encode_text(self, input_text: Union[str, list]) -> List[np.float32]:
        if input_text is None:
            return []
        with torch.no_grad():
            kwargs = {"show_progress_bar": False}
            embeddings = self.model.encode(input_text, **kwargs).tolist()
        return embeddings

    def get_dims(self) -> int:
        """Get the dimensionality of the model

        Returns:
            int: Number of dimensions
        """
        return self.model.get_sentence_embedding_dimension()

class ModelInference:

    def __init__(self, model_path, redis_host='redisai', redis_port=6379) -> None:
        self._redis = Client(host=redis_host, port=redis_port)
        self._tokenizer = AutoTokenizer.from_pretrained(model_path)

    def _mean_pooling(self, token_embeddings, attention_mask):
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)

    def encode(self, sentences: Union[str, List[str]]) -> List[float]:
        encoded_input = self._tokenizer(sentences, padding=True, truncation=True, return_tensors='pt')
        dag = self._redis.dag(routing=0, readonly=True)
        dag.tensorset('input_ids', encoded_input['input_ids'].numpy())
        dag.tensorset('attention_mask', encoded_input['attention_mask'].numpy())
        dag.modelexecute("model", inputs=['input_ids', 'attention_mask'], outputs=['last_hidden_state', 'pooler_output'])
        dag.tensorget('last_hidden_state')
        dag.tensorget('pooler_output')
        _, _, _, last_hidden_state, pooler_output = dag.execute()
        del dag
        embeddings = self._mean_pooling(torch.tensor(last_hidden_state), encoded_input['attention_mask'])
        return F.normalize(embeddings, p=2, dim=1)[0].tolist()

    def get_dims(self) -> int:
        """Get the dimensionality of the model

        Returns:
            int: Number of dimensions
        """
        return 384

def predict(text: str) -> ModelInference.encode:
    """Generate the embedding of a string

    Args:
        text (str): The text which be vectorized

    Returns:
        ModelInference.encode: Resulted vector
    """
    model = ModelInference(settings.model_path, redis_host=os.getenv('REDIS_HOST', 'localhost'), redis_port=os.getenv('REDIS_PORT', 6379))
    return model.encode(text)

def get_dims() -> int:
    """Get the dimensionality of the model in use

    Returns:
        int: Number of dimensions
    """
    model = ModelInference(settings.model_path)
    return model.get_dims()
