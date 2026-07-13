# AskBuddy-ai Backend

A production-oriented AI chat backend built with **FastAPI** and **Python**. This project focuses on learning how modern AI applications are designed, including streaming responses, conversation management, logging, and scalable backend architecture.

> **Status:** 🚧 Under active development

## Features

* 🤖 AI chat using LLM APIs
* ⚡ Real-time response streaming (SSE)
* 💬 Conversation management
* 📝 Automatic conversation title generation
* 📜 Persistent chat history
* 🔄 Fully asynchronous architecture (`async`/`await`)
* 📁 Production-style rotating file logging
* 🏗️ Clean project structure
* 🔌 Easy integration with different LLM providers

## Tech Stack

* Python
* FastAPI
* AsyncIO
* Server-Sent Events (SSE)
* Groq API (Current LLM Provider)
* SQLAlchemy
* PostgreSQL
* Pydantic
* Python Logging

## Project Structure

```text
app/
├── api/
├── db/
├── models/
├── schemas/
├── services/
│   ├── chat_service.py
│   ├── llm_service.py
│   └── title_service.py
├── utils/
├── core/
└── main.py
```

## Current Workflow

1. User sends a message.
2. Backend stores the user message.
3. Request is sent to the LLM.
4. AI response is streamed back token-by-token using SSE.
5. Assistant response is stored.
6. If it's a new conversation, a title is generated asynchronously without blocking the streamed response.
7. Logs are written to rotating log files for debugging and monitoring.



## Key Concepts Implemented

* Asynchronous FastAPI endpoints
* Streaming AI responses
* Conversation persistence
* Background processing
* Separation of business logic
* Production logging
* Clean service-based architecture



## Running the Project

### Clone the repository

```bash
git clone https://github.com/your-username/ai-chat-backend.git
cd ai-chat-backend
```

### Create a virtual environment

```bash
python -m venv .venv
```

Activate it:

**Windows**

```bash
.venv\Scripts\activate
```

**Linux / macOS**

```bash
source .venv/bin/activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Create a `.env`

```env
GROQ_API_KEY=your_api_key
DATABASE_URL=your_database_url
```

### Start the server

```bash
uvicorn app.main:app --reload
```



## Roadmap

* [x] AI chat integration
* [x] Streaming responses
* [x] Conversation history
* [x] Conversation title generation
* [x] Rotating file logging
* [ ] Authentication
* [ ] Rate limiting
* [ ] Conversation search
* [ ] Background workers
* [ ] Metrics & monitoring
* [ ] Redis caching
* [ ] Vector database integration
* [ ] Tool calling
* [ ] RAG support
* [ ] Multi-model support
* [ ] Docker deployment
* [ ] CI/CD pipeline



## Goals

This project is built to learn and implement the backend architecture used in production AI applications. The focus is not only on integrating an LLM, but also on designing scalable, maintainable, and production-ready backend systems.
