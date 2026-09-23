# College Complaint Management System
Full-stack Flask + SQLAlchemy + HTML/CSS/JS complaint portal.

## Run
python -m venv .venv
pip install -r backend/requirements.txt
python backend/app.py

Open http://127.0.0.1:5000

## Demo logins
Admin: admin1@mlgandhi.local / Admin@123
Admin: admin2@mlgandhi.local / Admin@123
Professor: professor@mlgandhi.local / Professor@123
Student: student@mlgandhi.local / Student@123

Database tables auto-create on first run. SQLite is the default; PostgreSQL works with DATABASE_URL.
For Netlify, deploy `frontend/` and put your deployed Flask API URL in `frontend/config.js`.


## Railway deployment

This project is Railway-ready.

1. Upload/push this complete project to GitHub.
2. Create a Railway project and deploy the GitHub repository.
3. Add a PostgreSQL database in Railway.
4. Railway provides `DATABASE_URL`; the Flask app reads it automatically.
5. Add `SECRET_KEY` as a Railway variable.
6. Deploy. The Flask backend serves the frontend as well.
7. Open the Railway public domain.

The database tables are automatically created on first startup.

### Demo accounts

Admin 1: `admin1@mlgandhi.local` / `Admin@123`  
Admin 2: `admin2@mlgandhi.local` / `Admin@123`  
Professor: `professor@mlgandhi.local` / `Professor@123`  
Student: `student@mlgandhi.local` / `Student@123`

Change demo credentials before real use.

### Optional Netlify frontend

If you later host only the frontend on Netlify, set the API base URL in `frontend/config.js` to the Railway public URL and configure `CORS_ORIGINS` accordingly.

## Final target: Railway only

Stack: Python + Flask + HTML + CSS + Vanilla JavaScript + SQLAlchemy + PostgreSQL.

There is NO Netlify requirement or configuration. Flask serves the frontend and backend from the same Railway service.

### Railway deployment
1. Push this project to GitHub.
2. Create a Railway project and deploy the repository.
3. Add a PostgreSQL service.
4. Add `SECRET_KEY` in Railway Variables.
5. Railway supplies `DATABASE_URL`.
6. Deploy using the included `railway.json`.
7. Open the generated Railway public domain.

### Credits
Aryan — Backend Developer — Roll Number 181
Savan — Frontend Developer — Roll Number 76

College: Shri M. L. Gandhi Higher Education Society, Modasa
Website: College Complaint Management System (CCMS)

~\ project by - FLOREX SIR 🥢 

FOR CONTACT TG :- @fizzxo 
GIT HUB :- @hereflorex

