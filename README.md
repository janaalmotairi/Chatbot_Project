# HR Assistant Chatbot 🤖

An intelligent HR Chatbot designed to assist with Human Resources queries using **Retrieval-Augmented Generation (RAG)** technology. The application allows users to interact with HR data using either a lightweight local model or a powerful cloud-based model.

---

## 🌟 Features

- **Hybrid Model Support:**
  - 🏠 **Local Mode:** Runs completely offline using `Qwen 1.5B` (No Internet required).
  - ☁️ **Cloud Mode:** Connects to `Qwen 72B` via Hugging Face API for advanced reasoning and high accuracy.
- **RAG Technology:** Retrieves relevant information from company documents (CSV) to provide answers.
- **Chat History:** Automatically saves conversations to a local file and allows viewing/clearing history directly from the sidebar.
- **User-Friendly Interface:** Built with **Streamlit** for a smooth and interactive experience.

---

## 🛠️ Tech Stack

- **Language:** Python 
- **Framework:** Streamlit
- **AI Models:** Qwen (1.5B & 72B)
- **Libraries:**
  - `transformers` & `torch` (for local inference)
  - `huggingface_hub` (for cloud API)
  - `langchain` (for RAG implementation)

---

## 🚀 Installation & Setup

### 1. Clone the Repository
    git clone [https://github.com/janaalmotairi/ch.git](https://github.com/janaalmotairi/ch.git)
    cd ch

### 2. Install dependencies
    pip install streamlit torch transformers huggingface_hub langchain 

### 3. Setup the local model
**Note:** The local model files are large and are not included in this repository due to GitHub limits.
Download the Qwen 1.5B model from Hugging Face.
Place the model files inside a folder named `local_qwen_model` in the root directory.

### 4.Setup Cloud API (Optional)
To use the Cloud Qwen (72B) model:
1. Open `app.py`.
2. Locate the `SECURE_API_TOKEN` variable.
3. Paste your Hugging Face Access Token.

## ▶️ Usage
Run the application using Streamlit:
    streamlit run app.py

1. **Select Model:** Choose between "Local Qwen" or "Cloud Qwen" from the sidebar.
2. **Ask Questions:** Type your HR-related query in the chat input.
3. **View History:** Check past conversations in the "Chat History" section in the sidebar.

## 📂 Project Structure

* `app.py`: The main application script.
* `RAG.py`: Contains the logic for the RAG system.
* `chat_history.txt`: Stores the chat logs.
* `local_qwen_model/`: Folder containing the offline model.
* `faiss_index_hr/`: Folder for the vector database (FAISS).
* `Test_qwen.py`: Script for testing the model.
* `WA_Fn-UseC_-HR-Employee-Attrition.csv`: The HR dataset file.
* `.gitignore`: Specifies files to ignore in Git.

## 📸 Screenshots
### 1. User Interface
The application features a clean and user-friendly interface powered by **Streamlit**. The sidebar allows easy access to settings and chat history.
<img width="1917" height="1002" alt="Screenshot 2026-02-01 114755" src="https://github.com/user-attachments/assets/37655304-e735-4e04-86d4-67fb0ba40e95" />

### 2. Model Selection
Users can easily switch between models using the dropdown menu:
* **Local Qwen 1.5B:** For offline usage.
* **Cloud Qwen 72B:** For advanced reasoning using the Hugging Face API.
<img width="392" height="318" alt="Screenshot 2026-02-01 114810" src="https://github.com/user-attachments/assets/011d9ae1-07fb-4613-a185-c0814b9e690b" />

### 3. Chat History
The chatbot automatically saves your conversations. You can:
* **View History:** Expand the list to read past queries and answers.
* **Clear History:** Delete all saved chats with a single click to start fresh.
<img width="379" height="287" alt="Screenshot 2026-02-01 114845" src="https://github.com/user-attachments/assets/dd58fdf4-6e4d-434c-a666-9f0970ce3d8e" />
<img width="210" height="300" alt="Screenshot 2026-02-01 114836" src="https://github.com/user-attachments/assets/0788281a-8c3d-4462-942e-cee7c685b890" />


## 👤 Author
Developed by **Jana**👩‍💻
