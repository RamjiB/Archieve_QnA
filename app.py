import streamlit as st
from archieve_qa import PdfQA
from pathlib import Path
from tempfile import NamedTemporaryFile,TemporaryDirectory
import time
import shutil
from constants import *
import os



# Streamlit app code
st.set_page_config(
    page_title='Q&A Bot for Archives',
    page_icon='🔖',
    layout='wide',
    initial_sidebar_state='auto',
)


if "pdf_qa_model" not in st.session_state:
    st.session_state["pdf_qa_model"]:PdfQA = PdfQA() ## Intialisation

## To cache resource across multiple session 
@st.cache_resource
def load_llm(llm,load_in_8bit):

    if llm == LLM_OPENAI_GPT35:
        pass
    elif llm == LLM_FLAN_T5_SMALL:
        return PdfQA.create_flan_t5_small(load_in_8bit)
    elif llm == LLM_FLAN_T5_BASE:
        return PdfQA.create_flan_t5_base(load_in_8bit)
    elif llm == LLM_FLAN_T5_LARGE:
        return PdfQA.create_flan_t5_large(load_in_8bit)
    elif llm == LLM_FASTCHAT_T5_XL:
        return PdfQA.create_fastchat_t5_xl(load_in_8bit)
    elif llm == LLM_FALCON_SMALL:
        return PdfQA.create_falcon_instruct_small(load_in_8bit)
    else:
        raise ValueError("Invalid LLM setting")

## To cache resource across multiple session
@st.cache_resource
def load_emb(emb):
    if emb == EMB_INSTRUCTOR_XL:
        return PdfQA.create_instructor_xl()
    elif emb == EMB_SBERT_MPNET_BASE:
        return PdfQA.create_sbert_mpnet()
    elif emb == EMB_OPENAI_ADA:
        pass
    else:
        raise ValueError("Invalid embedding setting")



st.title("PDF Q&A (Self hosted LLMs)")

with st.sidebar:
    emb = st.radio("**Select Embedding Model**", [EMB_INSTRUCTOR_XL, EMB_SBERT_MPNET_BASE, EMB_OPENAI_ADA],index=1)
    llm = st.radio("**Select LLM Model**", [LLM_OPENAI_GPT35, LLM_FLAN_T5_SMALL, LLM_FLAN_T5_BASE, LLM_FLAN_T5_LARGE, LLM_FASTCHAT_T5_XL, LLM_FALCON_SMALL],index=1)
    load_in_8bit = st.radio("**Load 8 bit**", [True, False],index=1)
    current_dirtory = os.listdir(".")
    directories = [item for item in current_dirtory if os.path.isdir(os.path.join(".", item))]
    pdf_files_folder_path = st.selectbox("**Select Folder**", directories)

    
    if st.button("Submit") and pdf_files_folder_path is not None:
        with st.spinner(text="Generating Embeddings.."):
            with TemporaryDirectory() as tmp_dir_path:
                if (llm == LLM_OPENAI_GPT35 and OPENAI_API_KEY is None) or (emb == EMB_OPENAI_ADA and OPENAI_API_KEY is None):
                    st.sidebar.success("Update your OpenAI Key and Restart")
                else:
                    shutil.rmtree(tmp_dir_path, ignore_errors=True)
                    shutil.copytree(pdf_files_folder_path, tmp_dir_path)
                    st.session_state["pdf_qa_model"].config = {
                        "dir_path": str(tmp_dir_path),
                        "embedding": emb,
                        "llm": llm,
                        "load_in_8bit": load_in_8bit
                    }
                    try:
                        st.session_state["pdf_qa_model"].embedding = load_emb(emb)
                        st.session_state["pdf_qa_model"].llm = load_llm(llm,load_in_8bit)        
                        st.session_state["pdf_qa_model"].init_embeddings()
                        st.session_state["pdf_qa_model"].init_models()
                        st.session_state["pdf_qa_model"].vector_db_pdf()
                        st.sidebar.success("Embeddings successfully Created and Store in VectorDB (Chroma)")
                    except Exception as e:
                        st.sidebar.success(f"Error: {e}")

question = st.text_input('Ask a question')

if st.button("Answer"):
    try:
        st.session_state["pdf_qa_model"].retreival_qa_chain()
        answer = st.session_state["pdf_qa_model"].answer_query(question)
        st.write(f"{answer}")
    except Exception as e:
        st.error(f"Error answering the question: {str(e)}")