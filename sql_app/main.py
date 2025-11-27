from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional
from jose import JWTError, jwt
from datetime import datetime, timedelta

from . import crud, models, schemas
from .database import SessionLocal, engine

from datetime import date 

from fastapi.staticfiles import StaticFiles

# --- Auth Constants ---

SECRET_KEY = "YOUR_VERY_SECRET_KEY_GOES_HERE" # Change this!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
oauth2_scheme_mother = OAuth2PasswordBearer(tokenUrl="mother/token")
oauth2_scheme_moh = OAuth2PasswordBearer(tokenUrl="moh/token") # MOH Web Portal (NEW)

# --- Auth Functions (Same as before) ---
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- Dependency Functions (Updated) ---

async def get_current_midwife(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    # ... (Keep existing code) ...
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except JWTError:
        raise credentials_exception
    midwife = crud.get_midwife_by_username(db, username=token_data.username)
    if midwife is None:
        raise credentials_exception
    return midwife

async def get_current_mother(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme_mother)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        nic: str = payload.get("sub")
        if nic is None:
            raise credentials_exception
        token_data = schemas.TokenData(sub_id=nic)
    except JWTError:
        raise credentials_exception
    mother = crud.get_mother_by_nic(db, nic=token_data.sub_id)
    if mother is None:
        raise credentials_exception
    return mother

# --- NEW: MOH Auth Dependency ---
async def get_current_moh(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme_moh)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials (MOH)",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except JWTError:
        raise credentials_exception
    moh = crud.get_moh_officer_by_username(db, username=token_data.username)
    if moh is None:
        raise credentials_exception
    return moh


# --- API ENDPOINTS ---

# 1. MOH Self-Registration (For System Admin to create the first MOH account)
@app.post("/moh/register", response_model=schemas.MOHOfficer)
def register_moh(moh: schemas.MOHOfficerCreate, db: Session = Depends(get_db)):
    db_moh = crud.get_moh_officer_by_username(db, username=moh.username)
    if db_moh:
        raise HTTPException(status_code=400, detail="MOH Username already registered")
    return crud.create_moh_officer(db=db, moh=moh)

# 2. MOH Login (Web Login)
@app.post("/moh/token", response_model=schemas.Token)
async def login_for_moh(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    moh = crud.get_moh_officer_by_username(db, username=form_data.username)
    if not moh or not crud.verify_password(form_data.password, moh.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": moh.username})
    return {"access_token": access_token, "token_type": "bearer"}

# 3. Midwife Registration (Used by the MOH Web Form)
@app.post("/midwives/full", response_model=schemas.Midwife, status_code=status.HTTP_201_CREATED)
def register_new_midwife_from_web(
    midwife_data: schemas.MidwifeRegistration, 
    db: Session = Depends(get_db),
    # Ensure only a logged-in MOH can access this endpoint
    current_moh: schemas.MOHOfficer = Depends(get_current_moh) 
):
    db_midwife = crud.register_full_midwife(db=db, midwife_data=midwife_data)
    
    if db_midwife is None:
        raise HTTPException(status_code=400, detail="Username or NIC already exists.")
        
    return db_midwife

# 4. View All Midwives (For MOH Directory/Management)
@app.get("/midwives/", response_model=List[schemas.Midwife])
def get_all_midwives_for_moh(
    db: Session = Depends(get_db),
    current_moh: schemas.MOHOfficer = Depends(get_current_moh)
):
    # Currently returns all midwives; can be filtered by moh_area if needed later
    return db.query(models.Midwife).all()



# ... (Register and Login endpoints stay the same) ...
@app.post("/register/", response_model=schemas.Midwife)
def register_midwife(midwife: schemas.MidwifeCreate, db: Session = Depends(get_db)):
    db_midwife = crud.get_midwife_by_username(db, username=midwife.username)
    if db_midwife:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_midwife(db=db, midwife=midwife)

@app.post("/token", response_model=schemas.Token)
async def login_for_midwife(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    midwife = crud.get_midwife_by_username(db, username=form_data.username)
    if not midwife or not crud.verify_password(form_data.password, midwife.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": midwife.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/midwives/me/", response_model=schemas.Midwife)
async def read_midwives_me(current_midwife: schemas.Midwife = Depends(get_current_midwife)):
    return current_midwife

@app.post("/mother/token", response_model=schemas.Token)
async def login_for_mother(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    mother = crud.get_mother_by_nic(db, nic=form_data.username)
    if not mother or not crud.verify_password(form_data.password, mother.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect NIC or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": mother.nic})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/mothers/me/", response_model=schemas.Mother)
async def read_mothers_me(current_mother: schemas.Mother = Depends(get_current_mother)):
    return current_mother

# --- MIDWIFE ACTIONS (UPDATED) ---

@app.post("/mothers/", response_model=schemas.Mother)
def create_mother_for_midwife(
    mother: schemas.MotherCreate, 
    db: Session = Depends(get_db), 
    current_midwife: schemas.Midwife = Depends(get_current_midwife)
):
    db_mother = crud.get_mother_by_nic(db, nic=mother.nic)
    if db_mother:
        raise HTTPException(status_code=400, detail="Mother with this NIC already registered")
    return crud.create_mother(db=db, mother=mother, midwife_id=current_midwife.id)

# UPDATED: Accepts 'search' parameter
@app.get("/mothers/", response_model=List[schemas.Mother])
def read_mothers_for_midwife(
    skip: int = 0, 
    limit: int = 100, 
    search: Optional[str] = None, # New parameter
    db: Session = Depends(get_db),
    current_midwife: schemas.Midwife = Depends(get_current_midwife)
):
    mothers = crud.get_mothers_by_midwife(db, midwife_id=current_midwife.id, skip=skip, limit=limit, search=search)
    return mothers

# NEW: Update Mother Details
@app.put("/mothers/{mother_id}", response_model=schemas.Mother)
def update_mother_details(
    mother_id: int,
    mother_update: schemas.MotherUpdate,
    db: Session = Depends(get_db),
    current_midwife: schemas.Midwife = Depends(get_current_midwife)
):
    # 1. Check if mother exists
    db_mother = crud.get_mother(db, mother_id=mother_id)
    if not db_mother:
        raise HTTPException(status_code=404, detail="Mother not found")
        
    # 2. Security Check: Ensure this mother belongs to this midwife
    if db_mother.midwife_id != current_midwife.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this mother")
        
    # 3. Update
    return crud.update_mother(db=db, mother_id=mother_id, mother_update=mother_update)

@app.post("/mothers/{mother_id}/records/", response_model=schemas.HealthRecord)
def create_record_for_mother(
    mother_id: int,
    record: schemas.HealthRecordCreate,
    db: Session = Depends(get_db),
    current_midwife: schemas.Midwife = Depends(get_current_midwife)
):
    return crud.create_health_record(db=db, record=record, mother_id=mother_id)

@app.get("/mothers/{mother_id}/records/", response_model=List[schemas.HealthRecord])
def read_records_for_mother(
    mother_id: int,
    db: Session = Depends(get_db),
    current_midwife: schemas.Midwife = Depends(get_current_midwife)
):
    records = crud.get_health_records_for_mother(db, mother_id=mother_id)
    return records
            
# --- PREGNANCY RECORD ENDPOINTS ---

@app.post("/mothers/{mother_id}/pregnancy-records/", response_model=schemas.PregnancyRecord)
def create_pregnancy_record_for_mother(
    mother_id: int,
    record: schemas.PregnancyRecordCreate,
    db: Session = Depends(get_db),
    current_midwife: schemas.Midwife = Depends(get_current_midwife)
):
    # Check if mother exists
    db_mother = crud.get_mother(db, mother_id=mother_id)
    if not db_mother:
        raise HTTPException(status_code=404, detail="Mother not found")
        
    return crud.create_pregnancy_record(db=db, record=record, mother_id=mother_id)

@app.get("/mothers/{mother_id}/pregnancy-records/", response_model=List[schemas.PregnancyRecord])
def read_pregnancy_records_for_mother(
    mother_id: int,
    db: Session = Depends(get_db),
    current_midwife: schemas.Midwife = Depends(get_current_midwife)
):
    return crud.get_pregnancy_records_for_mother(db, mother_id=mother_id)

# --- DELIVERY RECORD ENDPOINTS ---

@app.post("/mothers/{mother_id}/delivery-records/", response_model=schemas.DeliveryRecord)
def create_delivery_record_for_mother(
    mother_id: int,
    record: schemas.DeliveryRecordCreate,
    db: Session = Depends(get_db),
    current_midwife: schemas.Midwife = Depends(get_current_midwife)
):
    # Check if mother exists
    db_mother = crud.get_mother(db, mother_id=mother_id)
    if not db_mother:
        raise HTTPException(status_code=404, detail="Mother not found")
        
    return crud.create_delivery_record(db=db, record=record, mother_id=mother_id)

@app.get("/mothers/{mother_id}/delivery-records/", response_model=List[schemas.DeliveryRecord])
def read_delivery_records_for_mother(
    mother_id: int,
    db: Session = Depends(get_db),
    current_midwife: schemas.Midwife = Depends(get_current_midwife)
):
    return crud.get_delivery_records_for_mother(db, mother_id=mother_id)

# --- ANTENATAL PLAN ENDPOINTS ---

@app.post("/mothers/{mother_id}/antenatal-plans/", response_model=schemas.AntenatalPlan)
def create_antenatal_plan_for_mother(
    mother_id: int,
    plan: schemas.AntenatalPlanCreate,
    db: Session = Depends(get_db),
    current_midwife: schemas.Midwife = Depends(get_current_midwife)
):
    # Check if mother exists
    db_mother = crud.get_mother(db, mother_id=mother_id)
    if not db_mother:
        raise HTTPException(status_code=404, detail="Mother not found")
        
    return crud.create_antenatal_plan(db=db, plan=plan, mother_id=mother_id)

@app.get("/mothers/{mother_id}/antenatal-plans/", response_model=List[schemas.AntenatalPlan])
def read_antenatal_plans_for_mother(
    mother_id: int,
    db: Session = Depends(get_db),
    current_midwife: schemas.Midwife = Depends(get_current_midwife)
):
    return crud.get_antenatal_plans_for_mother(db, mother_id=mother_id)

# --- MOTHER PORTAL ENDPOINTS (READ-ONLY) ---

@app.get("/my-pregnancy-records/", response_model=List[schemas.PregnancyRecord])
def read_my_pregnancy_records(
    db: Session = Depends(get_db),
    current_mother: schemas.Mother = Depends(get_current_mother)
):
    # The 'current_mother' dependency ensures this is a valid mother login
    return crud.get_pregnancy_records_for_mother(db, mother_id=current_mother.id)

@app.get("/my-delivery-records/", response_model=List[schemas.DeliveryRecord])
def read_my_delivery_records(
    db: Session = Depends(get_db),
    current_mother: schemas.Mother = Depends(get_current_mother)
):
    return crud.get_delivery_records_for_mother(db, mother_id=current_mother.id)

@app.get("/my-antenatal-plans/", response_model=List[schemas.AntenatalPlan])
def read_my_antenatal_plans(
    db: Session = Depends(get_db),
    current_mother: schemas.Mother = Depends(get_current_mother)
):
    return crud.get_antenatal_plans_for_mother(db, mother_id=current_mother.id)
            
# --- MOTHER PASSWORD CHANGE ---

@app.put("/mothers/me/password", response_model=dict)
def change_mother_password(
    password_data: schemas.PasswordChange,
    db: Session = Depends(get_db),
    current_mother: schemas.Mother = Depends(get_current_mother)
):
    success = crud.update_mother_password(db, mother_id=current_mother.id, password_data=password_data)
    if not success:
        raise HTTPException(status_code=400, detail="Incorrect old password")
        
    return {"message": "Password updated successfully"}

# new section added for the web ---

# This tells FastAPI: "If someone goes to http://localhost:8000/static/login.html, show them that file."
app.mount("/static", StaticFiles(directory="static"), name="static")