# Chat and File APIs Usage Guide

A practical guide for using the Jewelry Design Platform APIs to upload files, manage conversations, and chat with the AI assistant.

## Table of Contents

- [Authentication](#authentication)
- [File APIs](#file-apis)
- [Chat APIs](#chat-apis)
- [Complete Workflows](#complete-workflows)
- [Error Handling](#error-handling)
- [Best Practices](#best-practices)

## Authentication

All API endpoints require authentication using JWT tokens.

### 1. Register a New User

```bash
POST /api/v1/users/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "name": "Jane Nguyen",
  "gender": "female",
  "age": 28,
  "marital_status": "single",
  "segment": "premium",
  "region": "south",
  "nationality": "Vietnamese"
}
```

**Response:**
```json
{
  "id": "user_abc123",
  "email": "user@example.com",
  "name": "Jane Nguyen",
  "gender": "female",
  "age": 28,
  "marital_status": "single",
  "segment": "premium",
  "region": "south",
  "nationality": "Vietnamese",
  "is_active": true,
  "created_at": "2025-11-16T10:00:00",
  "updated_at": "2025-11-16T10:00:00"
}
```

### 2. Login

```bash
POST /api/v1/users/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 3. Use Token in Requests

Include the token in the `Authorization` header for all subsequent requests:

```bash
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## File APIs

### Upload a File

**Important:** Files must be uploaded BEFORE they can be referenced in chat messages.

```bash
POST /api/v1/files/upload
Authorization: Bearer <your_token>
Content-Type: multipart/form-data

file: <binary file data>
```

**Example using cURL:**
```bash
curl -X POST "http://localhost:8080/api/v1/files/upload" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -F "file=@/path/to/ring_reference.jpg"
```

**Example using Python:**
```python
import requests

url = "http://localhost:8080/api/v1/files/upload"
headers = {
    "Authorization": f"Bearer {access_token}"
}
files = {
    "file": open("ring_reference.jpg", "rb")
}

response = requests.post(url, headers=headers, files=files)
file_data = response.json()

print(f"File ID: {file_data['short_id']}")  # e.g., "a3f9k2m7"
```

**Example using JavaScript/Fetch:**
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const response = await fetch('http://localhost:8080/api/v1/files/upload', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`
  },
  body: formData
});

const fileData = await response.json();
console.log(`File ID: ${fileData.short_id}`);  // e.g., "a3f9k2m7"
```

**Response:**
```json
{
  "short_id": "a3f9k2m7",
  "filename": "ring_reference.jpg",
  "content_type": "image/jpeg",
  "file_size": 245678,
  "created_at": "2025-11-16T10:30:00"
}
```

**Key Points:**
- Save the `short_id` - you'll use it to reference this file
- Short IDs are 8 characters (e.g., "a3f9k2m7")
- Easy to reference in LLM conversations

### Download a File

```bash
GET /api/v1/files/{short_id}/download
Authorization: Bearer <your_token>
```

**Example:**
```bash
curl -X GET "http://localhost:8080/api/v1/files/a3f9k2m7/download" \
  -H "Authorization: Bearer <token>" \
  -o downloaded_image.jpg
```

**Response:**
- Binary file data with appropriate Content-Type header
- Content-Disposition header with original filename

### Get File Metadata

```bash
GET /api/v1/files/{short_id}
Authorization: Bearer <your_token>
```

**Response:**
```json
{
  "short_id": "a3f9k2m7",
  "filename": "ring_reference.jpg",
  "file_path": "a3/a3f9k2m7.jpg",
  "content_type": "image/jpeg",
  "file_size": 245678,
  "user_id": "user_abc123",
  "created_at": "2025-11-16T10:30:00",
  "updated_at": "2025-11-16T10:30:00"
}
```

### List Your Files

```bash
GET /api/v1/files?limit=100&offset=0
Authorization: Bearer <your_token>
```

**Response:**
```json
{
  "files": [
    {
      "short_id": "a3f9k2m7",
      "filename": "ring_reference.jpg",
      "content_type": "image/jpeg",
      "file_size": 245678,
      "created_at": "2025-11-16T10:30:00"
    },
    {
      "short_id": "b4h8j3n9",
      "filename": "necklace_design.png",
      "content_type": "image/png",
      "file_size": 156789,
      "created_at": "2025-11-16T11:00:00"
    }
  ],
  "total": 2
}
```

### Delete a File

```bash
DELETE /api/v1/files/{short_id}
Authorization: Bearer <your_token>
```

**Response:**
- 204 No Content (success)
- 404 Not Found (file doesn't exist)
- 403 Forbidden (not your file)

---

## Chat APIs

### 1. Send a Chat Message (Auto-Creates Conversation)

**New in v1.1**: You can now start chatting immediately without creating a conversation first!

```bash
POST /api/v1/chat
Authorization: Bearer <your_token>
Content-Type: application/json

{
  "message": "I want to design an engagement ring for my girlfriend"
}
```

**What happens:**
1. ✅ No `conversation_id` provided
2. ✅ New conversation auto-created with title from your message
3. ✅ Message sent to assistant
4. ✅ Response includes new `conversation_id`

**Response:**
```json
{
  "conversation_id": "conv_auto123",
  "user_message": {
    "id": "msg_001",
    "conversation_id": "conv_auto123",
    "role": "user",
    "content": "I want to design an engagement ring for my girlfriend",
    "images": []
  },
  "assistant_message": {
    "id": "msg_002",
    "role": "assistant",
    "content": "That's wonderful! 💍 Tell me more about her...",
    "images": []
  }
}
```

Save the `conversation_id` from the response to continue the conversation!

### 2. Continue an Existing Conversation

```bash
POST /api/v1/chat
Authorization: Bearer <your_token>
Content-Type: application/json

{
  "conversation_id": "conv_auto123",
  "message": "She loves simple and elegant designs"
}
```

**Response:**
```json
{
  "conversation_id": "conv_auto123",
  "user_message": {
    "id": "msg_003",
    "role": "user",
    "content": "She loves simple and elegant designs"
  },
  "assistant_message": {
    "id": "msg_004",
    "role": "assistant",
    "content": "Perfect! Simple and elegant is timeless. Let me create a design..."
  }
}
```

### 3. Create a Conversation Manually (Optional)

You can still create conversations manually if you want custom titles:

```bash
POST /api/v1/conversations
Authorization: Bearer <your_token>
Content-Type: application/json

{
  "title": "Engagement Ring Design"
}
```

**Response:**
```json
{
  "id": "conv_xyz789",
  "user_id": "user_abc123",
  "title": "Engagement Ring Design",
  "created_at": "2025-11-16T12:00:00",
  "updated_at": "2025-11-16T12:00:00"
}
```

### 3. Send Chat with Reference Images

The assistant can now **see and understand images** you upload! Images are automatically included in the conversation context.

**Step 1: Upload the reference image first**
```bash
POST /api/v1/files/upload
file: ring_inspiration.jpg

# Response: {"short_id": "a3f9k2m7", ...}
```

**Step 2: Send chat with file ID**
```bash
POST /api/v1/chat
Authorization: Bearer <your_token>
Content-Type: application/json

{
  "conversation_id": "conv_xyz789",
  "message": "Can you design a ring similar to this one?",
  "images": ["a3f9k2m7"]
}
```

**What happens:**
1. ✅ Image is loaded from file service
2. ✅ Converted to base64 for LLM vision API
3. ✅ LLM can **see and analyze** the image
4. ✅ Design is created based on visual features

**Response:**
```json
{
  "conversation_id": "conv_xyz789",
  "user_message": {
    "id": "msg_003",
    "role": "user",
    "content": "Can you design a ring similar to this one?",
    "images": ["a3f9k2m7"],
    "artifact": null
  },
  "assistant_message": {
    "id": "msg_004",
    "role": "assistant",
    "content": "Beautiful reference! I can see the elegant solitaire style with a round brilliant diamond in a 4-prong setting. The band appears to be platinum with delicate pavé accents. Let me create a design inspired by this...",
    "images": [],
    "tool_calls": [
      {
        "name": "generate_concept_design",
        "arguments": {...}
      }
    ],
    "artifact": {
      "type": "design",
      "design": {
        "name": "Eternal Promise",
        "description": "A classic solitaire diamond ring inspired by the reference image...",
        "properties": {...},
        "images": [],
        "three_d_model": null
      }
    }
  }
}
```

**Multiple Images:**
You can send multiple reference images at once:
```json
{
  "conversation_id": "conv_xyz789",
  "message": "I like elements from all of these designs",
  "images": ["a3f9k2m7", "b4h8j3n9", "c5k9m4p2"]
}
```

**Image Context Retention:**
- Images remain in conversation context
- Assistant can reference them in later messages
- Automatically used as reference for concept design and 2D generation

### 4. Request 2D Image Generation

```bash
POST /api/v1/chat
Content-Type: application/json

{
  "conversation_id": "conv_xyz789",
  "message": "Please generate 2D images of this design"
}
```

**Response:**
```json
{
  "conversation_id": "conv_xyz789",
  "assistant_message": {
    "content": "I've generated 2D product images from 3 different angles!",
    "artifact": {
      "type": "design",
      "design": {
        "name": "Eternal Promise",
        "description": "...",
        "images": [
          "c5k9m4p2",  // Front view file ID
          "d6n3q7r8",  // Side view file ID
          "e8s2t9v4"   // Top view file ID
        ]
      }
    }
  }
}
```

**Step 3: Download generated images**
```bash
# Download each image
GET /api/v1/files/c5k9m4p2/download  # Front view
GET /api/v1/files/d6n3q7r8/download  # Side view
GET /api/v1/files/e8s2t9v4/download  # Top view
```

### 5. Get Conversation History

```bash
GET /api/v1/conversations/{conversation_id}
Authorization: Bearer <your_token>
```

**Response:**
```json
{
  "id": "conv_xyz789",
  "user_id": "user_abc123",
  "title": "Engagement Ring Design",
  "created_at": "2025-11-16T12:00:00",
  "updated_at": "2025-11-16T12:05:00",
  "messages": [
    {
      "id": "msg_001",
      "role": "user",
      "content": "I want to design an engagement ring",
      "images": []
    },
    {
      "id": "msg_002",
      "role": "assistant",
      "content": "That's wonderful! Tell me more...",
      "images": []
    }
  ]
}
```

---

## Complete Workflows

### Workflow 1: Simple Design Request (New Simplified Flow!)

**No need to create conversation first** - just start chatting!

```python
import requests

BASE_URL = "http://localhost:8080/api/v1"
token = "your_access_token"
headers = {"Authorization": f"Bearer {token}"}

# Step 1: Start chatting (conversation auto-created!)
chat1 = requests.post(
    f"{BASE_URL}/chat",
    headers=headers,
    json={
        "message": "I want a modern diamond ring for my engagement"
    }
).json()

print("Assistant:", chat1["assistant_message"]["content"])

# Save the auto-created conversation_id for next messages
conv_id = chat1["conversation_id"]
print(f"Conversation ID: {conv_id}")

# Step 2: Provide more details
chat2 = requests.post(
    f"{BASE_URL}/chat",
    headers=headers,
    json={
        "conversation_id": conv_id,
        "message": "I prefer white gold, simple and elegant style"
    }
).json()

# Step 3: Generate design
chat3 = requests.post(
    f"{BASE_URL}/chat",
    headers=headers,
    json={
        "conversation_id": conv_id,
        "message": "Please create a design based on this"
    }
).json()

# Check if design was created
artifact = chat3["assistant_message"].get("artifact")
if artifact and artifact["type"] == "design":
    design = artifact["design"]
    print(f"Design created: {design['name']}")
    print(f"Description: {design['description']}")
```

### Workflow 2: Design with Reference Images

**The assistant can now SEE your images!** Upload reference photos and the AI will analyze visual features.

```python
import requests

BASE_URL = "http://localhost:8080/api/v1"
token = "your_access_token"
headers = {"Authorization": f"Bearer {token}"}

# Step 1: Upload reference image
with open("ring_reference.jpg", "rb") as f:
    file_response = requests.post(
        f"{BASE_URL}/files/upload",
        headers=headers,
        files={"file": f}
    ).json()

image_id = file_response["short_id"]
print(f"Uploaded image: {image_id}")

# Step 2: Send message with reference image (conversation auto-created!)
# The assistant will SEE and ANALYZE the image!
chat = requests.post(
    f"{BASE_URL}/chat",
    headers=headers,
    json={
        "message": "Create a ring design inspired by this image",
        "images": [image_id]  # Image is sent to vision API
    }
).json()

# Save conversation_id for continuing the chat
conv_id = chat["conversation_id"]

print("Assistant:", chat["assistant_message"]["content"])
# Example response: "I can see a beautiful solitaire ring with a round diamond
#                    in a 4-prong platinum setting. Let me create a design..."

# Check for design artifact
artifact = chat["assistant_message"].get("artifact")
if artifact:
    design = artifact['design']
    print(f"\nDesign created: {design['name']}")
    print(f"Description: {design['description']}")
    print(f"Metal: {design['properties']['metal']}")
    print(f"Gemstone: {design['properties']['gemstone']}")

# Step 3: Request 2D images (reference image is still in context)
chat2 = requests.post(
    f"{BASE_URL}/chat",
    headers=headers,
    json={
        "conversation_id": conv_id,
        "message": "Generate 2D images of this design"
    }
).json()

# The 2D generation will use the original reference for style consistency
artifact2 = chat2["assistant_message"]["artifact"]
generated_images = artifact2["design"]["images"]
print(f"\nGenerated {len(generated_images)} images: {generated_images}")
```

### Workflow 3: Generate and Download 2D Images

```python
import requests

BASE_URL = "http://localhost:8080/api/v1"
token = "your_access_token"
headers = {"Authorization": f"Bearer {token}"}

# Assume we have a conversation with a design already created
conv_id = "conv_xyz789"

# Step 1: Request 2D image generation
chat = requests.post(
    f"{BASE_URL}/chat",
    headers=headers,
    json={
        "conversation_id": conv_id,
        "message": "Generate 2D images of this design"
    }
).json()

# Step 2: Get image IDs from artifact
artifact = chat["assistant_message"]["artifact"]
image_ids = artifact["design"]["images"]

print(f"Generated {len(image_ids)} images: {image_ids}")

# Step 3: Download each image
for idx, img_id in enumerate(image_ids):
    response = requests.get(
        f"{BASE_URL}/files/{img_id}/download",
        headers=headers
    )

    # Save to file
    filename = f"design_view_{idx+1}.png"
    with open(filename, "wb") as f:
        f.write(response.content)

    print(f"Downloaded: {filename}")
```

### Workflow 4: JavaScript/Frontend Example

```javascript
const BASE_URL = 'http://localhost:8080/api/v1';
let accessToken = 'your_access_token';

// Upload reference image
async function uploadImage(file) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${BASE_URL}/files/upload`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`
    },
    body: formData
  });

  return await response.json();
}

// Send chat message (conversation auto-created if not provided!)
async function sendMessage(conversationId, message, imageIds = []) {
  const body = {
    message: message,
    images: imageIds
  };

  // Only include conversation_id if provided (otherwise auto-creates)
  if (conversationId) {
    body.conversation_id = conversationId;
  }

  const response = await fetch(`${BASE_URL}/chat`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(body)
  });

  return await response.json();
}

// Complete workflow (simplified - no manual conversation creation!)
async function designWorkflow() {
  // 1. Upload reference image
  const fileInput = document.getElementById('imageInput');
  const fileData = await uploadImage(fileInput.files[0]);
  console.log('Uploaded:', fileData.short_id);

  // 2. Send message with image (conversation auto-created!)
  const chat = await sendMessage(
    null,  // No conversation_id - will auto-create!
    'Design a ring based on this reference',
    [fileData.short_id]
  );

  console.log('Assistant:', chat.assistant_message.content);
  console.log('Conversation ID:', chat.conversation_id);  // Save this for next messages

  // 3. Display artifact if available
  if (chat.assistant_message.artifact) {
    const design = chat.assistant_message.artifact.design;
    console.log('Design:', design.name);

    // Display design images if any
    if (design.images.length > 0) {
      design.images.forEach(imageId => {
        const imgUrl = `${BASE_URL}/files/${imageId}/download`;
        // Display image in UI
        displayImage(imgUrl);
      });
    }
  }

  // 4. Continue conversation
  const chat2 = await sendMessage(
    chat.conversation_id,  // Use the auto-created conversation_id
    'Generate 2D images of this design'
  );
}
```

---

## Error Handling

### Common HTTP Status Codes

| Code | Meaning | Common Causes |
|------|---------|---------------|
| 400 | Bad Request | Invalid file format, missing required fields |
| 401 | Unauthorized | Missing or invalid token |
| 403 | Forbidden | Trying to access/delete someone else's file |
| 404 | Not Found | File or conversation doesn't exist |
| 413 | Payload Too Large | File size exceeds limit |
| 500 | Internal Server Error | Server-side error (check logs) |

### Error Response Format

```json
{
  "detail": "File with short_id 'xyz123' not found"
}
```

### Example Error Handling (Python)

```python
try:
    response = requests.post(
        f"{BASE_URL}/chat",
        headers=headers,
        json={
            "conversation_id": conv_id,
            "message": "Hello"
        }
    )
    response.raise_for_status()  # Raise exception for 4xx/5xx

    data = response.json()
    print("Success:", data)

except requests.exceptions.HTTPError as e:
    if e.response.status_code == 401:
        print("Authentication failed. Please login again.")
    elif e.response.status_code == 404:
        print("Conversation not found.")
    else:
        print(f"Error: {e.response.json()['detail']}")

except requests.exceptions.ConnectionError:
    print("Cannot connect to server")
```

### Example Error Handling (JavaScript)

```javascript
async function sendMessageSafe(conversationId, message) {
  try {
    const response = await fetch(`${BASE_URL}/chat`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        conversation_id: conversationId,
        message: message
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Request failed');
    }

    return await response.json();

  } catch (error) {
    console.error('Chat error:', error.message);

    if (error.message.includes('token')) {
      // Handle authentication error
      redirectToLogin();
    }

    throw error;
  }
}
```

---

## Best Practices

### 1. File Management

✅ **DO:**
- Upload files before referencing them in chat
- Save file IDs for later use
- Check file upload response for errors
- Delete unused files to save space

❌ **DON'T:**
- Try to send base64 images directly in chat
- Reference file IDs that don't exist
- Upload the same file multiple times

### 2. Chat Flow

✅ **DO:**
- Create one conversation per design session
- Provide context in your messages
- Wait for assistant response before sending next message
- Check for artifacts in assistant messages

❌ **DON'T:**
- Send rapid-fire messages without waiting
- Mix multiple design projects in one conversation
- Skip important details (style, occasion, preferences)

### 3. Image Handling

✅ **DO:**
- Download generated images by file ID
- Store file IDs for future reference
- Use appropriate image formats (JPEG, PNG)

❌ **DON'T:**
- Try to decode base64 from chat responses (not sent anymore)
- Assume images are embedded in messages

### 4. Authentication

✅ **DO:**
- Store tokens securely (encrypted storage, environment variables)
- Handle token expiration gracefully
- Refresh tokens when needed

❌ **DON'T:**
- Hardcode tokens in source code
- Share tokens between users
- Commit tokens to version control

### 5. Performance

✅ **DO:**
- Reuse conversations for related messages
- Cache file IDs to avoid re-uploading
- Implement loading states for long operations (2D generation)

❌ **DON'T:**
- Create new conversation for every message
- Upload large files unnecessarily
- Poll for updates (wait for response)

---

## Rate Limits & Quotas

(Note: Update these based on your actual implementation)

- **File uploads**: Max 10MB per file
- **Chat messages**: No hard limit, but be reasonable
- **Concurrent requests**: Recommended max 10 per user
- **File storage**: Check with your plan

---

## API Reference Quick Links

- **Full API Documentation**: http://localhost:8080/docs
- **ReDoc Documentation**: http://localhost:8080/redoc
- **Health Check**: http://localhost:8080/health

---

## Support

For issues or questions:
- Check the error message in the response
- Review the API documentation at `/docs`
- Check server logs for detailed errors
- Refer to `FILE_HANDLING_FLOW.md` for architecture details

---

## Changelog

### Version 1.1.0 (2025-11-16)
- Implemented file service with short IDs
- Updated chat to use file IDs instead of base64
- Added file upload/download endpoints
- Agents now save generated images to file service

### Version 1.0.0 (Initial Release)
- Basic chat functionality
- Conversation management
- User authentication
