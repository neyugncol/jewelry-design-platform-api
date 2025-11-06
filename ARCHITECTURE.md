# Architecture Documentation

## Overview

The PNJ Jewelry AI Designer API is built using a layered architecture pattern with clear separation of concerns. This document explains the architectural decisions and component interactions.

## Architecture Layers

```
┌─────────────────────────────────────────────┐
│           API Layer (FastAPI)               │
│  - Route handlers                           │
│  - Request/Response validation              │
│  - Error handling                           │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│         Service Layer (Business Logic)      │
│  - GeminiService: AI interactions           │
│  - ConversationService: Conversation mgmt   │
│  - ImageService: Image generation           │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│      Data Layer (SQLAlchemy ORM)            │
│  - Models: Conversation, Message, Image     │
│  - Database operations                      │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│         Database (SQLite)                   │
│  - Persistent storage                       │
└─────────────────────────────────────────────┘

External Services:
┌─────────────────────────────────────────────┐
│      Google Gemini API                      │
│  - Gemini 2.0 Flash (Chat + Tools)          │
│  - Gemini 2.5 Flash Image (Generation)      │
└─────────────────────────────────────────────┘
```

## Component Details

### 1. API Layer (`app/api/`)

**Purpose**: Handle HTTP requests and responses

**Components**:
- `chat.py`: Chat endpoints with AI assistant
- `conversations.py`: Conversation CRUD operations
- `images.py`: Image generation endpoints

**Responsibilities**:
- Request validation using Pydantic schemas
- Dependency injection (database sessions)
- HTTP status code management
- Error handling and formatting

### 2. Service Layer (`app/services/`)

**Purpose**: Business logic and external service integration

**Components**:

#### GeminiService
- Manages Gemini API client
- Implements function calling for image generation
- Handles chat conversations with context
- Processes tool calls and responses

#### ConversationService
- Creates and retrieves conversations
- Manages messages within conversations
- Handles conversation history

#### ImageService
- Orchestrates image generation
- Saves images to filesystem
- Creates database records for generated images

### 3. Data Layer (`app/models/`)

**Purpose**: Data persistence and ORM

**Models**:

#### Conversation
```python
- id: Primary key
- user_id: User identifier (for future auth)
- title: Conversation title
- description: Optional description
- created_at, updated_at: Timestamps
- Relationships: messages, generated_images
```

#### Message
```python
- id: Primary key
- conversation_id: Foreign key
- role: 'user' | 'assistant' | 'system'
- content: Message text
- images: JSON list of image URLs
- metadata: JSON for tool calls, etc.
- created_at: Timestamp
```

#### GeneratedImage
```python
- id: Primary key
- conversation_id: Foreign key
- message_id: Optional foreign key
- image_type: '2d' | '3d'
- prompt: Generation prompt
- image_url: Base64 data URL
- image_path: Local file path
- properties: JSON jewelry properties
- created_at: Timestamp
```

### 4. Schema Layer (`app/schemas/`)

**Purpose**: Request/response validation and documentation

**Components**:
- `conversation.py`: Conversation schemas
- `message.py`: Message and chat schemas
- `image.py`: Image generation schemas

Uses Pydantic for:
- Type validation
- Automatic OpenAPI documentation
- Serialization/deserialization

## Data Flow

### Chat Request Flow

```
1. Client → POST /api/v1/chat
   {
     "conversation_id": 1,
     "message": "Show me a ring design"
   }

2. API Layer → Validate request
   - Check conversation exists
   - Validate message format

3. Service Layer → ConversationService
   - Save user message to database
   - Retrieve conversation history

4. Service Layer → GeminiService
   - Send messages to Gemini 2.0 Flash
   - Include tool definitions for image generation

5. Gemini API → Response with tool call
   {
     "content": "I'll create some designs...",
     "tool_calls": [{
       "name": "generate_jewelry_design",
       "arguments": {...}
     }]
   }

6. Service Layer → ImageService
   - Execute tool call
   - Generate images via Gemini 2.5 Flash Image
   - Save images to filesystem and database

7. Service Layer → ConversationService
   - Save assistant message with images

8. API Layer → Return response
   {
     "user_message": {...},
     "assistant_message": {...},
     "generated_images": [...]
   }
```

### Direct Image Generation Flow

```
1. Client → POST /api/v1/generate/2d
   {
     "prompt": "...",
     "properties": {...}
   }

2. API Layer → Validate request

3. Service Layer → ImageService
   - Call GeminiService.generate_image()
   - Save to filesystem
   - Create database records

4. API Layer → Return response
   {
     "success": true,
     "images": [...]
   }
```

## Design Patterns

### 1. Dependency Injection
- Database sessions injected via FastAPI's `Depends()`
- Enables easy testing and mocking

### 2. Service Layer Pattern
- Business logic separated from API handlers
- Reusable across different endpoints
- Easier to test and maintain

### 3. Repository Pattern (Implicit)
- ConversationService acts as repository
- Abstracts database operations
- Could be further refined for production

### 4. Factory Pattern
- GeminiService creates API clients
- Centralizes configuration

## Configuration Management

Uses `pydantic-settings` for configuration:

```python
class Settings(BaseSettings):
    gemini_api_key: str
    database_url: str
    chat_model: str = "gemini-2.0-flash-exp"
    image_model: str = "gemini-2.5-flash-image"

    class Config:
        env_file = ".env"
```

Benefits:
- Type-safe configuration
- Environment variable support
- Validation on startup

## Error Handling

### Approach
1. **Service Layer**: Raises exceptions with descriptive messages
2. **API Layer**: Catches exceptions and returns HTTP errors
3. **Client**: Receives structured error responses

### Example
```python
try:
    response = await gemini_service.chat(...)
except Exception as e:
    raise HTTPException(
        status_code=500,
        detail=f"AI service error: {str(e)}"
    )
```

## Database Design

### Schema Relationships

```
Conversation (1) ←→ (N) Message
Conversation (1) ←→ (N) GeneratedImage
Message (1) ←→ (N) GeneratedImage
```

### Indexes
- `conversation_id` on messages and images
- `user_id` on conversations (for future multi-tenancy)

### Cascading Deletes
- Deleting conversation removes all messages and images
- Maintains referential integrity

## Security Considerations (Future)

### Current State (PoC)
- No authentication
- No rate limiting
- No input sanitization beyond Pydantic

### Production Requirements
1. **Authentication**: JWT tokens, API keys
2. **Authorization**: Role-based access control
3. **Rate Limiting**: Per-user/IP limits
4. **Input Validation**: Enhanced sanitization
5. **CORS**: Restrict origins
6. **HTTPS**: TLS encryption
7. **Secrets**: External secrets management

## Scalability Considerations

### Current Limitations
- SQLite: Single writer, limited concurrency
- Local filesystem: Not distributed
- Synchronous image generation

### Production Improvements
1. **Database**: PostgreSQL with connection pooling
2. **Storage**: S3/GCS for images
3. **Async Tasks**: Celery/RQ for long operations
4. **Caching**: Redis for API responses
5. **Load Balancing**: Multiple API instances
6. **CDN**: Image delivery
7. **Monitoring**: Prometheus, Grafana

## API Versioning

Current: `/api/v1/...`

Strategy:
- URL-based versioning
- Maintain backward compatibility
- Deprecation notices in responses

## Testing Strategy

### Unit Tests
- Service layer logic
- Model validation
- Schema validation

### Integration Tests
- API endpoint testing
- Database operations
- Mock external services

### End-to-End Tests
- Full user workflows
- Use test database
- Mock Gemini API

## Deployment

### Docker
- Multi-stage builds for optimization
- Volume mounts for persistence
- Environment-based configuration

### Development
```bash
docker-compose up
```

### Production (Future)
- Kubernetes for orchestration
- Helm charts for deployment
- CI/CD pipeline (GitHub Actions)

## Monitoring & Observability

### Current
- FastAPI automatic OpenAPI docs
- Basic error logging

### Production Needs
1. **Logging**: Structured JSON logs
2. **Metrics**: Request rates, latency
3. **Tracing**: Distributed tracing
4. **Alerting**: Error rate alerts
5. **Health Checks**: Readiness/liveness probes

## Performance Optimization

### Current Performance
- In-memory SQLite operations: Fast
- Gemini API calls: 1-3s latency
- Image generation: 3-10s per image

### Optimization Strategies
1. **Caching**: Cache AI responses
2. **Async Processing**: Queue image generation
3. **CDN**: Cache static responses
4. **Database Indexes**: Optimize queries
5. **Connection Pooling**: Reuse connections

## Technology Choices

### Why FastAPI?
- Modern, fast, async support
- Automatic OpenAPI documentation
- Type hints and validation
- Great developer experience

### Why SQLite (PoC)?
- Zero configuration
- File-based
- Good for development
- Easy to migrate to PostgreSQL

### Why SQLAlchemy?
- ORM abstraction
- Database agnostic
- Relationships and migrations
- Production-ready

### Why Pydantic?
- Type validation
- JSON serialization
- OpenAPI integration
- Clear error messages

## Future Architecture Evolution

### Phase 1: PoC (Current)
- Monolithic API
- SQLite
- Local storage

### Phase 2: Production MVP
- PostgreSQL
- Cloud storage
- Basic auth
- Rate limiting

### Phase 3: Scale
- Microservices (optional)
- Message queue
- Caching layer
- Multiple regions

### Phase 4: Enterprise
- Multi-tenancy
- Advanced analytics
- ML pipeline
- Real-time collaboration

## Conclusion

This architecture provides:
- Clear separation of concerns
- Easy to understand and modify
- Ready for iterative improvement
- Foundation for production scaling

The PoC design prioritizes simplicity and speed of development while maintaining good practices that will facilitate future enhancements.
