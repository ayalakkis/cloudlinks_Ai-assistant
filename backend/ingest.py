import os
import sys
import uuid

import pymupdf
from dotenv import load_dotenv
from openai import OpenAI
from qdrant_client.models import PointStruct
from qdrant_db import create_collection_if_needed, COLLECTION_NAME

load_dotenv()
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

EMBEDDING_MODEL = "text-embedding-3-small"

CHUNK_SIZE = 800
CHUNK_OVERLAP = 100


def read_pdf(file_path): #Defines a function called read_pdf that receives the PDF's file path
    all_text = "" #Creates an empty string where we will store all the text from the PDF
    pdf_document = pymupdf.open(file_path) #Opens the PDF using PyMuPDF and stores the opened document in pdf_document
    for page in pdf_document: #Loops through every page of the PDF
        page_text = page.get_text() #Extracts the text from the current page and stores it in page_text
        all_text = all_text + page_text + "\n" #Appends the text from the current page to all_text
    pdf_document.close()#Closes the PDF document to free up resources
    return all_text


def read_txt(file_path): #Defines a function called read_txt that receives the TXT's file path
    text_file = open(file_path, "r", encoding="utf-8") #Opens the TXT file in read mode with UTF-8 encoding and stores the opened file in text_file
    file_text = text_file.read() #Reads the entire content of the TXT file and stores it in file_text
    text_file.close() #Closes the TXT file to free up resources
    return file_text 


def split_text(text): 
    chunks = []
    start = 0
    while start < len(text): #Keeps creating chunks as long as there is still text left to read
        end = start + CHUNK_SIZE #Defines the end of the current chunk by adding CHUNK_SIZE to the start index
        chunk = text[start:end] #Extracts the substring from the text starting at the start index and ending at the end index, and stores it in chunk
        chunks.append(chunk) #Appends the current chunk to the chunks list
        start = end - CHUNK_OVERLAP #Moves the start index forward by CHUNK_SIZE minus CHUNK_OVERLAP to create overlapping chunks
    return chunks 


def create_embedding(text): #converts text into an embedding.
    response = client.embeddings.create( #Sends the text to the embedding API to generate its vector representation
        model=EMBEDDING_MODEL, #Tells the API which embedding model to use
        input=text, #Gives the model the text that should be converted into a vector
    )
    embedding = response.data[0].embedding #Takes the actual vector from the API response
    return embedding


def store_chunks(chunks, file_name): #stores all the text chunks in Qdrant
    qdrant = create_collection_if_needed() 
    points = []
    for chunk_number, chunk_text in enumerate(chunks): #Goes through every chunk and gives each chunk a number
        embedding = create_embedding(chunk_text) #Converts the current chunk into an embedding vector

        point = PointStruct(
            id=str(uuid.uuid4()), #
            vector=embedding,
            payload={
                "text": chunk_text,
                "file_name": file_name,
                "chunk_number": chunk_number,
            },
        )
        points.append(point)

    qdrant.upsert(collection_name=COLLECTION_NAME, points=points)
    print(f"Stored {len(points)} chunks from '{file_name}' in Qdrant.")

    return len(points)


def ingest_file(file_path):
    file_name = os.path.basename(file_path)

    if file_path.lower().endswith(".pdf"):
        text = read_pdf(file_path)
    elif file_path.lower().endswith(".txt"):
        text = read_txt(file_path)
    else:
        print("Only .pdf and .txt files are supported.")
        return 0

    print(f"Read {len(text)} characters from {file_name}.")

    chunks = split_text(text)
    print(f"Split into {len(chunks)} chunks.")

    chunk_count = store_chunks(chunks, file_name)
    print("Done.")
    return chunk_count


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ingest.py <path-to-pdf-or-txt-file>")
    else:
        ingest_file(sys.argv[1])
