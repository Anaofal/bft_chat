from langchain_google_genai import GoogleGenerativeAI, ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferWindowMemory, ChatMessageHistory
from langchain.prompts import PromptTemplate
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.callbacks.manager import CallbackManager
from langchain.document_loaders.csv_loader import CSVLoader
from dotenv import load_dotenv
import os
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from langchain.vectorstores import Qdrant

# Chargement des variables d'environnement
load_dotenv()

# Utilisation du modèle d'embeddings GoogleGenerativeAI
def chunk_embedder():
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", temperature=0.5)
    return embeddings

def load_llm():
    callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])
    llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0)
    return llm

def init_chat():
    llm = load_llm()
    embeddings = chunk_embedder()

    # Connexion à Qdrant
    client = QdrantClient(
        url="https://de6620c5-c596-4a5a-afcb-d8912b199b76.europe-west3-0.gcp.cloud.qdrant.io",
        api_key="fDqAgOrkVYgSJpf9daBRbDRHLvEXS78I-4w5wNiu0aT95vJmXeochQ",)
    collection_name = "BFT_chatbot"

    # Vérifier si la collection existe déjà
    if not client.get_collections().collections or collection_name not in [c.name for c in client.get_collections().collections]:
        # Créer la collection si elle n'existe pas
        client.recreate_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE), 
        )
        # Charger et ajouter des documents initiaux si la collection n'existe pas encore
        loader = CSVLoader("faq.csv", encoding="utf-8")
        content = loader.load()

        # Diviser les documents en chunks
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=5, chunk_overlap=2)
        docs = text_splitter.split_documents(documents=content)

        # Initialiser et ajouter les documents au vectorstore
        vectorstore = Qdrant(
            client=client, 
            collection_name=collection_name, 
            embeddings=embeddings
        )
        vectorstore.add_documents(docs)
    else:
        # Charger l'existant si la collection est déjà là
        vectorstore = Qdrant(
            client=client, 
            collection_name=collection_name, 
            embeddings=embeddings
        )

    # Modèle de prompt pour l'assistant
    template = """
    Tu es un assistant virtuel pour BFT, spécialisé dans la réponse aux questions fréquemment posées par les agents de terrain, 
    les caissiers, et les gestionnaires d'agences des institutions de microfinance. Ton rôle est de fournir des réponses rapides, 
    précises et claires pour résoudre leurs problèmes. Les questions peuvent concerner des procédures internes, des problèmes techniques, 
    ou des informations sur les services BFT. Ton objectif est d'aider efficacement.

    Règles de réponse :
    1. Si la réponse se trouve dans la FAQ, copie et renvoie la réponse exacte de la FAQ sans reformulation ni modification.
    2. Utilise les informations du site officiel "https://bftgroup.co/" pour compléter ou enrichir la réponse si nécessaire.
    3. Si une question a plusieurs réponses possibles, donne toutes les options de manière exhaustive.
    4. Utilise tes capacités de Gemini Pro pour enrichir les réponses seulement et seulement quand la FAQ ou le site officiel ne couvrent pas entièrement la question.
    5. Si tu n'as pas suffisamment d'informations pour répondre précisément à la question, dis : "Je n'ai pas assez d'informations pour répondre à cette question."
    6. Si la question est basique (politesse, ton rôle, ta fonction), réponds de manière concise et adaptée.
    7. Pour toute réponse, soit concis et va directement à l'essentiel, sauf si la question demande des détails.

    Formatage des réponses :
    - Fournis des réponses structurées (liste, étapes, ou paragraphes courts) pour faciliter la lecture.
    

    context: {context}
    Question : {question}
    output
    """


    # Mémoire de conversation pour l'assistant (persistance)
    message_history = ChatMessageHistory()
    chat_memory = ConversationBufferWindowMemory(
        memory_key="chat_history",
        output_key="answer",
        chat_memory=message_history,
        k=5,
        return_messages=True
    )
    
    prompt = PromptTemplate(template=template, input_variables=["context", "question"])
    chain_type_kwargs = {"prompt": prompt}

    # Définir le retriever pour le vectorstore
    retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 20})
    
    # Chaîne de conversation pour la récupération d'informations et LLM
    conversation = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=chat_memory,
        combine_docs_chain_kwargs=chain_type_kwargs,
    )
    
    return conversation

conversation = init_chat()

# Fonction pour interagir avec le chatbot
def Talker(query: str, conversation):
    output = conversation.invoke(input=query)
    response = output.get('answer')
    return response

# Exemple d'appel de la fonction Talker
print(Talker(" Que faire si un agent  n'arrive pas à se connecter?", conversation))
