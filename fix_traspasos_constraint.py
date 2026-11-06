from database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
db.execute(text("ALTER TABLE traspasos DROP CONSTRAINT IF EXISTS traspasos_estado_check;"))
db.execute(text("ALTER TABLE traspasos ADD CONSTRAINT traspasos_estado_check CHECK (estado IN ('SOLICITADO', 'PENDIENTE', 'EN_TRANSITO', 'RECIBIDO', 'RECEPCIONADO', 'CANCELADO'));"))
db.commit()
print("Constraint traspasos_estado_check actualizada exitosamente!")
db.close()

