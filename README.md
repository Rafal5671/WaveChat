# WaveChat

> WaveChat is a real-time web messenger built on a microservices architecture. It enables live conversations, file sharing, and browser notifications. Backend powered by Django and FastAPI, frontend built with Vue 3.

---

## Build Status

![Platform](https://img.shields.io/badge/platform-Web%20App-blue)
![Frontend](https://img.shields.io/badge/frontend-Vue%203-42b883)
![Backend](https://img.shields.io/badge/backend-Django-092e20)
![Database](https://img.shields.io/badge/database-PostgreSQL-336791)
![Auth](https://img.shields.io/badge/authentication-JWT-green)
![WebSocket](https://img.shields.io/badge/realtime-WebSocket-purple)
![Mail](https://img.shields.io/badge/mail-Mailpit-orange)
![Containerized](https://img.shields.io/badge/docker-enabled-2496ed)
![Language](https://img.shields.io/badge/language-Python%20%2F%20TypeScript-yellow)
![Tests](https://img.shields.io/badge/tests-pytest-blue)

---

## Description

WaveChat is a full-stack real-time messaging application similar to WhatsApp or Messenger.
It is built with a microservices architecture — each concern is handled by an independent service
communicating via Redis Pub/Sub and REST APIs.

Users can register with email OTP verification,
send text messages and media files in real time via WebSocket, and receive browser
notifications via Server-Sent Events when they are not actively in a conversation.

---

## Features

- Email registration with OTP verification via Mailpit
- JWT authentication with refresh token rotation
- Brute-force login protection via Redis
- Real-time messaging via WebSocket (Django Channels)
- Typing indicators
- Image, video, audio and file uploads via MinIO (S3-compatible)
- Browser push notifications via SSE when offline
- User profiles with avatars and online status
- Dockerized full-stack environment with a single command startup

---

## Tech Stack

- **Frontend:** Vue 3, TypeScript, Pinia, Vue Router, Tailwind CSS v4, Axios
- **Auth Service:** Python, Django, Django REST Framework, SimpleJWT
- **User Service:** Python, Django, Django REST Framework
- **Chat Service:** Python, Django, Django Channels, Daphne, WebSocket
- **Media Service:** Python, FastAPI, Pillow, boto3, MinIO
- **Notification Service:** Python, FastAPI, Celery, Redis Pub/Sub, SSE
- **Database:** PostgreSQL (separate instance per service)
- **Cache / Broker:** Redis
- **Storage:** MinIO (S3-compatible)
- **Email:** Mailpit (development)
- **Testing:** pytest, pytest-django, pytest-mock, pytest-asyncio
- **Containerization:** Docker, Docker Compose

---

## Project Structure

```
wavechat/
├── docker-compose.yml
├── docker/
│   └── nginx.conf                  # Reverse proxy config
├── frontend/                       # Vue 3 SPA
│   ├── Dockerfile
│   ├── nginx.conf
│   └── src/
│       ├── types/                  # TypeScript interfaces
│       ├── services/               # HTTP clients (axios)
│       ├── stores/                 # Pinia state management
│       ├── composables/            # useWebSocket, useNotifications
│       ├── components/
│       │   └── chat/               # ConversationList, MessageBubble...
│       └── views/                  # Login, Register, Chat, Profile
└── services/
    ├── auth_service/               # Django — JWT, OTP, registration
    │   ├── Dockerfile
    │   ├── accounts/
    │   └── tests/
    ├── user_service/               # Django — profiles, contacts
    │   ├── Dockerfile
    │   ├── profiles/
    │   └── tests/
    ├── chat_service/               # Django Channels — WebSocket, messages
    │   ├── Dockerfile
    │   ├── chat/
    │   └── tests/
    ├── media_service/              # FastAPI — file uploads, thumbnails
    │   ├── Dockerfile
    │   └── tests/
    └── notification_service/       # FastAPI + Celery — SSE, push
        ├── Dockerfile
        └── tests/
```

---

## Architecture

```
┌──────────────┐    HTTP / WS     ┌─────────────────────────────────┐
│   Vue 3      │ ───────────────► │           Nginx                 │
│  Frontend    │                  │        (port 80)                │
└──────────────┘                  └─────────────────────────────────┘
                                    │        │        │        │
                              /api/auth/ /api/users/ /ws/  /api/chat/
                                    │        │        │        │
                              ┌─────┘   ┌───┘   ┌───┘   ┌────┘
                              ▼         ▼       ▼        ▼
                         ┌────────┐ ┌──────┐ ┌──────┐ ┌──────┐
                         │  Auth  │ │ User │ │ Chat │ │Media │
                         │Service │ │  Svc │ │  Svc │ │ Svc  │
                         └────────┘ └──────┘ └──────┘ └──────┘
                              │         │       │
                              └────┬────┘       │ Redis Pub/Sub
                                   │            ▼
                               PostgreSQL  ┌──────────────┐
                              (per service)│ Notification │
                                           │   Service    │
                                           │ Celery + SSE │
                                           └──────────────┘
                                                  │
                                             ┌────────┐
                                             │MinIO   │
                                             │:9000   │
                                             └────────┘
```

---

## Getting Started

### Prerequisites

- Docker + Docker Desktop
- Git

### 1. Clone the repository

```bash
git clone https://github.com/Rafal5671/WaveChat.git
cd WaveChat
```

### 2. Create `.env` file

```bash
cp .env.example .env
```

All default values in `.env.example` work out of the box — no changes needed for local development.

### 3. Run the full stack

```bash
docker compose up --build
```

### 4. Open in browser

| Service     | URL                        |
|-------------|----------------------------|
| App         | http://localhost           |
| Mailpit     | http://localhost:8025      |
| MinIO       | http://localhost:9001      |

---

## Message Flow

```
1. User sends message via WebSocket
2. chat_service saves to PostgreSQL
3. chat_service broadcasts to all participants via Redis Channel Layer
4. chat_service publishes event to Redis Pub/Sub
5. notification_service listener receives event
6. Celery task checks who is offline
7. SSE stream delivers browser notification to offline participants
```

---

## API Overview

### Auth Service (`/api/auth/`)

| Method | Endpoint               | Auth     | Description                        |
|--------|------------------------|----------|------------------------------------|
| POST   | /register/             | Public   | Register — sends OTP to email      |
| POST   | /verify-email/         | Public   | Verify OTP and complete signup     |
| POST   | /login/                | Public   | Login and get JWT tokens           |
| POST   | /logout/               | Required | Blacklist refresh token            |
| POST   | /token/refresh/        | Public   | Refresh access token               |
| GET    | /me/                   | Required | Get current user info              |
| GET    | /validate/             | Required | Validate token (internal)          |

### User Service (`/api/users/`)

| Method | Endpoint                   | Auth     | Description              |
|--------|----------------------------|----------|--------------------------|
| POST   | /profile/create/           | Required | Create profile           |
| GET    | /profile/                  | Required | Get own profile          |
| PATCH  | /profile/                  | Required | Update own profile       |
| GET    | /profile/{id}/             | Required | Get public profile       |
| GET    | /profile/search/?q=        | Required | Search users             |
| GET    | /contacts/                 | Required | List contacts            |
| POST   | /contacts/                 | Required | Add contact              |
| DELETE | /contacts/{id}/            | Required | Remove contact           |
| POST   | /contacts/block/{id}/      | Required | Block user               |

### Chat Service (`/api/chat/`)

| Method | Endpoint                              | Auth     | Description                   |
|--------|---------------------------------------|----------|-------------------------------|
| GET    | /conversations/                       | Required | List conversations            |
| POST   | /conversations/                       | Required | Create conversation           |
| GET    | /conversations/{id}/                  | Required | Get conversation              |
| GET    | /conversations/{id}/messages/         | Required | List messages (paginated)     |
| PATCH  | /messages/{id}/                       | Required | Edit message                  |
| DELETE | /messages/{id}/                       | Required | Soft-delete message           |

### WebSocket (`/ws/chat/{conversation_id}/?token=<jwt>`)

**Client → Server:**
```json
{ "type": "message", "content": "Hello!", "message_type": "text" }
{ "type": "typing", "is_typing": true }
{ "type": "read", "message_id": "<uuid>" }
```

**Server → Client:**
```json
{ "type": "history", "messages": [...] }
{ "type": "message", "id": "...", "content": "...", "sender_id": "..." }
{ "type": "typing", "user_id": "...", "is_typing": true }
{ "type": "read_receipt", "message_id": "...", "reader_id": "...", "read_at": "..." }
```

---

## Running Tests

```bash
# Auth service
cd services/auth_service
pytest tests/ -v

# User service
cd services/user_service
pytest tests/ -v

# Chat service
cd services/chat_service
pytest tests/ -v

# Media service
cd services/media_service
pytest tests/ -v

# Notification service
cd services/notification_service
pytest tests/ -v
```

---

## Environment Variables

Copy `.env.example` to `.env` — all values work out of the box for local development.

| Variable                | Default                    | Description                        |
|-------------------------|----------------------------|------------------------------------|
| `SECRET_KEY`            | (provided in example)      | Django secret key                  |
| `AUTH_POSTGRES_PASSWORD`| `auth_pass`                | Auth database password             |
| `USER_POSTGRES_PASSWORD`| `user_pass`                | User database password             |
| `CHAT_POSTGRES_PASSWORD`| `chat_pass`                | Chat database password             |
| `MINIO_ROOT_USER`       | `minioadmin`               | MinIO access key                   |
| `MINIO_ROOT_PASSWORD`   | `minioadmin`               | MinIO secret key                   |
| `EMAIL_HOST`            | `mailpit`                  | SMTP host (Mailpit in dev)         |
| `EMAIL_PORT`            | `1025`                     | SMTP port                          |

---

## Example Screenshots
<img width="1870" height="992" alt="Screenshot 2026-05-14 at 13-17-07 Vite App" src="https://github.com/user-attachments/assets/121ad413-cb89-4bd1-873d-ef6d52748dd3" />
<img width="1870" height="992" alt="Screenshot 2026-05-14 at 13-17-26 Vite App" src="https://github.com/user-attachments/assets/7926738d-0ec3-4ab3-956d-a8474d3b9c53" />
<img width="1870" height="992" alt="Screenshot 2026-05-14 at 13-17-34 Vite App" src="https://github.com/user-attachments/assets/994c7d4b-2b31-449d-88ed-d2fa68ac1467" />
<img width="1870" height="992" alt="Screenshot 2026-05-14 at 13-17-39 Vite App" src="https://github.com/user-attachments/assets/c4c5ae3d-e72c-4b15-88a1-88167d356ee8" />
<img width="1870" height="992" alt="Screenshot 2026-05-14 at 13-17-53 Vite App" src="https://github.com/user-attachments/assets/79168be0-5550-4ebb-976b-e6c6d9354ce2" />
