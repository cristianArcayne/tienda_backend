from database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
q = "SELECT pg_get_constraintdef(c.oid) FROM pg_constraint c JOIN pg_class t ON c.conrelid = t.oid WHERE t.relname = 'traspasos' AND c.conname = 'traspasos_estado_check';"
res = db.execute(text(q)).fetchall()
print("Constraint actual:", res)
db.close()

