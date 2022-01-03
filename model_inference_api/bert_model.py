from sentence_transformers import SentenceTransformer

model = SentenceTransformer('sentence-transformers/distiluse-base-multilingual-cased-v2')


sentences = ['Dissolved trace metals concentrations obtained during R/V Hakuho-maru KH-14-3 cruise']

embeddings = model.encode(sentences)

print(embeddings)
print(embeddings.shape)

print(type(embeddings))

for sentence, embedding in zip(sentences, embeddings):
    print('Sentence:', sentence)
    print('Embedding:', embedding)
    print('\n')