## Dev deployment
```sh
docker-compose -f docker-compose-dev.yaml up
```

## Prod deployment 
```sh
docker-compose up
```

## Inference API
uvicorn model_inference:app --workers 1

https://www.comet.ml/site/how-to-10x-throughput-when-serving-hugging-face-models-without-a-gpu/

https://towardsdatascience.com/speeding-up-bert-search-in-elasticsearch-750f1f34f455
https://huggingface.co/climatebert/distilroberta-base-climate-f
https://towardsdatascience.com/elasticsearch-meets-bert-building-search-engine-with-elasticsearch-and-bert-9e74bf5b4cf2
https://www.elastic.co/guide/en/machine-learning/master/ml-nlp-deploy-models.html#ml-nlp-select-model