# GEOSS Search service

## Dependecies

* Python 3.8
* ElasticSearch 8.1

## Installation

In the root directory execute:
```
python setup.py install
```
**or**, using pip:
```
pip install .
```
For a production deployment, before installing the module, run
```
pip install -r requirements.txt -r requirements-production.txt
```
to install the specific versions of Python libraries that have been tested.

Documents can be bulky inserted into ElasticSearch using:
```
geoss_search init <path-to-documents-json> --with-schema <path-to-schema-yaml>
```
where ```<path-to-documents-json>``` is the full path to the *json* file containing the documents to be inserted, and ```<path-to-schema-yaml>``` is the full path of the *YAML* file describing the schema of documents.

Start the service running:
```
geoss_search run
```

For more information about the available *cli* commands, run
```
geoss_search <command> --help
```
with command one of ```run```, ```init```.

## Environment

The following *environment variables* are available:

* **APP_NAME**: The service name [default: geoss_search]
* **FASTAPI_ENV**: FastAPI environment [default: development]
* **ELASTIC_NODE**<sup>*</sup>: URL of the *ElasticSearch* node.
* **CA_CERTS**<sup>*</sup>: Path to CA certificate files.
* **ELASTIC_PASSWORD**<sup>*</sup>: ElasticSearch password.
* **MODEL_PATH**<sup>*</sup>: Path to Torch model.
* **QUANTIZE_MODEL**: Whether to quantize model [default: False].
* **ELASTIC_INDEX**<sup>*</sup>: Name of *ElasticSearch Index* to use.
* **RESULTS_PER_PAGE**: Number of results per page in query responses [default: 5].

<sup>*</sup> Required.

## Build and run as a container

1. Copy `.env.example` to `.env` and configure.
2. Adjust `docker-compose.yml` to your needs (e.g. specify volume source locations, etc.).
3. Build with:
```
docker-compose build
```
4. Start application:
```
docker-compose up
```

This procedure will result in a container of the service, and a 3-node cluster of *ElasticSearch*.

## Run tests
Run *nosetests* using an ephemeral container with:

    docker-compose -f docker-compose-testing.yml -p eiffel_geoss_search-testing run --rm --user "$(id -u):$(id -g)" nosetests -v

When finished, remove also the *ElasticSearch* container created for testing purposes with

    docker container rm -f elasticsearch-single > /dev/null


## Dev deployment
```sh
docker-compose -f docker-compose-dev.yaml up
```

## Inference API
uvicorn model_inference:app --workers 1

https://www.comet.ml/site/how-to-10x-throughput-when-serving-hugging-face-models-without-a-gpu/

https://towardsdatascience.com/speeding-up-bert-search-in-elasticsearch-750f1f34f455
https://huggingface.co/climatebert/distilroberta-base-climate-f
https://towardsdatascience.com/elasticsearch-meets-bert-building-search-engine-with-elasticsearch-and-bert-9e74bf5b4cf2
https://www.elastic.co/guide/en/machine-learning/master/ml-nlp-deploy-models.html#ml-nlp-select-model