# Webhook Server Setup Guide

Log meals, workouts, and health data to Notion from anywhere - phone, web, or voice assistant.

## Quick Start

### 1. Deploy the Server

**Option A: Railway (Recommended - Free tier available)**
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

**Option B: Render**
1. Connect your GitHub repo at render.com
2. Create a new "Web Service"
3. Set build command: `pip install -r requirements.txt && pip install -r webhook/requirements.txt`
4. Set start command: `uvicorn webhook.server:app --host 0.0.0.0 --port $PORT`

**Option C: Local (for testing)**
```bash
cd /path/to/2026-Fitness-Diet
pip install -r webhook/requirements.txt
python webhook/server.py
```

### 2. Set Environment Variables

```bash
NOTION_API_KEY=ntn_xxxxx          # Your Notion API key
NOTION_DATABASE_ID=xxxxx          # Your database ID
WEBHOOK_API_KEY=your-secret-key   # Create a secure key for API access
```

### 3. Test the Endpoint

```bash
# Health check
curl https://your-app.railway.app/

# Log a meal
curl -X POST https://your-app.railway.app/log/quick \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-key" \
  -d '{"text": "eggs and bacon for breakfast"}'
```

---

## iOS Shortcuts Setup

Create these shortcuts to log from your iPhone with Siri or a tap:

### Shortcut 1: "Log Meal" (Voice)

1. Open Shortcuts app → + New Shortcut
2. Add action: **Dictate Text**
3. Add action: **Get Contents of URL**
   - URL: `https://your-app.railway.app/log/quick`
   - Method: POST
   - Headers:
     - `X-API-Key`: your-secret-key
     - `Content-Type`: application/json
   - Request Body: JSON
     - `text`: (Dictated Text variable)
4. Add action: **Show Result**
5. Name it "Log Meal"

Now say: "Hey Siri, Log Meal" → "I had salmon and broccoli for dinner"

### Shortcut 2: "Log Weight"

1. Open Shortcuts app → + New Shortcut
2. Add action: **Ask for Input** (Number, prompt: "What's your weight?")
3. Add action: **Get Contents of URL**
   - URL: `https://your-app.railway.app/log/weight`
   - Method: POST
   - Headers: X-API-Key, Content-Type
   - Request Body: JSON → `weight`: (Provided Input)
4. Add action: **Show Result**
5. Name it "Log Weight"

### Shortcut 3: "Quick Log" (Text)

1. Open Shortcuts app → + New Shortcut
2. Add action: **Ask for Input** (Text, prompt: "What do you want to log?")
3. Add action: **Get Contents of URL** (same as above with /log/quick)
4. Add action: **Show Result**
5. Name it "Quick Log"

---

## API Endpoints Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/log/meal` | POST | Log a meal with calories/protein estimation |
| `/log/workout` | POST | Log a workout |
| `/log/weight` | POST | Log weight and track progress |
| `/log/mood` | POST | Log mood |
| `/log/quick` | POST | Smart logging - auto-detects type |
| `/status` | GET | Get today's progress |
| `/suggest/meal` | GET | Get meal suggestions |

### Request Examples

**Log a meal:**
```json
POST /log/meal
{
  "description": "grilled chicken salad with olive oil dressing",
  "meal_type": "lunch",
  "notes": "at the office"
}
```

**Quick log (auto-detect):**
```json
POST /log/quick
{
  "text": "ran 3 miles this morning"
}
```

**Log weight:**
```json
POST /log/weight
{
  "weight": 248.5,
  "notes": "after morning workout"
}
```

### Response Example

```json
{
  "success": true,
  "entry_id": "abc123",
  "parsed": {
    "calories": 450,
    "protein": 42,
    "meal_type": "Lunch"
  },
  "warnings": ["High sodium - consider low-sodium dressing"],
  "follow_up_questions": []
}
```

---

## Android Setup (Tasker)

1. Install Tasker from Play Store
2. Create a new Task:
   - Action: **HTTP Request**
   - Method: POST
   - URL: your webhook URL
   - Headers: X-API-Key, Content-Type
   - Body: `{"text": "%VOICE"}`
3. Create a Profile triggered by voice command
4. Link to the Task

---

## Security Notes

- Always use HTTPS in production
- Keep your `WEBHOOK_API_KEY` secret
- Consider IP allowlisting if only accessing from known locations
- The API key is passed via header, not URL, for security
