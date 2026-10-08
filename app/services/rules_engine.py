from itertools import product
from app.models.schemas import AccessDecision

# Reglas originales:
# A = P ∧ S ∧ ¬Q
# E = P ∧ (R ∨ Q)
# Nuevas reglas justificadas:
# V = certificación vigente y autorización: evita acceso con certificación vencida.
# H = horario seguro y material peligroso: restringe R fuera del horario permitido.

def evaluar_camion(P, Q, R, S, certificacion_vigente=None, horario_seguro=True):
    if certificacion_vigente is None:
        certificacion_vigente = S
    A = P and S and not Q
    E = P and (R or Q)
    V = P and certificacion_vigente
    H = not R or horario_seguro
    acceso = A and V and H
    explicacion = [
        f"A = P ∧ S ∧ ¬Q = {P} ∧ {S} ∧ {not Q} → {A}.",
        f"E = P ∧ (R ∨ Q) = {P} ∧ ({R} ∨ {Q}) → {E}.",
        f"V = P ∧ certificacion_vigente = {P} ∧ {certificacion_vigente} → {V}.",
        f"H = ¬R ∨ horario_seguro = {not R} ∨ {horario_seguro} → {H}.",
    ]
    if acceso:
        resultado = "ACCESO_AUTORIZADO"
        explicacion.append("Todas las condiciones de acceso seguro se cumplen.")
    elif E:
        resultado = "INSPECCION"
        explicacion.append("Se requiere inspección porque E es verdadera.")
    else:
        resultado = "ACCESO_DENEGADO"
        explicacion.append("No se cumplen las condiciones de acceso seguro.")
    return AccessDecision(P=P,Q=Q,R=R,S=S,A=A,E=E,
        reglas_nuevas={"V_certificacion_vigente": V, "H_horario_seguro": H},
        resultado=resultado, explicacion=explicacion).model_dump()

def tabla_verdad():
    rows=[]
    for P,Q,R,S,V,H in product([False,True], repeat=6):
        A=P and S and not Q; E=P and (R or Q); acceso=A and V and (not R or H)
        rows.append({"P":P,"Q":Q,"R":R,"S":S,"V":V,"H":H,"A":A,"E":E,"ACCESO":acceso})
    return rows
