
import os
from datetime import datetime, timezone
from functools import wraps
from dotenv import load_dotenv
from flask import Flask, jsonify, request, session, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONT=os.path.join(BASE,"frontend")
app=Flask(__name__,static_folder=FRONT,static_url_path="")
app.config["SECRET_KEY"]=os.getenv("SECRET_KEY","change-me")
url=os.getenv("DATABASE_URL","sqlite:///complaint_portal.db")
if url.startswith("postgres://"): url=url.replace("postgres://","postgresql://",1)
app.config["SQLALCHEMY_DATABASE_URI"]=url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"]=False
CORS(app,supports_credentials=True,origins=os.getenv("CORS_ORIGINS","*").split(","))
db=SQLAlchemy(app)
def now(): return datetime.now(timezone.utc)

class User(db.Model):
 id=db.Column(db.Integer,primary_key=True); name=db.Column(db.String(120),nullable=False)
 email=db.Column(db.String(180),unique=True,nullable=False); password_hash=db.Column(db.String(255),nullable=False)
 role=db.Column(db.String(30),default="student",nullable=False); roll_number=db.Column(db.String(50))
 class_name=db.Column(db.String(100)); department=db.Column(db.String(120)); created_at=db.Column(db.DateTime(timezone=True),default=now)
 def public(self): return {"id":self.id,"name":self.name,"email":self.email,"role":self.role,"roll_number":self.roll_number,"class_name":self.class_name,"department":self.department}

class Complaint(db.Model):
 id=db.Column(db.Integer,primary_key=True); title=db.Column(db.String(180),nullable=False); description=db.Column(db.Text,nullable=False)
 category=db.Column(db.String(80),nullable=False); status=db.Column(db.String(40),default="Pending",nullable=False)
 student_id=db.Column(db.Integer,db.ForeignKey("user.id"),nullable=False); professor_id=db.Column(db.Integer,db.ForeignKey("user.id"))
 resolution_note=db.Column(db.Text); student_feedback=db.Column(db.String(40)); created_at=db.Column(db.DateTime(timezone=True),default=now); updated_at=db.Column(db.DateTime(timezone=True),default=now,onupdate=now)
 student=db.relationship("User",foreign_keys=[student_id]); professor=db.relationship("User",foreign_keys=[professor_id])
 def public(self): return {"id":self.id,"title":self.title,"description":self.description,"category":self.category,"status":self.status,"student":self.student.public(),"professor":self.professor.public() if self.professor else None,"resolution_note":self.resolution_note,"student_feedback":self.student_feedback,"created_at":self.created_at.isoformat(),"updated_at":self.updated_at.isoformat()}

class ComplaintUpdate(db.Model):
 id=db.Column(db.Integer,primary_key=True); complaint_id=db.Column(db.Integer,db.ForeignKey("complaint.id"),nullable=False); actor_id=db.Column(db.Integer,db.ForeignKey("user.id"),nullable=False)
 status=db.Column(db.String(40),nullable=False); note=db.Column(db.Text); created_at=db.Column(db.DateTime(timezone=True),default=now)
 actor=db.relationship("User")

class Notice(db.Model):
 id=db.Column(db.Integer,primary_key=True); title=db.Column(db.String(180),nullable=False); content=db.Column(db.Text,nullable=False); priority=db.Column(db.String(30),default="Normal")
 author_id=db.Column(db.Integer,db.ForeignKey("user.id")); created_at=db.Column(db.DateTime(timezone=True),default=now); author=db.relationship("User")
 def public(self): return {"id":self.id,"title":self.title,"content":self.content,"priority":self.priority,"author":self.author.name if self.author else "Admin","created_at":self.created_at.isoformat()}

def me(): return db.session.get(User,session.get("user_id")) if session.get("user_id") else None
def required(fn):
 @wraps(fn)
 def w(*a,**k):
  if not me(): return jsonify(error="Login required"),401
  return fn(*a,**k)
 return w
def roles(*rs):
 def d(fn):
  @wraps(fn)
  def w(*a,**k):
   u=me()
   if not u:return jsonify(error="Login required"),401
   if u.role not in rs:return jsonify(error="Permission denied"),403
   return fn(*a,**k)
  return w
 return d
def addlog(c,u,status,note=""): db.session.add(ComplaintUpdate(complaint_id=c.id,actor_id=u.id,status=status,note=note or None))

@app.get("/api/health")
def health(): return jsonify(ok=True)

@app.post("/api/auth/register")
def register():
 d=request.get_json() or {}; email=(d.get("email") or "").strip().lower(); pw=d.get("password") or ""
 if not d.get("name") or not email or len(pw)<6:return jsonify(error="Name, email and 6+ character password required"),400
 if db.session.scalar(db.select(User).filter_by(email=email)):return jsonify(error="Email already registered"),409
 u=User(name=d["name"].strip(),email=email,password_hash=generate_password_hash(pw),role="student",roll_number=d.get("roll_number"),class_name=d.get("class_name"),department=d.get("department"))
 db.session.add(u);db.session.commit();session["user_id"]=u.id;return jsonify(user=u.public()),201

@app.post("/api/auth/login")
def login():
 d=request.get_json() or {};u=db.session.scalar(db.select(User).filter_by(email=(d.get("email") or "").strip().lower()))
 if not u or not check_password_hash(u.password_hash,d.get("password") or ""):return jsonify(error="Invalid email or password"),401
 session["user_id"]=u.id;return jsonify(user=u.public())
@app.post("/api/auth/logout")
def logout():session.clear();return jsonify(ok=True)
@app.get("/api/auth/me")
def authme():return jsonify(user=me().public() if me() else None)

@app.get("/api/notices")
def get_notices():return jsonify(notices=[n.public() for n in db.session.scalars(db.select(Notice).order_by(Notice.created_at.desc())).all()])
@app.post("/api/notices")
@roles("admin")
def create_notice():
 d=request.get_json() or {};n=Notice(title=d.get("title","").strip(),content=d.get("content","").strip(),priority=d.get("priority","Normal"),author_id=me().id)
 if not n.title or not n.content:return jsonify(error="Title and content required"),400
 db.session.add(n);db.session.commit();return jsonify(notice=n.public()),201
@app.delete("/api/notices/<int:i>")
@roles("admin")
def del_notice(i):
 n=db.session.get(Notice,i)
 if not n:return jsonify(error="Not found"),404
 db.session.delete(n);db.session.commit();return jsonify(ok=True)

@app.get("/api/complaints")
@required
def get_complaints():
 u=me();q=db.select(Complaint).order_by(Complaint.created_at.desc())
 if u.role=="student":q=q.filter(Complaint.student_id==u.id)
 elif u.role=="professor":q=q.filter((Complaint.professor_id==u.id)|(Complaint.professor_id.is_(None)))
 return jsonify(complaints=[c.public() for c in db.session.scalars(q).all()])
@app.post("/api/complaints")
@roles("student")
def create_complaint():
 d=request.get_json() or {}
 if not d.get("title") or not d.get("description"):return jsonify(error="Title and description required"),400
 c=Complaint(title=d["title"].strip(),description=d["description"].strip(),category=d.get("category","General"),student_id=me().id)
 db.session.add(c);db.session.flush();addlog(c,me(),"Pending","Complaint submitted by student.");db.session.commit();return jsonify(complaint=c.public()),201

@app.patch("/api/complaints/<int:i>")
@required
def update_complaint(i):
 c=db.session.get(Complaint,i);u=me();d=request.get_json() or {}
 if not c:return jsonify(error="Not found"),404
 if u.role=="student":
  if c.student_id!=u.id:return jsonify(error="Forbidden"),403
  f=d.get("student_feedback")
  if f not in ("Resolved","Not Resolved"):return jsonify(error="Invalid feedback"),400
  c.student_feedback=f;c.status="Closed" if f=="Resolved" else "Reopened";addlog(c,u,c.status,"Student confirmed resolution." if f=="Resolved" else "Student reported issue is still unresolved.")
 elif u.role in ("professor","admin"):
  if u.role=="admin" and "professor_id" in d:c.professor_id=int(d["professor_id"]) if d["professor_id"] else None
  if d.get("status") in ("Pending","In Progress","Resolved","Rejected","Reopened","Closed"):c.status=d["status"]
  if "resolution_note" in d:c.resolution_note=d["resolution_note"]
  addlog(c,u,c.status,c.resolution_note or "Status updated.")
 else:return jsonify(error="Forbidden"),403
 db.session.commit();return jsonify(complaint=c.public())

@app.get("/api/complaints/<int:i>/history")
@required
def history(i):
 c=db.session.get(Complaint,i);u=me()
 if not c:return jsonify(error="Not found"),404
 if u.role=="student" and c.student_id!=u.id:return jsonify(error="Forbidden"),403
 if u.role=="professor" and c.professor_id not in (None,u.id):return jsonify(error="Forbidden"),403
 rows=db.session.scalars(db.select(ComplaintUpdate).filter_by(complaint_id=i).order_by(ComplaintUpdate.created_at)).all()
 return jsonify(history=[{"id":x.id,"status":x.status,"note":x.note,"actor":x.actor.name,"created_at":x.created_at.isoformat()} for x in rows])

@app.get("/api/professors")
@required
def professors():return jsonify(professors=[u.public() for u in db.session.scalars(db.select(User).filter_by(role="professor")).all()])
@app.get("/api/users")
@roles("admin")
def users():return jsonify(users=[u.public() for u in db.session.scalars(db.select(User).order_by(User.created_at.desc())).all()])
@app.patch("/api/users/<int:i>")
@roles("admin")
def edit_user(i):
 u=db.session.get(User,i);d=request.get_json() or {}
 if not u:return jsonify(error="Not found"),404
 if d.get("role") in ("student","professor","admin"):u.role=d["role"]
 if d.get("name"):u.name=d["name"]
 db.session.commit();return jsonify(user=u.public())
@app.delete("/api/users/<int:i>")
@roles("admin")
def del_user(i):
 u=db.session.get(User,i)
 if not u:return jsonify(error="Not found"),404
 if u.id==me().id:return jsonify(error="Cannot delete yourself"),400
 db.session.delete(u);db.session.commit();return jsonify(ok=True)
@app.get("/api/admin/stats")
@roles("admin")
def stats():
 count=lambda f:db.session.scalar(db.select(db.func.count(Complaint.id)).filter(f)) or 0
 return jsonify(complaints=db.session.scalar(db.select(db.func.count(Complaint.id))) or 0,pending=count(Complaint.status=="Pending"),in_progress=count(Complaint.status=="In Progress"),resolved=count(Complaint.status.in_(["Resolved","Closed"])),students=db.session.scalar(db.select(db.func.count(User.id)).filter(User.role=="student")) or 0,professors=db.session.scalar(db.select(db.func.count(User.id)).filter(User.role=="professor")) or 0)

@app.get("/api/about")
def about():return jsonify(system="College Complaint Management System",college="Shri M. L. Gandhi Higher Education Society, Modasa",developers=[{"name":"Aryan","role":"Backend Developer","roll_number":"181"},{"name":"Savan","role":"Frontend Developer","roll_number":"76"}])

@app.route("/",defaults={"path":""})
@app.route("/<path:path>")
def frontend(path):
 p=os.path.join(FRONT,path)
 if path and os.path.isfile(p):return send_from_directory(FRONT,path)
 return send_from_directory(FRONT,"index.html")

with app.app_context():
 db.create_all()
 if not db.session.scalar(db.select(User.id).limit(1)):
  a=User(name="Aryan Admin",email="admin1@mlgandhi.local",password_hash=generate_password_hash("Admin@123"),role="admin")
  b=User(name="Savan Admin",email="admin2@mlgandhi.local",password_hash=generate_password_hash("Admin@123"),role="admin")
  p=User(name="Demo Professor",email="professor@mlgandhi.local",password_hash=generate_password_hash("Professor@123"),role="professor")
  s=User(name="Demo Student",email="student@mlgandhi.local",password_hash=generate_password_hash("Student@123"),role="student",roll_number="STU001",class_name="BCA Sem 5",department="Computer Applications")
  db.session.add_all([a,b,p,s]);db.session.flush()
  db.session.add(Notice(title="Welcome to College Complaint Management System",content="Students can report campus problems here and track their resolution.",priority="High",author_id=a.id));db.session.commit()

if __name__=="__main__":app.run(host="0.0.0.0",port=int(os.getenv("PORT","5000")),debug=True)
