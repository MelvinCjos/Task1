from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models import Base, User, Profile
from mongo_models import profile_picture_collection
import motor.motor_asyncio
from bson import ObjectId
import base64
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from pydantic import BaseModel, EmailStr

# Correct the URL format if needed
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:Melvin%40123@localhost/task_db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

app = FastAPI()
templates = Jinja2Templates(directory="templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)  # Added @ before app.get
async def get_register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.post("/register/")
async def register_user(full_name: str = Form(...), email: str = Form(...), 
                        password: str = Form(...), phone: str = Form(...),
                        profile_picture: UploadFile = File(...), db: Session = Depends(get_db)):
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create new user in PostgreSQL
    new_user = User(email=email, password=password, full_name=full_name, phone=phone)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Save profile picture in MongoDB
    pic_data = await profile_picture.read()
    profile_pic_id = profile_picture_collection.insert_one({"picture": pic_data}).inserted_id

    # Return success response
    return {"user_id": new_user.id, "message": "User registered successfully"}

class YourResponseModel(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    profile_picture: bytes | None  # Assuming you'll return the URL or path of the picture

@app.get("/users/{user_id}", response_model=YourResponseModel)  # Define YourResponseModel as per your requirement
async def get_user(user_id: int, db: Session = Depends(get_db)):
    # Fetch user from PostgreSQL
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Fetch profile picture from MongoDB (assuming the profile picture is stored with a reference to the user_id)
    profile_picture_data = await profile_picture_collection.find_one({"user_id": user_id})

    # Prepare your response object. This might include transforming the data into a suitable format.
    response = {
        "full_name": user.full_name,
        "email": user.email,
        "phone": user.phone,
        "profile_picture": profile_picture_data.get("picture") if profile_picture_data else None
    }

    return response
