"""
setup_models.py

Loads local Qwen and Groq client.
"""

import streamlit as st
from transformers import AutoTokenizer, AutoModelForCausalLM
from groq import Groq


@st.cache_resource
def load_local_qwen():
    """Load local Qwen model."""
    model_name = "Qwen/Qwen2.5-1.5B-Instruct"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        device_map="auto"
    )
    return model, tokenizer


@st.cache_resource
def load_groq_client(api_key: str):
    """Load Groq client."""
    return Groq(api_key=api_key)
