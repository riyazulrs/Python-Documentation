from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from Database import SessionLocal, engine
from models import Employee, Post
import uuid
import os
import pandas as pd
import shutil

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

#Session helper function
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/upload_excel/")
async def upload_excel(file: UploadFile = File(...), db: Session = Depends(get_db)):
    file_extension = file.filename.split(".")[-1]
    if file_extension not in ["xlsx", "xls"]:
        raise HTTPException(status_code=400, detail="Only Excel files are allowed")

    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        xls = pd.ExcelFile(file_path, engine="openpyxl")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read Excel file: {str(e)}")

    #First sheet
    skipped_emails = []
    employee_count = 0

    try:
        df_employees = pd.read_excel(xls, sheet_name=0)
        required_columns_emp = {"First Name", "Last Name", "Email", "Department", "Salary", "DOJ", "Address"}
        if not required_columns_emp.issubset(df_employees.columns):
            raise Exception(f"Missing columns in Sheet1. Found: {list(df_employees.columns)}")

        for emp in df_employees.to_dict(orient="records"):
            existing_employee = db.query(Employee).filter(Employee.email == emp["Email"]).first()
            if existing_employee:
                skipped_emails.append(emp["Email"])
                continue

            emp_obj = Employee(
                first_name=emp["First Name"],
                last_name=emp["Last Name"],
                email=emp["Email"],
                department=emp["Department"],
                salary=float(emp["Salary"]),
                doj=pd.to_datetime(emp["DOJ"]).date() if pd.notna(emp["DOJ"]) else None,
                address=emp["Address"]
            )
            db.add(emp_obj)
            employee_count += 1

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing Sheet1: {str(e)}")

   #Next sheet
    experience_count = 0
    try:
        df_exp = pd.read_excel(xls, sheet_name=1)
        required_columns_exp = {"First Name", "Last Name", "Company", "Start date", "End Date"}
        if not required_columns_exp.issubset(df_exp.columns):
            raise Exception(f"Missing columns in Sheet2. Found: {list(df_exp.columns)}")

        for exp in df_exp.to_dict(orient="records"):
            exp_obj = Post(
                first_name=exp["First Name"],
                last_name=exp["Last Name"],
                company=exp["Company"],
                start_date=pd.to_datetime(exp["Start date"]).date() if pd.notna(exp["Start date"]) else None,
                end_date=pd.to_datetime(exp["End Date"]).date() if pd.notna(exp["End Date"]) else None
            )
            db.add(exp_obj)
            experience_count += 1

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing Sheet2: {str(e)}")

    db.commit()

    return {
        "filename": unique_filename,
        "message": "File uploaded. Employee and experience data saved to database!",
        "employees_saved": employee_count,
        "employees_skipped_due_to_duplicates": skipped_emails,
        "experiences_saved": experience_count
    }

from models import Base 

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(engine)
