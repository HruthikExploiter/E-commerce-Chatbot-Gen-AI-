import pandas as pd
from pathlib import Path
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from groq import Groq
import os
from dotenv import load_dotenv


load_dotenv()

faq_path = Path(__file__).parent / "Resources/faq_data.csv"

chroma_client = chromadb.Client(Settings(
    persist_directory=None  # disables persistence
))

collection_name = 'faqs'

emb_funt = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name='sentence-transformers/all-MiniLM-L6-v2'
)

groq_client = Groq()

def data_ingestion(path):
    if collection_name not in [c.name for c in chroma_client.list_collections()]:
        print("ingesting the data into chromadb...")
        collection = chroma_client.get_or_create_collection(
            name = collection_name,
            embedding_function= emb_funt
        )

        df = pd.read_csv(path)
        doc_que = df['question'].to_list()
        doc_ans = [{'answer': ans} for ans in df["answer"].to_list()]
        ids = [f"id- {i}" for i in range(len(doc_que))]

        collection.add(
            documents = doc_que,
            metadatas = doc_ans,
            ids = ids

        )
    else:
        print(f"collection {collection_name} already exist...!")

def get_relevant_data(query):
    collection = chroma_client.get_collection(name = collection_name)
    result = collection.query(
            query_texts= [query],
        n_results= 2
        )
    return result

def faq_chain(query):
    result = get_relevant_data(query)
    context = ''.join([ r.get('answer') for r in result["metadatas"][0]])
    answer = generate_ans(query, context)
    return answer


def generate_ans(query, context):
    prompt = f''' Given the question and context below, generate the answer based on the context only.
    if you don't find the answer inside the context then say "I don't know".
    do not make things up. 
    
    Question: {query}\
    
    context: {context}
    '''
    llm = groq_client.chat.completions.create(
        messages=[
            {
                'role': 'user',
                'content': prompt
            }
        ],
        model= os.environ['GROQ_MODEL']
    )
    return llm.choices[0].message.content


if __name__=="__main__":
    data_ingestion(faq_path)
    query = 'do you take cash as a payment option ?'
    result = faq_chain(query)
    print(result)
