import streamlit as st
import msal
import requests
import pandas as pd
from datetime import datetime, timezone, timedelta
import os
from dotenv import load_dotenv

st.set_page_config(page_title="GRC Dashboard: Microsoft Graph + Alertas BOE", layout="wide")
load_dotenv()

# --- 1. EXTRACCIÓN REAL MICROSOFT GRAPH ---
@st.cache_data(ttl=300)
def get_graph_data(tenant_id, client_id, client_secret):
    authority = f"https://login.microsoftonline.com/{tenant_id}"
    app = msal.ConfidentialClientApplication(
        client_id, authority=authority, client_credential=client_secret
    )
    result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    if "access_token" not in result:
        raise Exception(result.get("error_description", "Error de autenticación en Entra ID"))
    
    headers = {"Authorization": f"Bearer {result['access_token']}"}
    base_url = "https://graph.microsoft.com/v1.0"

    users = requests.get(f"{base_url}/users?$select=id,displayName,userPrincipalName,userType,accountEnabled,createdDateTime", headers=headers).json().get("value", [])
    roles = requests.get(f"{base_url}/directoryRoles?$expand=members", headers=headers).json().get("value", [])
    apps = requests.get(f"{base_url}/applications?$select=displayName,appId,passwordCredentials", headers=headers).json().get("value", [])
    
    mfa_res = requests.get(f"{base_url}/reports/authenticationMethods/userRegistrationDetails", headers=headers)
    mfa_data = mfa_res.json().get("value", []) if mfa_res.status_code == 200 else None

    return users, roles, apps, mfa_data

# --- 2. DATOS SIMULADOS (PARA DEMO SIN TENANT) ---
def get_demo_data():
    now = datetime.now(timezone.utc)
    users = [
        {"id": "1", "displayName": "Laura Gómez (CISO)", "userPrincipalName": "lgomez@empresa.es", "userType": "Member", "accountEnabled": True, "createdDateTime": "2024-01-15T09:00:00Z"},
        {"id": "2", "displayName": "Carlos Ruiz (IT Admin)", "userPrincipalName": "cruiz@empresa.es", "userType": "Member", "accountEnabled": True, "createdDateTime": "2024-03-10T10:30:00Z"},
        {"id": "3", "displayName": "Cuenta Soporte Externo", "userPrincipalName": "soporte_ext#EXT#@empresa.onmicrosoft.com", "userType": "Guest", "accountEnabled": True, "createdDateTime": "2025-02-20T14:00:00Z"},
        {"id": "4", "displayName": "Consultor Auditoría 2025", "userPrincipalName": "auditor_antiguo#EXT#@empresa.onmicrosoft.com", "userType": "Guest", "accountEnabled": True, "createdDateTime": "2025-05-11T08:15:00Z"},
        {"id": "5", "displayName": "Ana Martín (Legal)", "userPrincipalName": "amartin@empresa.es", "userType": "Member", "accountEnabled": True, "createdDateTime": "2024-09-01T11:00:00Z"},
    ]
    roles = [
        {
            "displayName": "Global Administrator",
            "members": [
                {"displayName": "Laura Gómez (CISO)", "userPrincipalName": "lgomez@empresa.es"},
                {"displayName": "Carlos Ruiz (IT Admin)", "userPrincipalName": "cruiz@empresa.es"},
                {"displayName": "Cuenta Emergencia Break-Glass", "userPrincipalName": "breakglass@empresa.es"}
            ]
        }
    ]
    apps = [
        {
            "displayName": "Conector ERP Facturación",
            "appId": "app-001",
            "passwordCredentials": [{"endDateTime": (now - timedelta(days=5)).isoformat()}]
        },
        {
            "displayName": "Portal Proveedores B2B",
            "appId": "app-002",
            "passwordCredentials": [{"endDateTime": (now + timedelta(days=12)).isoformat()}]
        }
    ]
    return users, roles, apps, None

# --- 3. MOTOR DE ALERTAS NORMATIVAS BOE ---
@st.cache_data(ttl=3600)
def get_boe_ciber_alerts(dias_atras=7):
    headers = {"Accept": "application/json"}
    keywords = [
        "ciberseguridad", "seguridad de la información", "esquema nacional de seguridad",
        "protección de datos", "inteligencia artificial", "nis2", "resiliencia operativa",
        "infraestructuras críticas", "incidentes de seguridad", "identidad digital",
        "firma electrónica", "telecomunicaciones", "servicios digitales", "ccn-cert", "incibe"
    ]
    
    alertas_ciber = []
    todas_recientes = []

    for i in range(dias_atras):
        fecha_dt = datetime.now() - timedelta(days=i)
        fecha = fecha_dt.strftime("%Y%m%d")
        fecha_fmt = fecha_dt.strftime("%Y-%m-%d")
        url = f"https://www.boe.es/datosabiertos/api/boe/sumario/{fecha}"
        
        try:
            res = requests.get(url, headers=headers, timeout=4)
            if res.status_code != 200:
                continue
            
            data = res.json()
            diarios = data.get("data", {}).get("sumario", {}).get("diario", [])
            if isinstance(diarios, dict):
                diarios = [diarios]
                
            for diario in diarios:
                secciones = diario.get("seccion", [])
                if isinstance(secciones, dict):
                    secciones = [secciones]
                for sec in secciones:
                    if sec.get("codigo") in ["1", "3"]:
                        deptos = sec.get("departamento", [])
                        if isinstance(deptos, dict):
                            deptos = [deptos]
                        for dep in deptos:
                            items = dep.get("epigrafe", [])
                            if isinstance(items, dict):
                                items = [items]
                            for ep in items:
                                pubs = ep.get("item", [])
                                if isinstance(pubs, dict):
                                    pubs = [pubs]
                                for p in pubs:
                                    titulo = p.get("titulo", "")
                                    identificador = p.get("identificador", "")
                                    
                                    url_pdf_rel = p.get("url_pdf", {}).get("texto", "") if isinstance(p.get("url_pdf"), dict) else ""
                                    link_pdf = f"https://www.boe.es{url_pdf_rel}" if url_pdf_rel.startswith("/") else f"https://www.boe.es/boe/dias/{fecha[:4]}/{fecha[4:6]}/{fecha[6:]}/"
                                    link_web = f"https://www.boe.es/diario_boe/txt.php?id={identificador}" if identificador else link_pdf

                                    coincidencias = [k for k in keywords if k in titulo.lower()]
                                    registro = {
                                        "Fecha": fecha_fmt,
                                        "ID BOE": identificador,
                                        "Organismo": dep.get("nombre", ""),
                                        "Disposición": titulo,
                                        "Palabras Clave": ", ".join(coincidencias) if coincidencias else "General",
                                        "Acceso Web": link_web,
                                        "Descargar PDF": link_pdf
                                    }
                                    todas_recientes.append(registro)
                                    if coincidencias:
                                        alertas_ciber.append(registro)
        except Exception:
            continue
            
    return alertas_ciber, todas_recientes

# --- INTERFAZ DEL DASHBOARD ---
st.title("⚖️🛡️ Centro de Mando GRC: Seguridad Entra ID & Alertas BOE")
st.markdown("Monitorización técnica de identidades (**Microsoft Graph**) vinculada a vigilancia normativa en tiempo real (**BOE**).")

with st.sidebar:
    st.header("🔌 Conexión Microsoft Graph")
    modo_demo = st.toggle("Activar Modo Demo (Sin Tenant)", value=True)
    
    t_id = st.text_input("Tenant ID", value=os.getenv("TENANT_ID", ""), type="password", disabled=modo_demo)
    c_id = st.text_input("Client ID", value=os.getenv("CLIENT_ID", ""), type="password", disabled=modo_demo)
    c_sec = st.text_input("Client Secret", value=os.getenv("CLIENT_SECRET", ""), type="password", disabled=modo_demo)
    ejecutar = st.button("Auditar Tenant", type="primary", use_container_width=True)
    
    st.divider()
    st.header("📚 Marco Legal Base (Acceso Directo)")
    st.markdown("""
    - [Esquema Nacional de Seguridad (RD 311/2022)](https://www.boe.es/buscar/act.php?id=BOE-A-2022-7191)
    - [LOPDGDD (LO 3/2018)](https://www.boe.es/buscar/act.php?id=BOE-A-2018-16673)
    - [Seguridad Redes y Sistemas (RD-ley 12/2018)](https://www.boe.es/buscar/act.php?id=BOE-A-2018-12257)
    - [Código de Ciberseguridad BOE](https://www.boe.es/biblioteca_juridica/codigos/codigo.php?id=195)
    """)

# --- BLOQUE 1: AUDITORÍA TÉCNICA DEL TENANT ---
st.header("1. Auditoría de Seguridad del Tenant (Microsoft Graph)")

if modo_demo or ejecutar or (t_id and c_id and c_sec):
    try:
        if modo_demo:
            st.caption("🧪 **Modo Simulación Activo:** Mostrando telemetría representativa de un tenant corporativo.")
            users, roles, apps, mfa_data = get_demo_data()
        else:
            with st.spinner("Extrayendo telemetría real desde Microsoft Graph..."):
                users, roles, apps, mfa_data = get_graph_data(t_id, c_id, c_sec)

        df_users = pd.DataFrame(users)
        guests = df_users[df_users["userType"] == "Guest"] if not df_users.empty else pd.DataFrame()
        active_guests = guests[guests["accountEnabled"] == True] if not guests.empty else pd.DataFrame()

        global_admins = []
        for r in roles:
            if "Global Administrator" in r.get("displayName", ""):
                for m in r.get("members", []):
                    global_admins.append({"Nombre": m.get("displayName"), "UPN": m.get("userPrincipalName")})

        now = datetime.now(timezone.utc)
        secret_alerts = []
        for app in apps:
            for cred in app.get("passwordCredentials", []):
                end_date = datetime.fromisoformat(cred["endDateTime"].replace("Z", "+00:00"))
                days_left = (end_date - now).days
                if days_left < 30:
                    secret_alerts.append({
                        "Aplicación": app.get("displayName"),
                        "Estado": "🔴 CADUCADO" if days_left < 0 else f"🟡 Caduca en {days_left} días",
                        "Expiración": end_date.strftime("%Y-%m-%d")
                    })

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Identidades Totales", len(df_users))
        c2.metric("Invitados Externos Activos", len(active_guests), delta="Control Terceros (ENS/RGPD)", delta_color="inverse")
        c3.metric("Global Administrators", len(global_admins), delta="Mínimo Privilegio", delta_color="off")
        c4.metric("Secretos en Riesgo (<30d)", len(secret_alerts), delta="Continuidad Operativa", delta_color="inverse")

        tab1, tab2, tab3 = st.tabs(["🔑 Privilegios (Global Admins)", "🌐 Terceros (Guests)", "⏳ Higiene de Aplicaciones"])
        with tab1:
            st.info("**Criterio de Auditoría:** Limitar los Global Admins a menos de 5 cuentas y exigir MFA resistente a phishing.")
            st.dataframe(pd.DataFrame(global_admins), use_container_width=True, hide_index=True)
        with tab2:
            st.info("**Criterio RGPD (Art. 32):** Revisión periódica de cuentas invitadas para evitar fugas de información hacia proveedores o ex-colaboradores.")
            if not active_guests.empty:
                st.dataframe(active_guests[["displayName", "userPrincipalName", "createdDateTime"]], use_container_width=True, hide_index=True)
            else:
                st.success("No hay usuarios invitados activos.")
        with tab3:
            st.info("**Criterio ENS / NIS2:** La caducidad no monitorizada de secretos provoca interrupciones críticas de disponibilidad.")
            if secret_alerts:
                st.dataframe(pd.DataFrame(secret_alerts), use_container_width=True, hide_index=True)
            else:
                st.success("Todos los secretos de aplicación tienen vigencia superior a 30 días.")

    except Exception as e:
        st.error(f"Error conectando a Microsoft Graph: {e}")
else:
    st.info("👈 Activa el Modo Demo o introduce tus credenciales de Entra ID en la barra lateral.")

st.divider()

# --- BLOQUE 2: SISTEMA DE ALERTAS NORMATIVAS BOE ---
st.header("2. Alertas de Normativa en Ciberseguridad y Derecho Digital (BOE)")

dias_busqueda = st.slider("Ventana de rastreo en el BOE (últimos días):", min_value=1, max_value=14, value=7)

with st.spinner(f"Rastreando publicaciones del BOE en los últimos {dias_busqueda} días..."):
    alertas_ciber, todas_recientes = get_boe_ciber_alerts(dias_busqueda)

if alertas_ciber:
    st.error(f"🚨 **ALERTA NORMATIVA:** Se han detectado **{len(alertas_ciber)}** disposiciones relacionadas con ciberseguridad / ámbito digital en los últimos {dias_busqueda} días.")
    df_alertas = pd.DataFrame(alertas_ciber)
    st.dataframe(
        df_alertas,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Acceso Web": st.column_config.LinkColumn("Texto HTML", display_text="Leer en BOE ↗"),
            "Descargar PDF": st.column_config.LinkColumn("Documento Oficial", display_text="PDF Oficial 📥")
        }
    )
else:
    st.success(f"✅ Sin nuevas disposiciones críticas de ciberseguridad publicadas en el BOE en los últimos {dias_busqueda} días.")

with st.expander("Ver todas las disposiciones generales publicadas en este periodo"):
    if todas_recientes:
        df_todas = pd.DataFrame(todas_recientes)
        st.dataframe(
            df_todas[["Fecha", "Organismo", "Disposición", "Acceso Web", "Descargar PDF"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Acceso Web": st.column_config.LinkColumn("Texto HTML", display_text="Leer en BOE ↗"),
                "Descargar PDF": st.column_config.LinkColumn("PDF", display_text="PDF 📥")
            }
        )