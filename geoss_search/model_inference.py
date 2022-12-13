import torch
from sentence_transformers import SentenceTransformer
from sentence_transformers.LoggingHandler import install_logger
from typing import List, Union
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

def predict(text: str) -> ModelInference.encode_text:
    """Generate the embedding of a string

    Args:
        text (str): The text which be vectorized

    Returns:
        ModelInference.encode_text: Resulted vector
    """
    model = ModelInference(settings.model_path, settings.quantize_model)
    return model.encode_text(text)

def get_dims() -> int:
    """Get the dimensionality of the model in use

    Returns:
        int: Number of dimensions
    """
    model = ModelInference(settings.model_path, settings.quantize_model)
    return model.get_dims()
