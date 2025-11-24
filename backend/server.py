from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import jwt
from passlib.context import CryptContext
import pandas as pd
import io
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pytz

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"

# Scheduler
scheduler = AsyncIOScheduler(timezone=pytz.UTC)

# --- Models ---
class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: EmailStr
    phone: Optional[str] = None
    role: str = "staff"  # "admin" or "staff"
    timezone: str = "UTC"
    preferences: Dict[str, Any] = Field(default_factory=lambda: {
        "lead_time_minutes": 15,
        "channels": {"email": True, "sms": False, "push": False},
        "quiet_hours": {"enabled": False, "start": "22:00", "end": "07:00"}
    })
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None
    role: str = "staff"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Class(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    room: str
    teacher_email: EmailStr
    start_datetime: datetime
    end_datetime: datetime
    recurrence: str = "ONCE"  # ONCE, WEEKLY, ODD_WEEKS, EVEN_WEEKS
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Reminder(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    class_id: str
    user_id: str
    scheduled_time: datetime
    status: str = "pending"  # pending, sent, failed
    channel: str = "email"
    sent_at: Optional[datetime] = None
    error: Optional[str] = None

class PreferencesUpdate(BaseModel):
    lead_time_minutes: Optional[int] = None
    channels: Optional[Dict[str, bool]] = None
    quiet_hours: Optional[Dict[str, Any]] = None

# --- Helper Functions ---
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_token(user_id: str, email: str, role: str) -> str:
    payload = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(days=7)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user = await db.users.find_one({"id": payload["user_id"]}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return User(**user)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")

async def send_email_reminder(to_email: str, class_info: Dict):
    """Send email reminder"""
    try:
        smtp_host = os.environ.get("SMTP_HOST")
        smtp_port = int(os.environ.get("SMTP_PORT", 587))
        smtp_user = os.environ.get("SMTP_USER")
        smtp_pass = os.environ.get("SMTP_PASS")
        
        if not all([smtp_host, smtp_user, smtp_pass]):
            logging.warning("SMTP not configured, skipping email")
            return False
        
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = to_email
        msg['Subject'] = f"Class Reminder: {class_info['title']}"
        
        body = f"""
        <html>
        <body>
            <h2>Class Reminder</h2>
            <p><strong>Class:</strong> {class_info['title']}</p>
            <p><strong>Room:</strong> {class_info['room']}</p>
            <p><strong>Time:</strong> {class_info['start_datetime'].strftime('%Y-%m-%d %H:%M')}</p>
            <p>This class will start in {class_info.get('lead_time', 15)} minutes.</p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        
        return True
    except Exception as e:
        logging.error(f"Email send failed: {str(e)}")
        return False

async def process_reminders():
    """Background job to check and send reminders"""
    try:
        now = datetime.now(timezone.utc)
        # Get pending reminders that should be sent now
        reminders = await db.reminders.find({
            "status": "pending",
            "scheduled_time": {"$lte": now}
        }, {"_id": 0}).to_list(100)
        
        for reminder in reminders:
            # Get class info
            class_info = await db.classes.find_one({"id": reminder["class_id"]}, {"_id": 0})
            if not class_info:
                continue
            
            # Get user info
            user = await db.users.find_one({"id": reminder["user_id"]}, {"_id": 0})
            if not user:
                continue
            
            # Send reminder
            success = False
            if reminder["channel"] == "email":
                class_info['lead_time'] = user.get('preferences', {}).get('lead_time_minutes', 15)
                success = await send_email_reminder(user["email"], class_info)
            
            # Update reminder status
            await db.reminders.update_one(
                {"id": reminder["id"]},
                {"$set": {
                    "status": "sent" if success else "failed",
                    "sent_at": datetime.now(timezone.utc).isoformat(),
                    "error": None if success else "Failed to send"
                }}
            )
            
            # Log
            await db.logs.insert_one({
                "id": str(uuid.uuid4()),
                "reminder_id": reminder["id"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "sent" if success else "failed",
                "response": "Email sent" if success else "Failed to send"
            })
    except Exception as e:
        logging.error(f"Reminder processing error: {str(e)}")

async def schedule_class_reminders(class_obj: Dict):
    """Schedule reminders for a class"""
    try:
        # Find all users with matching email
        users = await db.users.find({"email": class_obj["teacher_email"]}, {"_id": 0}).to_list(10)
        
        for user in users:
            prefs = user.get("preferences", {})
            lead_time = prefs.get("lead_time_minutes", 15)
            channels = prefs.get("channels", {"email": True})
            
            # Calculate reminder time
            if isinstance(class_obj["start_datetime"], str):
                start_time = datetime.fromisoformat(class_obj["start_datetime"].replace('Z', '+00:00'))
            else:
                start_time = class_obj["start_datetime"]
            
            reminder_time = start_time - timedelta(minutes=lead_time)
            
            # Only schedule future reminders
            if reminder_time > datetime.now(timezone.utc):
                for channel, enabled in channels.items():
                    if enabled and channel == "email":  # Currently only email supported
                        reminder = {
                            "id": str(uuid.uuid4()),
                            "class_id": class_obj["id"],
                            "user_id": user["id"],
                            "scheduled_time": reminder_time.isoformat(),
                            "status": "pending",
                            "channel": channel,
                            "sent_at": None,
                            "error": None
                        }
                        await db.reminders.insert_one(reminder)
    except Exception as e:
        logging.error(f"Schedule reminder error: {str(e)}")

# --- Auth Routes ---
@api_router.post("/auth/register")
async def register(user_data: UserCreate):
    # Check if user exists
    existing = await db.users.find_one({"email": user_data.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password and create user
    hashed_pw = hash_password(user_data.password)
    user = User(
        name=user_data.name,
        email=user_data.email,
        phone=user_data.phone,
        role=user_data.role
    )
    
    user_dict = user.model_dump()
    user_dict["password"] = hashed_pw
    user_dict["created_at"] = user_dict["created_at"].isoformat()
    
    await db.users.insert_one(user_dict)
    
    token = create_token(user.id, user.email, user.role)
    return {"token": token, "user": user.model_dump()}

@api_router.post("/auth/login")
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user or not verify_password(credentials.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user["id"], user["email"], user["role"])
    user_data = User(**user)
    return {"token": token, "user": user_data.model_dump()}

@api_router.get("/auth/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

# --- Admin Routes ---
@api_router.post("/admin/timetables/upload")
async def upload_timetable(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        contents = await file.read()
        
        # Parse CSV or Excel
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(contents))
        else:
            raise HTTPException(status_code=400, detail="Only CSV and Excel files supported")
        
        # Validate columns
        required_cols = ['class_title', 'room', 'teacher_email', 'start_datetime', 'end_datetime']
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            raise HTTPException(status_code=400, detail=f"Missing columns: {missing}")
        
        # Create classes
        classes_created = 0
        for _, row in df.iterrows():
            class_obj = Class(
                title=row['class_title'],
                room=row['room'],
                teacher_email=row['teacher_email'],
                start_datetime=pd.to_datetime(row['start_datetime']),
                end_datetime=pd.to_datetime(row['end_datetime']),
                recurrence=row.get('recurrence', 'ONCE')
            )
            
            class_dict = class_obj.model_dump()
            class_dict["start_datetime"] = class_dict["start_datetime"].isoformat()
            class_dict["end_datetime"] = class_dict["end_datetime"].isoformat()
            class_dict["created_at"] = class_dict["created_at"].isoformat()
            
            await db.classes.insert_one(class_dict)
            
            # Schedule reminders
            await schedule_class_reminders(class_dict)
            
            classes_created += 1
        
        return {"success": True, "classes_created": classes_created}
    except Exception as e:
        logging.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/admin/classes")
async def create_class(class_data: Class, current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    class_dict = class_data.model_dump()
    class_dict["start_datetime"] = class_dict["start_datetime"].isoformat()
    class_dict["end_datetime"] = class_dict["end_datetime"].isoformat()
    class_dict["created_at"] = class_dict["created_at"].isoformat()
    
    await db.classes.insert_one(class_dict)
    await schedule_class_reminders(class_dict)
    
    return {"success": True, "class": class_data.model_dump()}

@api_router.get("/admin/upcoming")
async def get_upcoming_classes(hours: int = 24, current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    now = datetime.now(timezone.utc)
    future = now + timedelta(hours=hours)
    
    classes = await db.classes.find({
        "start_datetime": {"$gte": now.isoformat(), "$lte": future.isoformat()}
    }, {"_id": 0}).to_list(1000)
    
    return classes

@api_router.get("/admin/logs")
async def get_logs(limit: int = 100, current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    logs = await db.logs.find({}, {"_id": 0}).sort("timestamp", -1).to_list(limit)
    return logs

@api_router.post("/admin/test-reminder")
async def test_reminder(user_email: str, current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    test_class = {
        "title": "Test Class",
        "room": "Test Room",
        "start_datetime": datetime.now(timezone.utc) + timedelta(minutes=15),
        "lead_time": 15
    }
    
    success = await send_email_reminder(user_email, test_class)
    return {"success": success}

@api_router.get("/admin/users")
async def get_all_users(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    users = await db.users.find({}, {"_id": 0, "password": 0}).to_list(1000)
    return users

# --- Staff Routes ---
@api_router.get("/users/me/timetable")
async def get_my_timetable(current_user: User = Depends(get_current_user)):
    classes = await db.classes.find(
        {"teacher_email": current_user.email},
        {"_id": 0}
    ).to_list(1000)
    return classes

@api_router.put("/users/me/preferences")
async def update_preferences(prefs: PreferencesUpdate, current_user: User = Depends(get_current_user)):
    update_data = {}
    if prefs.lead_time_minutes is not None:
        update_data["preferences.lead_time_minutes"] = prefs.lead_time_minutes
    if prefs.channels is not None:
        update_data["preferences.channels"] = prefs.channels
    if prefs.quiet_hours is not None:
        update_data["preferences.quiet_hours"] = prefs.quiet_hours
    
    await db.users.update_one(
        {"id": current_user.id},
        {"$set": update_data}
    )
    
    return {"success": True}

@api_router.get("/users/me/classes")
async def get_my_upcoming_classes(days: int = 7, current_user: User = Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    future = now + timedelta(days=days)
    
    classes = await db.classes.find({
        "teacher_email": current_user.email,
        "start_datetime": {"$gte": now.isoformat(), "$lte": future.isoformat()}
    }, {"_id": 0}).to_list(1000)
    
    return classes

# --- Health Check ---
@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "scheduler": scheduler.running}

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    # Start scheduler
    scheduler.add_job(process_reminders, 'interval', minutes=5)
    scheduler.start()
    logger.info("Scheduler started")

@app.on_event("shutdown")
async def shutdown_db_client():
    scheduler.shutdown()
    client.close()
