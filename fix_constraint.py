from database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
db.execute(text("ALTER TABLE ventas DROP CONSTRAINT IF EXISTS ventas_estado_check;"))
db.execute(text("ALTER TABLE ventas ADD CONSTRAINT ventas_estado_check CHECK (estado IN ('COMPLETADA', 'ANULADA', 'FALLIDA', 'PENDIENTE', 'DEVUELTA', 'EN_DEVOLUCION'));"))
db.commit()
print("Constraint ventas_estado_check updated successfully!")
db.close()

