# 🏦 Verity AI — Bank Loan Document Verification System

> AI-powered document verification backend for bank loan approval using Node.js + Python FastAPI

![Architecture](https://img.shields.io/badge/Architecture-Microservices-blue)
![Node](https://img.shields.io/badge/Node.js-18+-green)
![Python](https://img.shields.io/badge/Python-3.10+-yellow)
![License](https://img.shields.io/badge/License-MIT-purple)

---

## 📁 Project Structure

```
verity-ai-main/
├── backend/                    ← Node.js Express Backend tamizh github check
│   ├── server.js               ← Entry point
│   ├── .env                    ← Environment variables
│   ├── src/
│   │   ├── config/
│   │   │   ├── database.js     ← MongoDB connection
│   │   │   ├── firebase.js     ← Firebase Admin SDK
│   │   │   └── logger.js       ← Winston logger
│   │   ├── models/
│   │   │   ├── User.model.js           ← User schema
│   │   │   └── LoanVerification.model.js ← Core loan model
│   │   ├── middleware/
│   │   │   ├── authenticate.js  ← JWT auth guard
│   │   │   ├── authorize.js     ← Role-based access
│   │   │   ├── upload.js        ← Multer file upload
│   │   │   └── errorHandler.js  ← Global error handler
│   │   ├── controllers/
│   │   │   ├── auth.controller.js
│   │   │   ├── upload.controller.js
│   │   │   ├── verification.controller.js
│   │   │   ├── manager.controller.js
│   │   │   └── history.controller.js
│   │   ├── routes/
│   │   │   ├── auth.routes.js
│   │   │   ├── upload.routes.js
│   │   │   ├── verification.routes.js
│   │   │   ├── manager.routes.js
│   │   │   ├── history.routes.js
│   │   │   └── health.routes.js
│   │   └── services/
│   │       ├── token.service.js    ← JWT generation
│   │       └── ai.service.js       ← Python AI bridge
│   └── uploads/                ← Document storage
│
├── ai-service/                 ← Python FastAPI AI Service
│   ├── main.py                 ← FastAPI app entry point
│   ├── requirements.txt
│   ├── .env
│   └── app/
│       ├── ocr/
│       │   └── extractor.py    ← Tesseract + EasyOCR
│       ├── parser/
│       │   └── field_parser.py ← Regex field extraction
│       └── decision/
│           └── rule_engine.py  ← Loan approval logic
│
└── Verity_AI.postman_collection.json
```

---

## 🚀 Quick Start

### Prerequisites

| Tool | Version |
|------|---------|
| Node.js | ≥ 18.x |
| Python | ≥ 3.10 |
| MongoDB | ≥ 6.x (local or Atlas) |
| Tesseract OCR | Latest ([Install Guide](https://github.com/UB-Mannheim/tesseract/wiki)) |
| Poppler | Latest ([Windows](http://blog.alivate.com.au/poppler-windows/)) |

### 1️⃣ Start MongoDB

```bash
# Local MongoDB
mongod --dbpath C:/data/db

# Or use MongoDB Atlas (update MONGODB_URI in .env)
```

### 2️⃣ Start Node.js Backend

```bash
cd backend
npm install
npm run dev      # Development with hot-reload
# OR
npm start        # Production
```

Backend runs at: **http://localhost:5000**

### 3️⃣ Start Python AI Service

```bash
cd ai-service

# Create virtual environment
python -m venv venv
venv\Scripts\activate    # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Start service
python main.py
# OR with auto-reload
uvicorn main:app --reload --port 8000
```

AI Service runs at: **http://localhost:8000**
- Swagger docs: **http://localhost:8000/docs**

---

## 🔑 Environment Setup

### Backend (`backend/.env`)

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Express port | `5000` |
| `MONGODB_URI` | MongoDB connection string | `mongodb://localhost:27017/verity_ai` |
| `JWT_SECRET` | JWT signing secret (min 32 chars) | — |
| `JWT_EXPIRES_IN` | Token expiry | `7d` |
| `FIREBASE_PROJECT_ID` | Firebase project ID | — |
| `FIREBASE_PRIVATE_KEY` | Firebase service account key | — |
| `FIREBASE_CLIENT_EMAIL` | Firebase service account email | — |
| `PYTHON_AI_SERVICE_URL` | Python service URL | `http://localhost:8000` |
| `AI_SERVICE_API_KEY` | Shared secret for internal auth | — |

### AI Service (`ai-service/.env`)

| Variable | Description | Default |
|----------|-------------|---------|
| `OCR_PROVIDER` | `tesseract` / `easyocr` / `auto` | `auto` |
| `AI_SERVICE_API_KEY` | Must match backend | — |
| `TESSERACT_CMD` | Tesseract binary path (Windows) | Auto-detected |
| `POPPLER_PATH` | Poppler bin directory (Windows) | Auto-detected |

---

## 📡 API Reference

### Authentication

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/register` | — | Register with email/password |
| POST | `/api/auth/login` | — | Login, get JWT |
| POST | `/api/auth/google` | — | Login with Google Firebase token |
| GET | `/api/auth/me` | 🔒 JWT | Get logged-in user profile |
| PATCH | `/api/auth/me` | 🔒 JWT | Update profile |

### File Upload

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/upload` | 🔒 JWT | Upload documents (PDF/image) |
| GET | `/api/upload/:id` | 🔒 JWT | Poll processing status |

**Upload body (multipart/form-data):**
```
files      → one or more document files
loanType   → personal | home | auto | business | education
processNow → true | false
```

### Verification

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/verify` | 🔒 JWT | Run loan verification (stored or manual data) |
| POST | `/api/verify/quick-check` | 🔒 JWT | Quick rule check (no DB) |
| GET | `/api/verify/:id` | 🔒 JWT | Get full verification record |

**Quick check example:**
```json
{
  "loanType": "personal",
  "extractedData": {
    "creditScore": 720,
    "monthlyIncome": 45000,
    "age": 28,
    "workExperienceYears": 3,
    "debtToIncomeRatio": 0.30,
    "loanAmount": 500000
  }
}
```

**Response:**
```json
{
  "success": true,
  "recommendation": "approve",
  "approvalScore": 92,
  "summary": "All 5 mandatory criteria passed. Approval score: 92/100.",
  "ruleChecks": [
    {
      "rule": "creditScore >= 650",
      "description": "Minimum credit/CIBIL score of 650",
      "passed": true,
      "actualValue": 720,
      "expectedValue": "≥ 650",
      "category": "mandatory"
    }
    ...
  ]
}
```

### Manager APIs (Role: manager | admin)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/manager/stats` | Dashboard statistics |
| GET | `/api/manager/requests` | List all applications (paginated) |
| GET | `/api/manager/requests/:id` | Application details |
| POST | `/api/manager/approve` | Approve application |
| POST | `/api/manager/reject` | Reject with reason |
| POST | `/api/manager/request-more-info` | Request more documents |
| GET | `/api/manager/users` | List all users |

### History

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/history` | 🔒 JWT | Paginated application history |
| GET | `/api/history/:id` | 🔒 JWT | Single record detail |
| DELETE | `/api/history/:id` | 🔒 JWT | Cancel pending application |

---

## 🧠 Loan Decision Rules

### Personal Loan
| Rule | Threshold | Type |
|------|-----------|------|
| CIBIL/Credit Score | ≥ 650 | Mandatory |
| Monthly Income | ≥ ₹25,000 | Mandatory |
| Age | 21–60 years | Mandatory |
| Debt-to-Income Ratio | ≤ 50% | Mandatory |
| Work Experience | ≥ 1 year | Mandatory |
| Credit Score (bonus) | ≥ 750 | Preferred |
| Bounced Cheques | 0 | Preferred |

### Home Loan
| Rule | Threshold | Type |
|------|-----------|------|
| Credit Score | ≥ 700 | Mandatory |
| Annual Income | ≥ ₹3.6L | Mandatory |
| LTV Ratio | ≤ 80% | Mandatory |
| Work Experience | ≥ 2 years | Mandatory |
| Age | 21–65 years | Mandatory |

### Business Loan
| Rule | Threshold | Type |
|------|-----------|------|
| Credit Score | ≥ 680 | Mandatory |
| Annual Revenue | ≥ ₹6L | Mandatory |
| Business Age | ≥ 2 years | Mandatory |
| Avg Monthly Balance | ≥ ₹10,000 | Mandatory |

---

## 🔐 Security Features

- **JWT Authentication** with expiry & role payload
- **Firebase Admin SDK** for Google login verification
- **Role-based access control** (client / manager / admin)
- **Helmet.js** for HTTP security headers
- **Rate limiting** (100 req/15min per IP)
- **Multer file validation** (type + size)
- **Internal API key** between Node ↔ Python services
- **Input validation** with express-validator

---

## 🧪 Testing with Postman

1. Import `Verity_AI.postman_collection.json`
2. Register a user → Login → copy the `token`
3. Set `token` variable in Postman collection
4. Upload a document → copy `verificationId`
5. Run quick-check or verify

---

## 📦 Tech Stack

| Layer | Technology |
|-------|-----------|
| API Server | Node.js + Express |
| AI Service | Python + FastAPI |
| Database | MongoDB + Mongoose |
| OCR | Tesseract + EasyOCR |
| Auth | JWT + Firebase Admin |
| File Upload | Multer |
| HTTP Logging | Morgan + Winston |
| Security | Helmet + express-rate-limit |

---

## 🐛 Troubleshooting

**Tesseract not found:**
```
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
```

**PDF conversion fails (Poppler missing):**
```
POPPLER_PATH=C:\poppler\bin
```

**MongoDB connection error:**
- Ensure MongoDB is running: `mongod`
- Check `MONGODB_URI` in `.env`

**AI service unavailable:**
- The Node.js backend gracefully falls back to the local rule engine
- The `/api/verify/quick-check` endpoint never requires the AI service

---

## 📝 License

MIT © Verity AI 2024
