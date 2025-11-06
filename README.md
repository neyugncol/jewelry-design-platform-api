# PNJ Jewelry Design Platform - API Service

AI-powered jewelry design assistant API for **PNJ Jewelry Corp** (Vietnamese Jewelry Corporation). This API service powers an interactive jewelry design platform where users can design new jewelry, edit existing products, or find jewelry that matches their preferences through conversational AI.

## Overview

The PNJ Jewelry Design Platform provides a unique collaborative design experience through two integrated frontend sections:

### 1. Artifact Section
Displays the **design interface** with:
- **Jewelry Design Properties**: Type, metal, gemstones, style, occasion, and more
- **2D Images**: High-quality jewelry design visualizations
- **3D Models**: Three-dimensional jewelry previews
- **Product Recommendations**: Curated list of matching PNJ jewelry products

The assistant can **automatically update artifacts** based on user requests or suggestions, while users can also **manually modify artifacts**, ensuring seamless collaboration between the AI assistant and the user during the design process.

### 2. Chat Section
Provides **conversational interaction** where users can:
- Ask questions about jewelry design and materials
- Send reference images to inspire designs
- Control and manipulate artifacts through natural language
- Receive intelligent suggestions and design recommendations

The assistant responds with useful information, design suggestions, and artifact updates to visualize ideas in real-time.

## Key Features

- **Collaborative Design**: Bi-directional artifact system where both AI and users can update designs
- **Conversational AI**: Chat with an AI assistant powered by Google Gemini 2.0 Flash
- **Artifact-Based Workflow**: Structured design artifacts and product recommendations
- **Image Management**: Upload and manage reference images for design inspiration
- **User Authentication & Profiles**:
  - JWT-based authentication with bcrypt password hashing
  - Secure user accounts with automatic conversation isolation
  - Rich user demographics (gender, age, marital status, customer segment, region, nationality)
  - Personalized AI recommendations based on user profile
- **Design History**: Track and retrieve all design conversations per user
- **Smart Tool Calling**: AI automatically generates designs when appropriate
- **Vietnamese Market Focus**: Optimized for PNJ's Vietnamese customer base with regional preferences

## Tech Stack

- **FastAPI**: Modern, fast web framework for building APIs
- **Pydantic**: Data validation using Python type annotations
- **SQLAlchemy**: SQL toolkit and ORM
- **SQLite**: Lightweight database (development/PoC)
- **Authentication**:
  - **python-jose**: JWT token generation and validation
  - **passlib**: Password hashing with bcrypt
- **Google Gemini AI**:
  - **Gemini 2.0 Flash**: Conversational AI with function calling
  - **Gemini 2.0 Flash** (with structured output): Jewelry design generation
- **UV**: Fast Python package installer and resolver
- **Docker & Docker Compose**: Containerization and orchestration

## Prerequisites

- **Python 3.13+** (or use Docker)
- **Docker and Docker Compose** (optional, recommended)
- **Google Gemini API key** ([Get one here](https://ai.google.dev/))

## Quick Start

### Option 1: Docker Compose (Recommended)

1. Clone the repository:
```bash
cd jewelry-design-platform-api
```

2. Create `.env` file:
```bash
cp .env.example .env
```

3. Edit `.env` and configure required variables:
```env
# Required: Get your Gemini API key from https://ai.google.dev/
GEMINI_API_KEY=your_actual_api_key_here

# Required: Generate a secure secret key for JWT authentication
# Generate with: openssl rand -hex 32
SECRET_KEY=your_secure_random_secret_key_at_least_32_chars
```

4. Start the service:
```bash
docker-compose up -d
```

5. Access the API:
   - **API**: http://localhost:8000
   - **Interactive docs**: http://localhost:8000/docs
   - **ReDoc**: http://localhost:8000/redoc

### Option 2: Local Development with UV

1. Install UV (if not already installed):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Create `.env` file and configure:
```bash
cp .env.example .env
# Edit .env and add required variables:
# - GEMINI_API_KEY (from https://ai.google.dev/)
# - SECRET_KEY (generate with: openssl rand -hex 32)
```

3. Install dependencies:
```bash
uv sync
```

4. Run the application:
```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Architecture

### Core Concepts

#### Artifacts
Artifacts are structured data objects that represent design outputs:

**Jewelry Design Artifact**:
```json
{
  "id": "uuid",
  "type": "design",
  "design": {
    "id": "uuid",
    "name": "Eternal Love Diamond Ring",
    "description": "A timeless engagement ring...",
    "properties": {
      "target_audience": "women",
      "jewelry_type": "ring",
      "metal": "platinum",
      "gemstone": "diamond",
      "style": "modern",
      "occasion": "engagement"
    },
    "images": ["image_id_1", "image_id_2"],
    "three_d_model": "model_id"
  }
}
```

**Product Recommendation Artifact**:
```json
{
  "id": "uuid",
  "type": "recommendation",
  "products": [
    {
      "id": "uuid",
      "name": "Classic Gold Band",
      "description": "...",
      "properties": {...},
      "price": 45700000,
      "images": ["image_id"]
    }
  ]
}
```

#### Conversation Flow
1. User creates a conversation
2. User sends message (optionally with images and/or artifact)
3. Assistant processes message, may call tools
4. Assistant responds with message (optionally with updated artifact)
5. Frontend displays chat and updates artifact section accordingly

## API Endpoints

### Authentication & User Management

#### Authentication Flow
1. **Register**: Create a new user account (`POST /api/v1/users/register`)
2. **Login**: Authenticate and receive a JWT token (`POST /api/v1/users/login`)
3. **Use Token**: Include the token in subsequent requests: `Authorization: Bearer <token>`

**Security Details**:
- JWT tokens with **7-day expiration**
- Password hashing with **bcrypt**
- Bearer token authentication on all protected endpoints
- Automatic user account isolation (users can only access their own data)

#### `POST /api/v1/users/register`
Create a new user account.

**Request**:
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "name": "Nguyễn Bảo Ngọc",
  "gender": "female",
  "age": 28,
  "marital_status": "single",
  "segment": "middle",
  "region": "south",
  "nationality": "Vietnamese"
}
```

**Required Fields**:
- `email`: Valid email address
- `password`: Minimum 8 characters

**Optional Profile Fields**:
- `name`: Full name
- `gender`: `male`, `female`, or `other`
- `age`: User age (0-150)
- `marital_status`: `single`, `married`, or `engaged`
- `segment`: Customer segment - `economic`, `middle`, `premium`, or `luxury`
- `region`: Geographic region - `north`, `central`, `south`, or `foreign`
- `nationality`: Country of nationality

**Response** (201 Created):
```json
{
  "id": "user-uuid",
  "email": "user@example.com",
  "name": "Nguyễn Bảo Ngọc",
  "gender": "female",
  "age": 28,
  "marital_status": "single",
  "segment": "middle",
  "region": "south",
  "nationality": "Vietnamese",
  "is_active": true,
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

#### `POST /api/v1/users/login`
Authenticate with email and password.

**Request**:
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Token expires in 7 days**. Use this token in the `Authorization` header for all subsequent requests.

#### `GET /api/v1/users/me`
Get current authenticated user profile.

**Headers**: `Authorization: Bearer <token>`

**Response**:
```json
{
  "id": "user-uuid",
  "email": "user@example.com",
  "name": "Nguyễn Bảo Ngọc",
  "gender": "female",
  "age": 28,
  "marital_status": "single",
  "segment": "middle",
  "region": "south",
  "nationality": "Vietnamese",
  "is_active": true,
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

#### `PUT /api/v1/users/me`
Update current user profile.

**Headers**: `Authorization: Bearer <token>`

**Request** (all fields optional):
```json
{
  "name": "Updated Name",
  "gender": "female",
  "age": 29,
  "marital_status": "engaged",
  "segment": "premium",
  "region": "north",
  "nationality": "Vietnamese"
}
```

**Response**: Updated user object (same as GET response)

#### `DELETE /api/v1/users/me`
Deactivate current user account.

**Headers**: `Authorization: Bearer <token>`

**Response**: 204 No Content

**Note**: This deactivates the account (sets `is_active = false`) but does not delete user data. Deactivated users cannot login.

---

### Conversations

#### `POST /api/v1/conversations`
Create a new conversation session.

**Request**:
```json
{
  "title": "Custom Wedding Ring Design",
  "description": "Designing a unique wedding ring"
}
```

**Response**:
```json
{
  "id": "conv-uuid",
  "user_id": "user-uuid",
  "title": "Custom Wedding Ring Design",
  "description": "Designing a unique wedding ring",
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

#### `GET /api/v1/conversations`
List all conversations for the authenticated user.

**Query Parameters**:
- `limit` (default: 50, max: 100)
- `offset` (default: 0)

#### `GET /api/v1/conversations/{conversation_id}`
Get conversation details with all messages.

**Response** includes all messages with their artifacts and images.

#### `DELETE /api/v1/conversations/{conversation_id}`
Delete a conversation and all its messages.

### Chat

#### `POST /api/v1/chat`
Send a message and receive AI response.

**Headers**: `Authorization: Bearer <token>`

**Request Body**:
- `conversation_id` (required): UUID of the conversation
- `message` (required): User's text message
- `images` (optional): Array of image IDs (images must be uploaded first via `/api/v1/images/upload`)
- `artifact` (optional): Current artifact state for updates

**Request Example**:
```json
{
  "conversation_id": "conv-uuid",
  "message": "I want a modern engagement ring with a solitaire diamond",
  "images": ["image_id_1"],
  "artifact": {
    "type": "design",
    "design": {
      "properties": {
        "jewelry_type": "ring",
        "occasion": "engagement"
      }
    }
  }
}
```

**Important**:
- Image IDs in the `images` array must reference images that were previously uploaded using `POST /api/v1/images/upload`
- The conversation must belong to the authenticated user

**Response**:
```json
{
  "conversation_id": "conv-uuid",
  "user_message": {
    "id": "msg-uuid",
    "role": "user",
    "content": "I want a modern engagement ring...",
    "images": ["image_id_1"],
    "artifact": {...},
    "created_at": "..."
  },
  "assistant_message": {
    "id": "msg-uuid",
    "role": "assistant",
    "content": "I've created a beautiful modern solitaire engagement ring design...",
    "artifact": {
      "type": "design",
      "design": {
        "id": "design-uuid",
        "name": "Modern Elegance Solitaire",
        "description": "A stunning modern solitaire engagement ring...",
        "properties": {
          "target_audience": "women",
          "jewelry_type": "ring",
          "metal": "platinum",
          "gemstone": "diamond",
          "style": "modern",
          "occasion": "engagement"
        },
        "images": ["generated_image_id"],
        "three_d_model": null
      }
    },
    "tool_calls": [...]
  }
}
```

### Images

**Important**: Images must be uploaded FIRST using the upload endpoint before they can be referenced in chat messages. The upload returns an `id` that you include in the `images` array of chat requests.

#### `POST /api/v1/images/upload`
Upload an image file for use in conversations.

**Headers**: `Authorization: Bearer <token>`

**Form Data**:
- `file`: Image file (JPEG, PNG, WebP, GIF)
- `conversation_id`: Optional conversation ID to associate the image with

**Response**:
```json
{
  "id": "img-uuid",
  "user_id": "user-uuid",
  "filename": "reference.jpg",
  "content_type": "image/jpeg",
  "image_data": "base64_encoded_string",
  "conversation_id": "conv-uuid",
  "created_at": "..."
}
```

**Note**: Save the returned `id` to reference this image in subsequent chat requests.

#### `GET /api/v1/images/{image_id}`
Get an image by ID.

**Headers**: `Authorization: Bearer <token>`

**Response**: Image object with base64 data

#### `GET /api/v1/images`
List images with pagination.

**Query Parameters**:
- `page` (default: 1)
- `page_size` (default: 20)
- `conversation_id`: Optional filter

#### `DELETE /api/v1/images/{image_id}`
Delete an image.

---

### Utility Endpoints

#### `GET /`
Root endpoint with API information.

**No authentication required**

**Response**:
```json
{
  "message": "Welcome to PNJ Jewelry AI Designer API",
  "version": "1.0.0",
  "docs": "/docs",
  "redoc": "/redoc"
}
```

#### `GET /health`
Health check endpoint for monitoring and load balancers.

**No authentication required**

**Response**:
```json
{
  "status": "healthy",
  "service": "PNJ Jewelry AI Designer",
  "version": "1.0.0"
}
```

## Usage Examples

### Authentication Workflow

```bash
# 1. Register a new user
curl -X POST "http://localhost:8000/api/v1/users/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "customer@example.com",
    "password": "SecurePass123!",
    "name": "Nguyễn Văn An",
    "gender": "male",
    "age": 30,
    "marital_status": "engaged",
    "segment": "middle",
    "region": "south",
    "nationality": "Vietnamese"
  }'

# Response: {"id": "user-uuid", "email": "customer@example.com", ...}

# 2. Login to get access token
curl -X POST "http://localhost:8000/api/v1/users/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "customer@example.com",
    "password": "SecurePass123!"
  }'

# Response: {"access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...", "token_type": "bearer"}

# 3. Get current user profile
curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# 4. Update user profile
curl -X PUT "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Nguyễn Văn An",
    "age": 31,
    "segment": "premium"
  }'
```

### Complete Design Workflow

```bash
# 1. Create a conversation (use token from login)
curl -X POST "http://localhost:8000/api/v1/conversations" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Anniversary Ring Design",
    "description": "10th anniversary special ring"
  }'

# Response: {"id": "conv-123", ...}

# 2. Upload reference image FIRST (required before using in chat)
curl -X POST "http://localhost:8000/api/v1/images/upload" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@ring_reference.jpg" \
  -F "conversation_id=conv-123"

# Response: {"id": "img-456", ...}
# IMPORTANT: Save the "img-456" ID to use in the next step!

# 3. Chat with assistant using the uploaded image ID
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "conv-123",
    "message": "Create an elegant vintage-style ring inspired by this image",
    "images": ["img-456"]
  }'

# Response includes assistant message with design artifact

# 4. Modify design via chat
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "conv-123",
    "message": "Can you make it with rose gold instead?",
    "artifact": {
      "type": "design",
      "design": {
        "id": "design-from-previous-response",
        "properties": {
          "metal": "18k_gold",
          "color": "rose gold"
        }
      }
    }
  }'

# Assistant updates the artifact with new metal specification
```

### Product Recommendation

```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "conv-123",
    "message": "Show me some PNJ rings similar to this design under 50 million VND"
  }'

# Assistant responds with recommendation artifact containing matching products
```

## Project Structure

```
jewelry-design-platform-api/
├── app/
│   ├── agents/                     # AI agents
│   │   ├── assistant_agent.py     # Main conversational agent with tools
│   │   └── jewelry_design_agent.py # Design generation agent
│   ├── api/                        # API route handlers
│   │   ├── chat.py                # Chat endpoints
│   │   ├── conversations.py       # Conversation management
│   │   ├── images.py              # Image upload/management
│   │   └── users.py               # User management
│   ├── db/                         # Database configuration
│   │   └── database.py
│   ├── models/                     # SQLAlchemy ORM models
│   │   ├── conversation.py
│   │   ├── message.py
│   │   ├── image.py
│   │   └── user.py
│   ├── schemas/                    # Pydantic schemas
│   │   ├── artifact.py            # Artifact schemas
│   │   ├── conversation.py
│   │   ├── message.py
│   │   ├── image.py
│   │   ├── jewelry.py             # Jewelry properties
│   │   └── user.py
│   ├── services/                   # Business logic
│   │   ├── assistant_service.py   # Assistant orchestration
│   │   ├── conversation_service.py
│   │   ├── image_service.py
│   │   └── user_service.py
│   ├── utils/                      # Utilities
│   │   └── auth.py                # Authentication helpers
│   ├── config.py                  # Configuration
│   └── main.py                    # FastAPI application
├── data/                          # Database and files (gitignored)
├── tests/                         # Test files
├── .env.example                   # Environment template
├── .gitignore
├── .python-version                # Python version (3.13)
├── docker-compose.yml             # Docker Compose config
├── Dockerfile                     # Docker image
├── pyproject.toml                 # Project dependencies (UV)
├── uv.lock                        # Lock file
├── ARCHITECTURE.md                # Architecture documentation
└── README.md
```

## Jewelry Properties

The system supports comprehensive jewelry attributes:

| Property | Values |
|----------|--------|
| **target_audience** | men, women, unisex, couple, personalized |
| **jewelry_type** | ring, earring, necklace, bracelet, anklet, bangle |
| **metal** | 18k_gold, 14k_gold, 10k_gold, silver, platinum |
| **gemstone** | diamond, ruby, sapphire, emerald, pearl, amethyst, topaz, garnet, aquamarine |
| **style** | classic, modern, vintage, minimalist, luxury, personality, natural |
| **occasion** | wedding, engagement, casual, formal, party, daily_wear |
| **color** | Free text (e.g., "white gold", "rose gold") |
| **thickness** | thin, medium, thick |
| **inspiration** | Free text for design story/background |

## Configuration

Environment variables in `.env`:

```bash
# Required
GEMINI_API_KEY=your_api_key_here

# Required - Authentication Secret (IMPORTANT: Change in production!)
SECRET_KEY=your_secret_key_here

# Optional (defaults shown)
DATABASE_URL=sqlite:///./data/jewelry_designer.db
CHAT_MODEL=gemini-2.0-flash
IMAGE_MODEL=gemini-2.5-flash-image

# App settings
APP_NAME="PNJ Jewelry AI Designer"
APP_VERSION="0.1.0"
DEBUG=True
```

### Authentication Configuration

The API uses **JWT (JSON Web Token)** authentication with the following settings (configured in `app/services/user_service.py`):

- **Algorithm**: HS256
- **Token Expiration**: 7 days (10080 minutes)
- **Password Hashing**: bcrypt with automatic salt generation

**Important Security Notes**:
- `SECRET_KEY` must be a strong, random string (at least 32 characters)
- Generate a secure key: `openssl rand -hex 32`
- Never commit the actual `SECRET_KEY` to version control
- In production, use environment-specific secrets management (e.g., AWS Secrets Manager, HashiCorp Vault)
- The default 7-day token expiration is suitable for PoC; adjust for production based on security requirements

## Development

### Code Quality

```bash
# Format code
uv run black app/

# Type checking
uv run mypy app/

# Linting
uv run ruff check app/
```

## AI Agent Architecture

### Assistant Agent
- Handles conversational interactions
- Supports tool calling for extended capabilities
- Maintains conversation context
- Iterative tool execution (max 10 iterations)

### Jewelry Design Agent
- Generates structured jewelry designs
- Uses Gemini's structured output (JSON mode)
- **Considers user demographics and preferences**: The agent uses the authenticated user's profile data (gender, age, marital status, segment, region, nationality) to personalize design recommendations
- Incorporates reference images
- Outputs complete `JewelryDesignOutput` objects

**User Demographics in AI Design**:
The system leverages rich user profile data to provide personalized jewelry recommendations:
- **Gender & Age**: Influences style preferences and design trends
- **Marital Status**: Helps suggest appropriate jewelry types (engagement, wedding, anniversary)
- **Segment** (economic/middle/premium/luxury): Guides material selection and price ranges
- **Region** (north/central/south/foreign): Considers regional design preferences and cultural influences
- **Nationality**: Incorporates cultural design elements and traditions

### Tool System
The assistant can register and call tools dynamically:

```python
# Example: Register a price estimation tool
assistant_agent.register_tool(
    name="estimate_price",
    description="Estimate jewelry price based on materials",
    parameters={...},
    implementation=price_estimation_function
)
```

## Production Considerations

This is a **Proof of Concept** implementation. For production deployment:

### Security
- [x] **JWT authentication** (implemented with 7-day token expiration)
- [x] **Password hashing** (bcrypt)
- [x] **User authentication and authorization** (bearer token)
- [ ] Add **refresh tokens** for JWT token renewal
- [ ] Add **rate limiting** per user/IP
- [ ] Enhanced input sanitization and validation
- [ ] **HTTPS/TLS encryption** in production
- [ ] Secrets management (AWS Secrets Manager, HashiCorp Vault)
- [ ] **CORS configuration** for specific origins (currently allows all)
- [ ] API key rotation mechanism
- [ ] Password reset/recovery flow
- [ ] Email verification for new accounts
- [ ] Multi-factor authentication (MFA)

### Database
- [ ] Migrate to PostgreSQL or MySQL
- [ ] Implement database connection pooling
- [ ] Add database migrations with Alembic
- [ ] Database backup and recovery strategy
- [ ] Optimize indexes for query performance

### Storage
- [ ] Move images to cloud storage (AWS S3, Google Cloud Storage)
- [ ] Implement CDN for image delivery
- [ ] Image optimization and compression
- [ ] 3D model storage and streaming

### Scalability
- [ ] Horizontal scaling with load balancer
- [ ] Redis for caching and session management
- [ ] Message queue for async tasks (Celery, RQ)
- [ ] Separate worker services for heavy operations
- [ ] Database read replicas

### Monitoring
- [ ] Application logging (structured JSON logs)
- [ ] Error tracking (Sentry, Rollbar)
- [ ] Performance monitoring (New Relic, Datadog)
- [x] **Health check endpoint** (`/health`)
- [ ] Metrics collection (Prometheus)
- [ ] Alerting system

### Features
- [ ] Real 3D model generation service integration
- [ ] Integration with PNJ inventory and pricing systems
- [ ] Advanced search and filtering
- [ ] Design version history
- [ ] Multi-language support (Vietnamese, English)
- [ ] AR jewelry preview
- [ ] Export to CAD formats
- [ ] Collaborative design features
- [ ] Design approval workflow

## Troubleshooting

### Authentication errors ("Could not validate credentials")
**Cause**: Missing or invalid `SECRET_KEY` in `.env`

**Solution**:
```bash
# Generate a secure secret key
openssl rand -hex 32

# Or with Python
python -c "import secrets; print(secrets.token_hex(32))"

# Add to .env file
echo "SECRET_KEY=your_generated_key_here" >> .env

# Restart the application
docker-compose restart  # or restart uvicorn
```

### "Invalid API key" error
- Verify `GEMINI_API_KEY` in `.env`
- Ensure the API key has access to Gemini 2.0 Flash
- Get API key from https://ai.google.dev/

### "Image not found" errors in chat
**Cause**: Referencing image IDs that don't exist or weren't uploaded

**Solution**:
1. Upload images FIRST using `POST /api/v1/images/upload`
2. Save the returned image `id` from the upload response
3. Use that `id` in the `images` array of your chat request

Example workflow:
```bash
# 1. Upload image
RESPONSE=$(curl -X POST "http://localhost:8000/api/v1/images/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@myimage.jpg")

# 2. Extract image ID (using jq)
IMAGE_ID=$(echo $RESPONSE | jq -r '.id')

# 3. Use in chat
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"conversation_id\": \"$CONV_ID\", \"message\": \"Design based on this\", \"images\": [\"$IMAGE_ID\"]}"
```

### Docker issues
```bash
# Rebuild without cache
docker-compose build --no-cache

# View logs
docker-compose logs -f

# Check port availability
netstat -an | grep 8000
```

### Database errors
```bash
# Reset database
rm data/jewelry_designer.db

# Restart application (will recreate tables)
docker-compose restart
```

### "Conversation not found" errors
- Ensure the conversation ID exists
- Verify the conversation belongs to the authenticated user

## API Documentation

Interactive documentation is automatically generated:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Contributing

This is a proprietary project for PNJ Jewelry Corp. For internal development:

1. Create a feature branch
2. Make changes with tests
3. Submit pull request for review
4. Ensure CI/CD checks pass

## Support

For issues or questions:
1. Check this README and ARCHITECTURE.md
2. Review API documentation at `/docs`
3. Contact the PNJ development team

---

**Built for PNJ Jewelry Corp** - Empowering customers to design their dream jewelry through AI-powered collaboration.
