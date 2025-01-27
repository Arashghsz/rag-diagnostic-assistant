# RAG Diagnostic Assistant

An AI-powered healthcare assistant that combines Retrieval-Augmented Generation (RAG) with multi-agent collaboration to deliver personalized diagnostic support and medical advice.

## Features

- 🤖 Multi-agent system with specialized roles (Diagnostic, Recommendation, and Explanation agents)
- 📚 Knowledge base integration with semantic search capabilities
- 🔄 RAG-enhanced responses for accurate medical information retrieval
- 🎯 Interactive diagnostic sessions with follow-up questioning
- 👤 Patient profile management
- 💾 Caching system for efficient embedding storage
- ⚡ Streamlit-based user interface

## Prerequisites

- Python 3.9+
- OpenAI API key
- Streamlit
- Internet connection for API access

## Quick Start

### Option 1: Running with Docker

1. Clone the repository:
   ```bash
   git clone git@github.com:Arashghsz/rag-diagnostic-assistant.git
   cd rag-diagnostic-assistant
   ```

2. Ensure your OpenAI API key is set in the .env file

3. Make sure Docker Desktop is installed and running:
   - Install Docker Desktop from https://www.docker.com/products/docker-desktop
   - Start Docker Desktop
   - Wait until Docker Desktop is running (check the whale icon in system tray)

4. Build and run with Docker Compose:
   ```bash
   docker-compose up --build
   ```

5. Access the application at http://localhost:8501

Troubleshooting:
- If you get a "system cannot find the file specified" error, make sure Docker Desktop is running
- If Docker Desktop isn't starting, try restarting your computer
- For Windows users, ensure WSL 2 is installed and enabled

### Option 2: Running Locally(Recommended)

1. Clone the repository:
   ```bash
   git clone git@github.com:Arashghsz/rag-diagnostic-assistant.git
   ```

2. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```

3. Ensure your OpenAI API key is set in the .env file

4. Run the application:
   ```bash
   cd agent
   streamlit run main.py
   ```

5. Access the application at http://localhost:8501

## Workflow Diagram

### Workflow Description

The RAG Diagnostic Assistant is structured into several key phases, ensuring a seamless and effective diagnostic experience. Below is an overview of the workflow:

---

### Initial Setup Phase

- **Load configuration and environment variables**
- **Initialize knowledge base** with medical dataset
- **Setup OpenAI API connection**
- **Initialize session state** for Streamlit
- **Patient Profile Collection**

---

### Collect Basic Patient Information:

- Age  
- Gender  
- Known medical conditions  
- Current medications  
- **Store profile in session state**  
- **Make profile available to all agents**

---

### Diagnostic Phase (DiagnosticAgent)

#### Initial Symptom Collection:

- Iterative questioning process:
  - **Process patient input**
  - **Search knowledge base** for relevant information
  - **Generate appropriate follow-up questions**
  - Continue until **sufficient information** gathered  
- **Mark with [DIAGNOSIS_COMPLETE]** when ready

---

### Recommendation Phase (RecommendationAgent)

- Triggered after diagnosis completion  
- **Reviews entire conversation history**  
- **Analyzes**: 
  - Patient profile  
  - Reported symptoms  
  - Diagnostic conclusions  
- **Generates**: 
  - Immediate relief suggestions  
  - Long-term management strategies  
- **Marks completion with [RECOMMENDATIONS_COMPLETE]**

---

### Explanation Phase (ExplanationAgent)

- **Final phase of consultation**  
- **Reviews entire case**: 
  - Initial symptoms  
  - Diagnostic process  
  - Recommended treatments  
- **Provides**:
  - Reasoning behind diagnosis  
  - Explanation of treatment choices  
  - Additional context for patient  
- **Marks completion with [EXPLANATION_COMPLETE]**

---

### Knowledge Base Integration

- **Continuous support** throughout the workflow  
- **Provides**:
  - Symptom matching  
  - Question suggestions  
  - Condition correlations  
- **Uses**:
  - Semantic search  
  - Embedding-based retrieval  
  - Cached responses  

---

### Session Management

- **Maintains conversation state**  
- **Handles transitions between agents**  
- **Manages user input/output**  
- **Provides error handling**  
- **Enables session reset**

### Example of RAG Diagnostic Assistant live chat software
![RAG Diagnostic Assistant Workflow](output/collecting%20user%20profile.png)
![RAG Diagnostic Assistant Workflow](output/live%20chat%20with%20diagnostic%20agent.png)
![RAG Diagnostic Assistant Workflow](output/getting%20response%20from%20RecommendationAgent.png)
![RAG Diagnostic Assistant Workflow](output/getting%20response%20from%20ExplanationAgent.png)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This tool is for educational purposes only and should not replace professional medical advice. Always consult with healthcare professionals for medical decisions.