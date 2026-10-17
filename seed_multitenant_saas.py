"""
Script de Población y Migración SaaS Multitenant para FashionStore.
Crea las tablas de Empresas, Planes y Suscripciones en PostgreSQL,
y siembra las 2 Empresas de Prueba Independientes requeridas por la docente.
"""
from datetime import datetime, timedelta
from database import engine, SessionLocal, Base
from models import (
    Empresa,
    PlanSuscripcion,
    SuscripcionEmpresa,
    HistorialCambioPlan,
    Sucursal,
    Ropa,
    Usuario,
    Venta,
    Reserva
)


def poblar_saas_multitenant():
    print("=" * 70)
    print("INICIANDO MIGRACIÓN Y POBLACIÓN SAAS MULTITENANT - FASHIONSTORE")
    print("=" * 70)

    # 1. Crear tablas en la base de datos si no existen
    Base.metadata.create_all(bind=engine)
    print("-> Tablas de base de datos verificadas/creadas exitosamente.")

    # 1.1 Migrar tablas existentes agregando la columna empresa_id si no existe
    from sqlalchemy import text
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE sucursales ADD COLUMN IF NOT EXISTS empresa_id INT REFERENCES empresas(id) ON DELETE CASCADE DEFAULT 1;"))
        conn.execute(text("ALTER TABLE ropa ADD COLUMN IF NOT EXISTS empresa_id INT REFERENCES empresas(id) ON DELETE CASCADE DEFAULT 1;"))
        conn.execute(text("ALTER TABLE ventas ADD COLUMN IF NOT EXISTS empresa_id INT REFERENCES empresas(id) ON DELETE SET NULL DEFAULT 1;"))
        conn.execute(text("ALTER TABLE reservas ADD COLUMN IF NOT EXISTS empresa_id INT REFERENCES empresas(id) ON DELETE SET NULL DEFAULT 1;"))
        conn.execute(text("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS empresa_id INT REFERENCES empresas(id) ON DELETE SET NULL DEFAULT 1;"))
    print("-> Migración de columnas empresa_id aplicada exitosamente.")

    db = SessionLocal()
    try:
        # 2. Crear los 2 Planes Oficiales del Segundo Parcial
        plan_basico = db.query(PlanSuscripcion).filter(PlanSuscripcion.codigo == "BASICO").first()
        if not plan_basico:
            plan_basico = PlanSuscripcion(
                codigo="BASICO",
                nombre="Plan Básico",
                descripcion="Plan para boutiques emergentes: hasta 2 sucursales, ventas, reservas y operación offline sin IA.",
                precio_mensual=99.0,
                precio_anual=990.0,
                duracion_dias=30,
                limite_sucursales=2,
                limite_usuarios=5,
                soporta_ar=True,
                soporta_ia=False,
                soporta_offline=True,
                activo=True
            )
            db.add(plan_basico)
            db.flush()
            print("  + Creado Plan: BÁSICO (Hasta 2 sucursales, Sin IA)")
        else:
            plan_basico.limite_sucursales = 2
            plan_basico.soporta_ia = False

        plan_pro = db.query(PlanSuscripcion).filter(PlanSuscripcion.codigo == "PROFESIONAL").first()
        if not plan_pro:
            plan_pro = PlanSuscripcion(
                codigo="PROFESIONAL",
                nombre="Plan Profesional",
                descripcion="Plan completo para cadenas de moda: hasta 10 sucursales, analítica de Machine Learning y reportes generativos con IA.",
                precio_mensual=299.0,
                precio_anual=2990.0,
                duracion_dias=30,
                limite_sucursales=10,
                limite_usuarios=25,
                soporta_ar=True,
                soporta_ia=True,
                soporta_offline=True,
                activo=True
            )
            db.add(plan_pro)
            db.flush()
            print("  + Creado Plan: PROFESIONAL (Hasta 10 sucursales, Con IA y Machine Learning)")
        else:
            plan_pro.limite_sucursales = 10
            plan_pro.soporta_ia = True

        db.commit()

        # 3. Crear Empresa 1 de Prueba: FashionStore S.A. (Plan Profesional)
        emp1 = db.query(Empresa).filter(Empresa.slug == "fashionstore").first()
        if not emp1:
            emp1 = Empresa(
                id=1,
                razon_social="FashionStore S.A.",
                nit="1029384021",
                slug="fashionstore",
                logo_url="/assets/images/logos/fashionstore-logo.svg",
                color_marca="#3b82f6",
                descripcion="Cadena de moda formal y de alta costura líder en Santa Cruz.",
                direccion="Av. San Martín #450, Equipetrol",
                ciudad="Santa Cruz",
                telefono="+591 70011223",
                correo_contacto="contacto@fashionstore.com.bo",
                estado="ACTIVA"
            )
            db.add(emp1)
            db.flush()
            print("  + Creada Empresa 1: FashionStore S.A. (Plan Profesional - ID 1)")

        # Suscripción Empresa 1
        susc1 = db.query(SuscripcionEmpresa).filter(SuscripcionEmpresa.empresa_id == emp1.id).first()
        if not susc1:
            susc1 = SuscripcionEmpresa(
                empresa_id=emp1.id,
                plan_id=plan_pro.id,
                estado="ACTIVA",
                ciclo="mensual",
                fecha_inicio=datetime.utcnow() - timedelta(days=15),
                fecha_fin=datetime.utcnow() + timedelta(days=365),
                auto_renovar=True,
                ultima_renovacion=datetime.utcnow()
            )
            db.add(susc1)
            print("  + Asignada Suscripción Profesional a FashionStore S.A.")

        # 4. Crear Empresa 2 de Prueba: Urban Boutique S.R.L. (Plan Básico)
        emp2 = db.query(Empresa).filter(Empresa.slug == "urbanboutique").first()
        if not emp2:
            emp2 = Empresa(
                id=2,
                razon_social="Urban Boutique S.R.L.",
                nit="9876543210",
                slug="urbanboutique",
                logo_url="/assets/images/logos/urban-logo.svg",
                color_marca="#10b981",
                descripcion="Tienda especializada en ropa urbana, streetwear y deportiva casual.",
                direccion="Av. Cristo Redentor #1200, 3er Anillo",
                ciudad="Santa Cruz",
                telefono="+591 78945612",
                correo_contacto="ventas@urbanboutique.bo",
                estado="ACTIVA"
            )
            db.add(emp2)
            db.flush()
            print("  + Creada Empresa 2: Urban Boutique S.R.L. (Plan Básico - ID 2)")

        # Suscripción Empresa 2
        susc2 = db.query(SuscripcionEmpresa).filter(SuscripcionEmpresa.empresa_id == emp2.id).first()
        if not susc2:
            susc2 = SuscripcionEmpresa(
                empresa_id=emp2.id,
                plan_id=plan_basico.id,
                estado="ACTIVA",
                ciclo="mensual",
                fecha_inicio=datetime.utcnow() - timedelta(days=5),
                fecha_fin=datetime.utcnow() + timedelta(days=25),
                auto_renovar=True,
                ultima_renovacion=datetime.utcnow()
            )
            db.add(susc2)
            print("  + Asignada Suscripción Básica a Urban Boutique S.R.L.")

        db.commit()

        # 5. Asegurar sucursales independientes para cada Empresa
        # Sucursales de Empresa 1 (FashionStore): Central y Equipetrol
        sucursales_emp1 = db.query(Sucursal).filter(Sucursal.id.in_([1, 2])).all()
        for s in sucursales_emp1:
            s.empresa_id = emp1.id

        # Sucursal de Empresa 2 (Urban Boutique): Sucursal Norte (ID 3 o nueva)
        suc_urban = db.query(Sucursal).filter(Sucursal.nombre == "Sucursal Urban Norte").first()
        if not suc_urban:
            suc_urban = Sucursal(
                nombre="Sucursal Urban Norte",
                direccion="Av. Banzer Km 8, Centro Comercial Plaza Norte",
                ciudad="Santa Cruz",
                telefono="+591 3 3445566",
                activo=True,
                empresa_id=emp2.id
            )
            db.add(suc_urban)
            print("  + Creada sucursal propia para Empresa 2: Sucursal Urban Norte")

        # 6. Asignar productos existentes a Empresa 1 y crear prendas independientes para Empresa 2
        db.query(Ropa).filter(Ropa.empresa_id == None).update({Ropa.empresa_id: emp1.id})
        
        from models.catalogo import Categoria
        primera_cat = db.query(Categoria).first()
        cat_id = primera_cat.id if primera_cat else 1

        ropa_urban = db.query(Ropa).filter(Ropa.nombre == "Polera Streetwear Grafiti Urban").first()
        if not ropa_urban:
            ropa_urban = Ropa(
                nombre="Polera Streetwear Grafiti Urban",
                descripcion="Polera oversize algodón pesado diseño exclusivo urbano.",
                precio=135.0,
                costo_estandar=60.0,
                imagen_uri="/static/uploads/polera_oversize_negra.jpg",
                activo=True,
                categoria_id=cat_id,
                empresa_id=emp2.id
            )
            db.add(ropa_urban)
            print("  + Creada prenda exclusiva para Empresa 2 (Urban Boutique)")

        # 7. Asignar empresa_id a ventas, reservas y usuarios sin tenant
        db.query(Venta).filter(Venta.empresa_id == None).update({Venta.empresa_id: emp1.id})
        db.query(Reserva).filter(Reserva.empresa_id == None).update({Reserva.empresa_id: emp1.id})
        db.query(Usuario).filter(Usuario.empresa_id == None).update({Usuario.empresa_id: emp1.id})

        db.commit()
        print("\n-> MIGRACIÓN Y POBLACIÓN SAAS MULTITENANT COMPLETADA CON ÉXITO.")
        print(f"   * Empresa 1 (ID {emp1.id}): {emp1.razon_social} -> Plan {plan_pro.nombre} (Con IA, máx 10 sucursales)")
        print(f"   * Empresa 2 (ID {emp2.id}): {emp2.razon_social} -> Plan {plan_basico.nombre} (Sin IA, máx 2 sucursales)")
        print("=" * 70)

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error al poblar SaaS multitenant: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    poblar_saas_multitenant()
