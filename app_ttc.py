import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib import pagesizes
from reportlab.lib.units import inch
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import HRFlowable
from reportlab.platypus import KeepTogether
from reportlab.lib.pagesizes import A4
import os
from io import BytesIO
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta

ARCHIVO_PROSPECTOS = "prospectos.csv"
if "prospectos" not in st.session_state:
    if os.path.exists(ARCHIVO_PROSPECTOS):
        st.session_state.prospectos = pd.read_csv(ARCHIVO_PROSPECTOS)
    else:
        st.session_state.prospectos = pd.DataFrame(
            columns=[
                "FECHA",
                "NOMBRE",
                "CELULAR",
                "CORREO",
                "INTERES",
                "UNIDAD",
                "ESTADO",
                "NOTAS"
            ]
        )

# --- 1. CONFIGURACIÓN VISUAL Y SEGURIDAD ---
st.set_page_config(
    page_title="CRM TTC Alameda", 
    layout="wide", 
    page_icon="🏢",
    initial_sidebar_state="auto" # 'auto' decide según la pantalla, 'expanded' lo deja abierto
)

# Inyectamos CSS para que los botones y tarjetas se vean como una App profesional
st.markdown("""
    <style>
    /* Fondo con gradiente sutil */
    .main {
        background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
    }

    /* Títulos con tipografía imponente */
    h1 {
        font-weight: 800 !important;
        color: #1e293b !important;
        letter-spacing: -1px;
            
    }

    /* TARJETAS DE MÓDULO (Efecto Glassmorphism) */
    .module-card {
        background: rgba(255, 255, 255, 0.8);
        backdrop-filter: blur(10px);
        padding: 2.5rem;
        border-radius: 24px;
        border: 1px solid rgba(255, 255, 255, 0.3);
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.05), 0 10px 10px -5px rgba(0, 0, 0, 0.02);
        text-align: center;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }
    
    .module-card:hover {
        transform: translateY(-10px);
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.15);
        background: white;
    }

    /* BOTONES ESTILO PREMIUM */
    .stButton>button {
        background: linear-gradient(90deg, #1e3a8a 0%, #2563eb 100%);
        color: white !important;
        border: none !important;
        padding: 0.75rem 1.5rem !important;
        border-radius: 14px !important;
        font-weight: 700 !important;
        font-size: 16px !important;
        box-shadow: 0 4px 6px -1px rgba(30, 58, 138, 0.3);
        transition: all 0.3s ease !important;
    }

    .stButton>button:hover {
        box-shadow: 0 10px 15px -3px rgba(30, 58, 138, 0.4);
        opacity: 0.9;
        transform: scale(1.02);
    }

    /* PESTAÑAS (TABS) MODERNAS */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent !important;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: rgba(255,255,255,0.6) !important;
        border-radius: 12px 12px 0 0 !important;
        padding: 10px 20px !important;
        font-weight: 600 !important;
        color: #475569 !important;
        border: none !important;
    }

    .stTabs [aria-selected="true"] {
        background-color: #1e3a8a !important;
        color: white !important;
    }

    /* OCULTAR MENÚ DE STREAMLIT PARA MÁS LIMPIEZA */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# Inicialización de estados de sesión
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.perfil = None
    st.session_state.usuario_actual = None
    st.session_state.area_seleccionada = None
# ==========================================
# 2. DEFINICIÓN DE FUNCIONES
# ==========================================

def login():
    _, col_central, _ = st.columns([1, 1.2, 1])
    
    with col_central:
        with st.container(border=True):
            # Centramos logo y título
            st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
            st.image("https://cdn-icons-png.flaticon.com/512/6073/6073873.png", width=70)
            st.subheader("Acceso al Sistema")
            st.markdown("</div>", unsafe_allow_html=True)
            
            with st.form("login_form", clear_on_submit=False):
                u = st.text_input("Usuario", placeholder="Ej: Administrador")
                p = st.text_input("Contraseña", type="password", placeholder="••••••••")
                boton_submit = st.form_submit_button("INGRESAR", use_container_width=True)  
                if boton_submit:
                    u_clean = u.strip()
                    if u_clean == "Administrador" and p == "admin123":
                        st.session_state.autenticado = True
                        st.session_state.perfil = "ADMINISTRADOR"
                        st.session_state.usuario_actual = u_clean
                        st.rerun()
                    elif u_clean == "Ventas" and p == "ventas123":
                        st.session_state.autenticado = True
                        st.session_state.perfil = "COMERCIAL"
                        st.session_state.usuario_actual = u_clean
                        st.rerun()
                    else:
                        st.error("❌ Password o usuario incorrecto")
# ==========================================
# 3. LÓGICA DE NAVEGACIÓN (Control de pantallas)
# ==========================================

# PASO 1: ¿Está logueado?
if not st.session_state.autenticado:
    login()
    st.stop() # Detiene el resto del código para que solo vean el login

elif st.session_state.area_seleccionada is None:
    st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🏢 PANEL DE CONTROL ALAMEDA</h1>", unsafe_allow_html=True)
    st.write("---") 
    col_com, col_adm = st.columns(2)
    with col_com:
        st.markdown("""
            <div style='background-color: #E0F2FE; padding: 20px; border-radius: 15px; border-left: 5px solid #0284C7; min-height: 180px;'>
                <h2 style='color: #0369A1;'>🎯 COMERCIAL</h2>
                <p>Módulo de Prospectos.</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("🚀 INGRESAR PROSPECTOS", key="btn_com"):
            st.session_state.area_seleccionada = "COMERCIAL"
            st.rerun()   
    with col_adm:
        st.markdown("""
            <div style='background-color: #F1F5F9; padding: 20px; border-radius: 15px; border-left: 5px solid #475569; min-height: 180px;'>
                <h2 style='color: #334155;'>🏦 ADMINISTRATIVO</h2>
                <p>Cartera, Pagos y Clientes Activos.</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("💼 INGRESAR A ADMINISTRACIÓN", key="btn_adm"):
            st.session_state.area_seleccionada = "ADMINISTRATIVA"
            st.rerun()
else:
    # Botón en el Sidebar para poder regresar al menú principal
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.usuario_actual}")
        # Usamos .get() por seguridad para evitar errores si la clave no existe aún
        perfil = st.session_state.get('perfil', 'Usuario')
        st.caption(f"Rol: {perfil.capitalize()}")
        
        if st.sidebar.button("⬅️ CAMBIAR DE MÓDULO"):
            st.session_state.area_seleccionada = None
            st.rerun()

        if st.button("🔓 Cerrar Sesión"):
            st.session_state.autenticado = False
            st.session_state.area_seleccionada = None
            st.rerun()
        st.divider()
    
    # --- CONTENIDO SEGÚN EL ÁREA ---
    if st.session_state.area_seleccionada == "COMERCIAL":
        st.title("🎯 Gestión de Prospectos")
        
        # --- Pestañas del Módulo Comercial ---
        tab_seguimiento, tab_registro = st.tabs(["📋 Lista de Seguimiento", "➕ Registrar Nuevo Interesado"])
        
        with tab_registro:
            st.subheader("Formulario de Captación")
            with st.form("form_prospecto", clear_on_submit=True):
                c1, c2 = st.columns(2)
                nombre_p = c1.text_input("Nombre Completo del Interesado")
                tel_p = c2.text_input("Teléfono / WhatsApp")
                correo_p = c1.text_input("Correo Electrónico")
                
                # NUEVO: Estado inicial de la venta
                estado_p = c2.selectbox("Estado Inicial", [
                    "📞 Por Contactar", 
                    "⏳ En Seguimiento", 
                    "🏠 Visitó Proyecto", 
                    "✅ Reservó", 
                    "❌ Desistió"
                ])
                
                interes_p = c1.selectbox("Nivel de Interés", ["Muy Alto", "Información General", "Inversionista"])
                unidad_p = c2.selectbox("¿Qué unidad busca?", ["Apartamento", "Local Comercial"])
                
                notas_p = st.text_area("Observaciones de la preventa")
                
                submitted = st.form_submit_button("GUARDAR INTERESADO")

                if submitted:

                    if nombre_p and tel_p:
                        nueva_fila = {
                            "FECHA": datetime.now().strftime("%d/%m/%Y"),
                            "NOMBRE": nombre_p.upper(),
                            "CELULAR": tel_p,
                            "CORREO": correo_p,
                            "INTERES": interes_p,
                            "UNIDAD": unidad_p,
                            "ESTADO": estado_p, # Guardamos el estado elegido
                            "NOTAS": notas_p
                        }
                        
                        st.session_state.prospectos = pd.concat([st.session_state.prospectos, pd.DataFrame([nueva_fila])], ignore_index=True)
                        st.session_state.prospectos.to_csv(ARCHIVO_PROSPECTOS, index=False)
                        
                        st.success(f"✅ ¡Excelente! {nombre_p} ha sido registrado.")
                        st.balloons()
                    else:
                        st.error("⚠️ El nombre y el teléfono son obligatorios.")

        with tab_seguimiento:
            st.subheader("Embudo de Ventas")
            if "prospectos" not in st.session_state or st.session_state.prospectos.empty:
                st.info("No hay prospectos registrados todavía.")
            else:
                # --- Filtros rápidos ---
                f1, f2 = st.columns(2)
                with f1:
                    filtro_estado = st.multiselect("Filtrar por Estado", 
                                                 options=list(st.session_state.prospectos['ESTADO'].unique()),
                                                 default=list(st.session_state.prospectos['ESTADO'].unique()))
                with f2:
                    buscar_p = st.text_input("🔍 Buscar por nombre o celular...")

                # Aplicar filtros
                df_p = st.session_state.prospectos
                df_p = df_p[df_p['ESTADO'].isin(filtro_estado)]
                
                if buscar_p:
                    df_p = df_p[df_p['NOMBRE'].str.contains(buscar_p.upper(), na=False) | 
                                df_p['CELULAR'].astype(str).str.contains(buscar_p)]
                
                # Mostrar tabla
                st.dataframe(df_p, use_container_width=True, hide_index=True)
                
                # Métricas rápidas
                m1, m2, m3 = st.columns(3)
                m1.metric("Total Prospectos", len(df_p))
                m2.metric("Reservas ✅", len(df_p[df_p['ESTADO'] == "✅ Reservó"]))
                m3.metric("Por Contactar 📞", len(df_p[df_p['ESTADO'] == "📞 Por Contactar"]))

    elif st.session_state.area_seleccionada == "ADMINISTRATIVA":
            
        # --- AQUÍ EMPIEZAN TUS FUNCIONES ORIGINALES ---

            def numero_a_letras(numero):
                """Convierte números enteros a texto en español."""
                unidades = ["", "UN", "DOS", "TRES", "CUATRO", "CINCO", "SEIS", "SIETE", "OCHO", "NUEVE"]
                decenas = ["", "DIEZ", "VEINTE", "TREINTA", "CUARENTA", "CINCUENTA", "SESENTA", "SETENTA", "OCHENTA", "NOVENTA"]
                diez_a_diecinueve = ["DIEZ", "ONCE", "DOCE", "TRECE", "CATORCE", "QUINCE", "DIECISEIS", "DIECISIETE", "DIECIOCHO", "DIECINUEVE"]
                veinte_a_veintinueve = ["VEINTE", "VEINTIUNO", "VEINTIDOS", "VEINTITRES", "VEINTICUATRO", "VEINTICINCO", "VEINTISEIS", "VEINTISIETE", "VEINTIOCHO", "VEINTINUEVE"]
                centenas = ["", "CIENTO", "DOSCIENTOS", "TRESCIENTOS", "CUATROCIENTOS", "QUINIENTOS", "SEISCIENTOS", "SETECIENTOS", "OCHOCIENTOS", "NOVECIENTOS"]

                if numero == 0: return "CERO"
                if numero == 100: return "CIEN"
                
                def convertir(n):
                    if n < 10:
                        return unidades[n]
                    elif n < 20:
                        return diez_a_diecinueve[n - 10]
                    elif n < 30:
                        return veinte_a_veintinueve[n - 20]
                    elif n < 100:
                        residuo = n % 10
                        return decenas[n // 10] + (" Y " + unidades[residuo] if residuo > 0 else "")
                    elif n < 1000:
                        residuo = n % 100
                        return centenas[n // 100] + (" " + convertir(residuo) if residuo > 0 else "")
                    elif n < 1000000:
                        miles = n // 1000
                        residuo = n % 1000
                        prefijo_mil = "MIL" if miles == 1 else convertir(miles) + " MIL"
                        return prefijo_mil + (" " + convertir(residuo) if residuo > 0 else "")
                    elif n < 1000000000:
                        millones = n // 1000000
                        residuo = n % 1000000
                        prefijo_millon = "UN MILLON" if millones == 1 else convertir(millones) + " MILLONES"
                        return prefijo_millon + (" " + convertir(residuo) if residuo > 0 else "")
                    return str(n)

                return convertir(int(numero))

            def formato_moneda(v):
                try:
                    if pd.isna(v) or str(v).lower() in ["nan", ""]: 
                        return "$ 0"
                    
                    # Primero nos aseguramos de tener un número limpio
                    valor_numerico = limpiar_valor(v)
                    
                    # Formateamos con separador de miles y sin decimales
                    return f"$ {valor_numerico:,.0f}".replace(",", ".")
                except:
                    return "$ 0"
            def formato_moneda(v):
                try:
                    if pd.isna(v) or str(v).lower() in ["nan", ""]:
                        return "$ 0"

                    valor_numerico = limpiar_valor(v)

                    return f"$ {valor_numerico:,.0f}".replace(",", ".")
                except:
                    return "$ 0"
            
            def input_moneda(label, valor_inicial, key, disabled=False):

                if key not in st.session_state:
                    st.session_state[key] = int(valor_inicial or 0)

                valor = st.number_input(
                    label,
                    min_value=0,
                    step=100000,   # ← ahora es int
                    value=int(st.session_state[key]),
                    key=f"{key}_num",
                    format="%d",
                    disabled=disabled
                )

                st.session_state[key] = int(valor)

                st.caption(f"💰 {formato_moneda(valor)}")

                return int(valor)
                    
            def limpiar_valor(v):
                try:
                    if pd.isna(v) or str(v).strip() == "" or str(v).lower() == "nan":
                        return 0
                    
                    # 1. Limpiar símbolos de moneda y espacios
                    s_val = str(v).replace("$", "").replace(" ", "").strip()
                    
                    # 2. Manejo de formato latino (punto para mil, coma para decimal)
                    # Si hay coma, es el decimal. Lo cambiamos a punto para que Python lo entienda.
                    if "," in s_val:
                        # Si tiene puntos de miles (ej: 19.000.000,00), los quitamos
                        if "." in s_val:
                            s_val = s_val.replace(".", "")
                        s_val = s_val.replace(",", ".")
                        
                    # 3. Convertir a float y luego a int (Esto elimina automáticamente el .0 o .00)
                    return int(float(s_val))
                except:
                    return 0

            # --- FUNCION PARA GENERAR PDF (NUEVA) ---
            def generar_pdf_recibo(datos_cliente, datos_recibo):
                pdf = FPDF()
                pdf.add_page()
                
                # --- LOGO EN EL PDF ---
                try:
                    pdf.image("logo ttc.png", 10, 8, 33) 
                except:
                    pass # Si la imagen no carga, el PDF se genera sin ella para no detener el proceso
                
                pdf.set_font("Arial", 'B', 12)
                
                # Encabezado (ajustamos el texto para que no se choque con el logo)
                pdf.ln(5) # Un pequeño salto de línea inicial
                pdf.cell(40) # Espacio en blanco para que el texto empiece después del logo
                pdf.cell(90, 6, "CONSTRUCTORA TTC Y C S.A.S", 0, 0)
                pdf.cell(0, 6, "RECIBO DE CAJA", 0, 1, 'R')                
                pdf.set_font("Arial", '', 9)
                pdf.cell(40) # Espacio en blanco
                pdf.cell(90, 4, "NIT: 900551615-8", 0, 0)
                pdf.cell(0, 4, f"Fecha: {datos_recibo['fecha']}", 0, 1, 'R')                
                pdf.cell(40) # Espacio en blanco
                pdf.cell(90, 4, "Calle 7 # 9 - 34 Local 208 NOBSA", 0, 1)                
                pdf.ln(15) # Espacio antes de los datos del cliente                
                # Datos Cliente (Uso de encode para evitar errores de caracteres)
                pdf.set_font("Arial", 'B', 10)
                pdf.cell(0, 8, f"RECIBIMOS DE: {str(datos_cliente['nombre']).encode('latin-1', 'replace').decode('latin-1')}", 1, 1)
                pdf.set_font("Arial", '', 10)
                pdf.cell(100, 8, f"C.C. / NIT: {datos_cliente['cc']}", 1, 0)
                pdf.cell(0, 8, f"CIUDAD: {datos_recibo['ciudad']}", 1, 1)
                pdf.cell(100, 8, f"PROYECTO: ALAMEDA EL BOSQUE", 1, 0)
                pdf.cell(0, 8, f"INMUEBLE: Apto {datos_cliente['apto']}", 1, 1)                
                pdf.ln(5)
                pdf.set_font("Arial", 'B', 9)
                pdf.multi_cell(0, 8, f"LA SUMA DE: {datos_recibo['letras'].upper()}", 1)                
                pdf.ln(5)
                # Tabla de valores
                pdf.cell(100, 8, "CONCEPTO", 1, 0, 'C')
                pdf.cell(0, 8, "VALOR", 1, 1, 'C')
                pdf.set_font("Arial", '', 10)
                pdf.cell(100, 12, datos_recibo['concepto'], 1, 0, 'L')
                pdf.cell(0, 12, datos_recibo['valor_str'], 1, 1, 'R')
                # -------------------------
                # CUOTA (si aplica)
                # -------------------------
                if datos_recibo.get("cuota"):
                    pdf.set_font("Arial", 'B', 9)
                    pdf.cell(0, 8, f"CUOTA: {datos_recibo['cuota']}", 1, 1)                
                # -------------------------
                # OBSERVACIONES
                # -------------------------
                if datos_recibo.get("observaciones"):

                    pdf.ln(3)
                    pdf.set_font("Arial", 'B', 9)
                    pdf.cell(0, 6, "OBSERVACIONES:", 0, 1)

                    pdf.set_font("Arial", '', 9)

                    obs_texto = str(datos_recibo['observaciones']).encode('latin-1', 'replace').decode('latin-1')

                    pdf.multi_cell(0, 6, obs_texto, 1)
                pdf.ln(20)
                pdf.cell(90, 0, "", 'T', 0)
                pdf.cell(20, 0, "", 0, 0)
                pdf.cell(80, 0, "", 'T', 1)
                pdf.cell(90, 10, "FIRMA Y SELLO RECAUDO", 0, 0, 'C')
                pdf.cell(20, 10, "", 0, 0)
                pdf.cell(80, 10, "FIRMA CLIENTE", 0, 1, 'C')
                
                return pdf.output(dest='S').encode('latin-1')

            # --- 2. SESIÓN ---
            if 'db' not in st.session_state:
                st.session_state.db = None

            st.title("🏢 CRM Alameda - Gestión Inmobiliaria")

            # --- 3. CARGA DE DATOS ---st.sidebar.image("logo ttc.png", use_container_width=True) ---

            ARCHIVO_MAESTRO = "BASE_DATOS_ALAMEDA_ACTUALIZADA.csv"

            def guardar_cambios_db():
                if st.session_state.db is not None:
                    try:
                        st.session_state.db.to_csv(ARCHIVO_MAESTRO, index=False)
                        return True
                    except Exception as e:
                        st.error(f"Error al guardar: {e}")
                return False

            # Inicializar sesión
            if 'db' not in st.session_state:
                st.session_state.db = None

            # --- PROCESO DE CARGA ---
            if st.session_state.db is None:
                if os.path.exists(ARCHIVO_MAESTRO):
                    # Intenta cargar el archivo automático
                    df_temp = pd.read_csv(ARCHIVO_MAESTRO)
                    for col in df_temp.columns:
                        df_temp[col] = df_temp[col].astype(str).replace("nan", "")
                    st.session_state.db = df_temp
                    st.rerun()
                else:
                    # Si no existe, pide el archivo en pantalla principal
                    st.title("🏢 Sistema TTC Alameda")
                    st.info("No se encontró base de datos activa. Por favor, carga el archivo Excel para iniciar.")
                    archivo_subido = st.file_uploader("Subir archivo Excel o CSV", type=["xlsx", "csv"])
                    
                    if archivo_subido:
                        if archivo_subido.name.endswith('.xlsx'):
                            df_temp = pd.read_excel(archivo_subido)
                        else:
                            df_temp = pd.read_csv(archivo_subido)
                        df_temp.columns = [str(c).strip().upper() for c in df_temp.columns]
                        for col in df_temp.columns:
                            df_temp[col] = df_temp[col].astype(str).replace(r'\.0$', '', regex=True).replace("nan", "")
                        st.session_state.db = df_temp
                        guardar_cambios_db()
                        st.success("¡Base de datos creada exitosamente!")
                        st.rerun()
                    st.stop() # No deja pasar nada de lo que sigue sin archivo

            # --- CONFIGURACIÓN DE PESTAÑAS Y VARIABLES ---
            db = st.session_state.db
            df = db
            cols = db.columns.tolist()
            c_apto = next((c for c in cols if any(x in c for x in ["INMUEBLE", "APTO", "UNIDAD"])), cols[0])
            c_nom  = next((c for c in cols if any(x in c for x in ["RECIBIMOS", "NOMBRE", "CLIENTE"])), cols[1])
            c_cc = next((c for c in cols if any(x in c for x in ["CEDULA", "NIT", "IDENTI", "DOCUMENTO", "C.C", "CC"])), None)
            c_banco = next((c for c in st.session_state.db.columns if 'BANCO' in c.upper()), None)
            c_cedula = "CEDULA"
            c_promesa = "# PROMESA"
            c_fechas_cuotas = [f"FECHA_C{i}" for i in range(1, 13)]
            c_valores_cuotas = [f"VALOR_C{i}" for i in range(1, 13)]
            c_estados_cuotas = [f"ESTADO_C{i}" for i in range(1, 13)]
            c_cancelado_ci = next((c for c in cols if "TOTAL" in c and "CANCELADO" in c and "C.I" in c), "TOTAL_CANCELADO_CI")
            c_pago = next((c for c in cols if any(x in c for x in ["NETO", "PAGADO", "VALOR_RECIBIDO", "TOTAL_ABONADO"])), "TOTAL_ABONADO")
            c_saldo = next((c for c in cols if any(x in c for x in ["SALDO", "PENDIENTE"])), "SALDO_PENDIENTE")
            c_v_venta = next((c for c in cols if "VALOR" in c.upper() and "VENTA" in c.upper()), None)
            c_escritura = "ESCRITURA No"
            c_notaria = "NOTARIA"
            c_tel  = next((c for c in cols if any(x in c for x in ["TEL", "CELULAR", "MOVIL"])), "TELEFONO")
            c_mail = next((c for c in cols if ("CORREO" in c or "EMAIL" in c or "MAIL" in c)), "EMAIL")
            c_direc = next((c for c in cols if "DIREC" in c), "DIRECCION")
            c_c_inicial = next((c for c in cols if "CUOTA" in c and "INICIAL" in c), "CUOTA_INICIAL")
            c_ccf = next((c for c in cols if "CCF" in c or "CAJA" in c), "CCF")
            c_entidad = next((c for c in cols if "ENTIDAD" in c or "BANCO" in c), "ENTIDAD_CREDITO")
            c_asesor = next((c for c in cols if "ASESOR" in c), "ASESOR")
            c_desembolso = next((c for c in cols if "VALOR" in c and "CRÉDITO" in c), "VALOR CRÉDITO")
            c_est_desembolso = next((c for c in cols if "ESTADO" in c and "DESEMBOLSO" in c), "ESTADO_DESEMBOLSO")
            c_subsidio = next((c for c in cols if ("ESTADO" in c and "SUB" in c) or ("SUB" in c and "VALOR" not in c)), "ESTADO_SUBSIDIO")
            c_val_subsidio = next((c for c in cols if "VALOR" in c and "SUB" in c), "VALOR_SUBSIDIO")
            c_obs = next((c for c in cols if "OBSERVA" in c), "OBSERVACIONES")
        
            for col_req in [c_pago, c_saldo, c_v_venta, c_obs, c_cancelado_ci, c_c_inicial]:
                if col_req not in db.columns:
                    db[col_req] = "0"
            if "HISTORIAL_FINANCIERO" not in db.columns:
                db["HISTORIAL_FINANCIERO"] = ""

            # Crear las pestañas
            nombres_tabs = ["🔍 Gestión Postventa", "➕ Registro", "💰 Cartera Ejecutiva", "📊 Informe Gerencial"]
            tabs = st.tabs(nombres_tabs)

            # --- TAB 1: BUSCADOR TRANSPARENTE Y COMPACTO ---
            with tabs[0]:
                st.markdown("""
                    <style>
                    [data-testid="stSidebarNav"] {
                        background-size: 200px;
                    }
                    /* Estilo para que las pestañas sean más grandes en celular */
                    .stTabs [data-baseweb="tab-list"] {
                        gap: 10px;
                    }
                    .stTabs [data-baseweb="tab"] {
                        height: 50px;
                        white-space: pre-wrap;
                    }
                    </style>
                    """, unsafe_allow_html=True)
                col_busq, col_espacio = st.columns([2, 3]) 
                
                with col_busq:
                    opciones_full = {f"Apto {row[c_apto]} - {row[c_nom]}": idx for idx, row in st.session_state.db.iterrows()}
                    
                    # BUSCADOR INTELIGENTE:
                    seleccion = st.selectbox(
                        "Buscar cliente:",
                        options=list(opciones_full.keys()),
                        index=None, 
                        placeholder="Escriba Apto o Nombre...",
                        key="buscador_dinamico"
                    )

                # 2. Lógica de carga: Solo se activa si 'seleccion' no es None
                if seleccion:
                    idx_sel = opciones_full[seleccion]
                    cliente = st.session_state.db.loc[idx_sel]
                    
                    # -------- VALOR DE VENTA --------
                    venta = int(limpiar_valor(cliente.get(c_v_venta)))
                    cuota_inicial_automatica = int(limpiar_valor(cliente.get(c_v_venta)) * 0.10)
                    abonos_base = int(limpiar_valor(cliente.get(c_pago)) )
                    cancelado_ci = int(limpiar_valor(cliente.get(c_cancelado_ci))) 
                    sub_valor = int(limpiar_valor(cliente.get(c_val_subsidio)))
                    desembolso_val = int(limpiar_valor(cliente.get(c_desembolso)))

                    # -------- ESTADOS --------
                    estado_des_actual = str(cliente.get(c_est_desembolso)).strip().upper()
                    desembolso_efectivo = desembolso_val if estado_des_actual == "SI" else 0

                    estado_sub_actual = str(cliente.get(c_subsidio)).strip().upper()
                    subsidio_efectivo = sub_valor if estado_sub_actual == "APROBADO" else 0

                    # -------- TOTALES FINANCIEROS --------
                    total_abonado_real = abonos_base + cancelado_ci + subsidio_efectivo + desembolso_efectivo
                    saldo_real = venta - total_abonado_real

                    # -------- CUOTA INICIAL --------
                    cuota_inicial_real = cuota_inicial_automatica
                    total_cancelado_ci_real = cancelado_ci

                    porcentaje_ci = 0
                    if cuota_inicial_real > 0:
                        porcentaje_ci = (total_cancelado_ci_real / cuota_inicial_real) * 100

                        # -------- INTERFAZ CLIENTE --------
                        st.divider()
                        st.markdown(f"## 👤 {cliente[c_nom]}")
                        st.markdown(f"**🆔 CC:** {cliente[c_cedula]} | **📍 Inmueble:** Apto {cliente[c_apto]}")

                        seccion = st.pills(
                            "Sección:",
                            ["📋 Contacto", "💰 Financiero", "📑 Trámites", "📝 Notas"],
                            selection_mode="single",
                            default="📋 Contacto"
                        )

                        # ===============================
                        # CONTACTO
                        # ===============================
                        if seccion == "📋 Contacto":

                            c1, c2, c3 = st.columns(3)

                            c1.info(f"📞 **Teléfono:**\n{cliente.get(c_tel, 'No registrado')}")
                            c2.info(f"📧 **Email:**\n{cliente.get(c_mail, 'No registrado')}")
                            c3.info(f"🏙️ **Ubicación:**\n{cliente.get(c_direc, 'No registrado')}")

                        elif seccion == "💰 Financiero":
                            
                            c_fiducia = "CONSIGNACIÓN FIDUCIA"

                            # ======================================================
                            # ASEGURAR COLUMNAS NECESARIAS
                            # ======================================================

                            if "PLAN_BLOQUEADO" not in st.session_state.db.columns:
                                st.session_state.db["PLAN_BLOQUEADO"] = False

                            if "NUMERO_CUOTAS" not in st.session_state.db.columns:
                                st.session_state.db["NUMERO_CUOTAS"] = 1

                            if "VALOR_SUBSIDIO" not in st.session_state.db.columns:
                                st.session_state.db["VALOR_SUBSIDIO"] = 0

                            if "VALOR_CREDITO" not in st.session_state.db.columns:
                                st.session_state.db["VALOR_CREDITO"] = 0

                            if "ESTADO_SUBSIDIO" not in st.session_state.db.columns:
                                st.session_state.db["ESTADO_SUBSIDIO"] = "POR TRAMITAR"

                            if "CREDITO_DESEMBOLSADO" not in st.session_state.db.columns:
                                st.session_state.db["CREDITO_DESEMBOLSADO"] = "NO"                                                    

                            if "guardar_financiero" not in st.session_state:
                                st.session_state.guardar_financiero = False

                            for i in range(1,13):

                                if f"VALOR_C{i}" not in st.session_state.db.columns:
                                    st.session_state.db[f"VALOR_C{i}"] = 0

                                if f"FECHA_C{i}" not in st.session_state.db.columns:
                                    st.session_state.db[f"FECHA_C{i}"] = None

                                if f"ESTADO_C{i}" not in st.session_state.db.columns:
                                    st.session_state.db[f"ESTADO_C{i}"] = "PENDIENTE"

                            # ======================================================
                            # VARIABLES PRINCIPALES
                            # ======================================================

                            valor_venta = venta
                            cuota_inicial = valor_venta * 0.10

                            abono_fiducia = int(limpiar_valor(st.session_state.db.at[idx_sel, c_fiducia]))
                            # ==========================
                            # CALCULAR TOTAL PAGADO (ANTES DE USARLO)
                            # ==========================
                            total_pagado = 0

                            n_cuotas_temp = int(st.session_state.db.at[idx_sel, "NUMERO_CUOTAS"])

                            for i in range(1, n_cuotas_temp + 1):

                                valor = limpiar_valor(st.session_state.db.at[idx_sel, f"VALOR_C{i}"])
                                estado = str(st.session_state.db.at[idx_sel, f"ESTADO_C{i}"]).upper()

                                pagado = 0
                                if f"PAGADO_C{i}" in st.session_state.db.columns:
                                    pagado = limpiar_valor(st.session_state.db.at[idx_sel, f"PAGADO_C{i}"])

                                if estado == "PAGADO":
                                    total_pagado += valor
                                else:
                                    total_pagado += pagado
                            saldo_ci = max(0, cuota_inicial - (abono_fiducia + total_pagado))

                            subsidio_guardado = int(limpiar_valor(cliente.get("VALOR_SUBSIDIO",0)))
                            credito_guardado = int(limpiar_valor(cliente.get("VALOR_CREDITO",0)))

                            estado_sub = str(cliente.get("ESTADO_SUBSIDIO","POR TRAMITAR"))
                            estado_cred = str(cliente.get("CREDITO_DESEMBOLSADO","NO"))

                            plan_bloqueado = bool(st.session_state.db.at[idx_sel,"PLAN_BLOQUEADO"])

                            # ======================================================
                            # PLAN DE PAGO CUOTA INICIAL
                            # ======================================================
                            with st.expander("💵 Pago Cuota Inicial", expanded=False):
                                st.markdown("### 📋 Plan de Pago Cuota Inicial")

                                # Calcular avance de la cuota inicial
                                porcentaje_ci = 0
                                if cuota_inicial > 0:
                                    porcentaje_ci = min(abono_fiducia / cuota_inicial, 1)

                                with st.container(border=True):

                                    c1,c2,c3,c4 = st.columns(4)

                                    with c1:
                                        st.caption("Valor de Venta")
                                        st.markdown(f"**{formato_moneda(valor_venta)}**")

                                    with c2:
                                        st.caption("Cuota Inicial (10%)")
                                        st.markdown(f"**{formato_moneda(cuota_inicial)}**")

                                    with c3:
                                        st.caption("Abono en Fiducia")
                                        st.markdown(f"**{formato_moneda(abono_fiducia)}**")

                                    with c4:
                                        st.caption("Saldo Cuota Inicial")
                                        st.markdown(f"**{formato_moneda(saldo_ci)}**")

                                    st.write("")

                                    # Barra de progreso de la cuota inicial
                                    st.caption("Avance de pago de la cuota inicial")

                                    st.progress(porcentaje_ci)

                                    st.caption(f"{int(porcentaje_ci*100)}% pagado")

                                st.write("")
                                # ======================================================
                                # CONFIGURACIÓN CUOTAS
                                # ======================================================

                                n_cuotas_pactadas = int(st.session_state.db.at[idx_sel,"NUMERO_CUOTAS"])

                                if n_cuotas_pactadas <= 0:
                                    n_cuotas_pactadas = 1

                                monto_a_diferir = saldo_ci

                                c1, c2, c3 = st.columns([2.2, 0.9, 0.9], vertical_alignment="bottom")

                                with c1:
                                    st.info(f"Saldo de CI a diferir: **{formato_moneda(monto_a_diferir)}**")

                                with c2:
                                    n_cuotas_pactadas = st.number_input(
                                        "Cuotas",
                                        min_value=1,
                                        max_value=18,
                                        value=n_cuotas_pactadas,
                                        disabled=plan_bloqueado,
                                        key=f"cuotas_{idx_sel}"
                                    )

                                with c3:
                                    if st.button("🔄 Calcular", disabled=plan_bloqueado):
                                        st.session_state[f"modo_{idx_sel}"] = "CALC"

                                modo = st.session_state.get(f"modo_{idx_sel}")

                                # ======================================================
                                # GENERAR CUOTAS
                                # ======================================================

                                if modo == "CALC" and not plan_bloqueado:

                                    cuota_sugerida = int(monto_a_diferir / n_cuotas_pactadas) if n_cuotas_pactadas > 0 else monto_a_diferir
                                    # 🔹 LIMPIAR VALORES ANTERIORES
                                    for i in range(1, 25):
                                        key_valor = f"vn_{idx_sel}_{i}"
                                        if key_valor in st.session_state:
                                            del st.session_state[key_valor]
                                    st.markdown("---")

                                    h1,h2,h3 = st.columns([1.5,1.2,1])

                                    h1.caption("Fecha")
                                    h2.caption("Valor")
                                    h3.caption("Estado")

                                    for i in range(1,n_cuotas_pactadas+1):

                                        c1,c2,c3 = st.columns([1.5,1.2,1])

                                        with c1:
                                            st.date_input(
                                                f"f{i}",
                                                value=date.today()+relativedelta(months=i),
                                                key=f"fn_{idx_sel}_{i}",
                                                label_visibility="collapsed"
                                            )

                                        with c2:

                                            key_valor = f"vn_{idx_sel}_{i}"

                                            # resetear valor si se recalcula
                                            st.session_state[key_valor] = formato_moneda(cuota_sugerida)

                                            st.text_input(
                                                f"v{i}",
                                                key=key_valor,
                                                label_visibility="collapsed"
                                            )

                                        with c3:
                                            st.selectbox(
                                                f"e{i}",
                                                ["PENDIENTE","PAGADO"],
                                                key=f"en_{idx_sel}_{i}",
                                                label_visibility="collapsed"
                                            )

                                    if st.button("💾 Guardar y Bloquear Plan",type="primary"):

                                        st.session_state.db.at[idx_sel,"NUMERO_CUOTAS"] = n_cuotas_pactadas
                                        st.session_state.db.at[idx_sel,c_fiducia] = abono_fiducia

                                        for i in range(1,n_cuotas_pactadas+1):

                                            fecha = st.session_state.get(f"fn_{idx_sel}_{i}")
                                            valor = limpiar_valor(st.session_state.get(f"vn_{idx_sel}_{i}"))

                                            if valor == 0:
                                                valor = cuota_sugerida

                                            st.session_state.db.at[idx_sel,f"FECHA_C{i}"] = fecha
                                            st.session_state.db.at[idx_sel,f"VALOR_C{i}"] = valor
                                            st.session_state.db.at[idx_sel,f"ESTADO_C{i}"] = st.session_state.get(f"en_{idx_sel}_{i}")

                                        st.session_state.db.at[idx_sel,"PLAN_BLOQUEADO"] = True

                                        st.session_state.db.to_excel("Base_Datos_TTC.xlsx",index=False)

                                        st.success("Plan guardado correctamente")

                                        st.rerun()

                                # ======================================================
                                # CRONOGRAMA CUOTAS
                                # ======================================================

                                total_pagado = 0

                                if plan_bloqueado:

                                    st.markdown("### 📊 Cronograma de Cuotas")

                                    for i in range(1,n_cuotas_pactadas+1):

                                        cx,cy = st.columns([2,1])

                                        fecha = st.session_state.db.at[idx_sel,f"FECHA_C{i}"]
                                        valor = int(limpiar_valor(st.session_state.db.at[idx_sel,f"VALOR_C{i}"]))
                                        estado = str(st.session_state.db.at[idx_sel,f"ESTADO_C{i}"]).upper()

                                        if estado == "PAGADO":
                                            total_pagado += valor
                                        elif estado == "PENDIENTE":
                                            valor_original = valor
                                            valor_pagado = limpiar_valor(
                                                st.session_state.db.at[idx_sel, f"PAGADO_C{i}"]
                                                if f"PAGADO_C{i}" in st.session_state.db.columns else 0
                                            )
                                            total_pagado += valor_pagado                                           

                                        cx.write(f"Cuota {i} | {fecha} | **{formato_moneda(valor)}**")

                                        cy.selectbox(
                                            f"estado_{i}",
                                            ["PENDIENTE","PAGADO"],
                                            index=0 if estado=="PENDIENTE" else 1,
                                            key=f"ue_{idx_sel}_{i}",
                                            label_visibility="collapsed"
                                        )

                                    if st.button("💾 Actualizar Estados"):

                                        for i in range(1,n_cuotas_pactadas+1):

                                            st.session_state.db.at[idx_sel,f"ESTADO_C{i}"] = st.session_state[f"ue_{idx_sel}_{i}"]

                                        st.session_state.db.to_excel("Base_Datos_TTC.xlsx",index=False)

                                        st.success("Estados actualizados")
                            # ======================================================
                            # RESUMEN FINANCIERO
                            # ======================================================
                            with st.expander("🏠 Credito, Subsidio y Resumen Financiero", expanded=False):
                                # Tomar valores actuales si existen
                                subsidio_actual = nuevo_sub if 'nuevo_sub' in locals() else subsidio_guardado
                                credito_actual = nuevo_cred if 'nuevo_cred' in locals() else credito_guardado

                                estado_sub_actual = estado_subsidio if 'estado_subsidio' in locals() else estado_sub
                                estado_cred_actual = estado_credito if 'estado_credito' in locals() else estado_cred


                                subsidio_aplicado = 0
                                credito_aplicado = 0

                                if estado_sub_actual == "APROBADO":
                                    subsidio_aplicado = subsidio_actual

                                if estado_cred_actual == "SI":
                                    credito_aplicado = credito_actual


                                total_descuentos = subsidio_aplicado + credito_aplicado


                                saldo_apto = valor_venta - (
                                    abono_fiducia +
                                    total_pagado +
                                    total_descuentos
                                )                                              
                                # ======================================================
                                # BARRA PROGRESO DE COMPRA
                                # ======================================================

                                total_pagado_apto = abono_fiducia + total_pagado + total_descuentos

                                porcentaje_compra = 0
                                if valor_venta > 0:
                                    porcentaje_compra = total_pagado_apto / valor_venta

                                st.markdown("### 🏠 Progreso de Compra")

                                st.progress(min(porcentaje_compra,1.0))

                                c1,c2 = st.columns(2)

                                with c1:
                                    st.caption("Total cubierto")
                                    st.write(f"{formato_moneda(total_pagado_apto)}")

                                
                                # ======================================================
                                # RESUMEN FINANCIERO
                                # ======================================================

                                st.markdown("### 📊 Resumen Financiero")

                                with st.container(border=True):

                                    r1,r2,r3 = st.columns(3)

                                    with r1:
                                        st.caption("Total Pagado Cuota Inicial")
                                        st.markdown(f"**{formato_moneda(abono_fiducia + total_pagado)}**")

                                    with r2:
                                        st.caption("Subsidio + Crédito")
                                        st.markdown(f"**{formato_moneda(subsidio_aplicado + credito_aplicado)}**")

                                    with r3:
                                        st.caption("Saldo Apartamento")
                                        st.markdown(f"**{formato_moneda(saldo_apto)}**")
                                # ======================================================
                                # SUBSIDIO Y CRÉDITO
                                # ======================================================

                                # Crear columnas de bloqueo si no existen
                                if "SUBSIDIO_BLOQUEADO" not in st.session_state.db.columns:
                                    st.session_state.db["SUBSIDIO_BLOQUEADO"] = False

                                if "CREDITO_BLOQUEADO" not in st.session_state.db.columns:
                                    st.session_state.db["CREDITO_BLOQUEADO"] = False


                                subsidio_bloqueado = bool(st.session_state.db.at[idx_sel,"SUBSIDIO_BLOQUEADO"])
                                credito_bloqueado = bool(st.session_state.db.at[idx_sel,"CREDITO_BLOQUEADO"])


                                with st.container(border=True):

                                    st.subheader("🏦 Crédito y Subsidio")

                                    # 3 columnas (subsidio / credito / acciones)
                                    col1,col2,col3 = st.columns([1,1,0.8])

                                    # -------------------------
                                    # SUBSIDIO
                                    # -------------------------
                                    with col1:

                                        nuevo_sub = input_moneda(
                                            "Valor Subsidio",
                                            subsidio_guardado,
                                            key=f"subsidio_{idx_sel}",
                                            disabled=subsidio_bloqueado
                                        )

                                        estado_subsidio = st.selectbox(
                                            "Estado Subsidio",
                                            ["POR TRAMITAR","TRAMITADO","APROBADO"],
                                            index=0 if estado_sub=="POR TRAMITAR" else 2,
                                            disabled=subsidio_bloqueado
                                        )

                                    with col2:

                                        nuevo_cred = input_moneda(
                                            "Valor Crédito",
                                            credito_guardado,
                                            key=f"credito_{idx_sel}",
                                            disabled=credito_bloqueado
                                        )

                                        estado_credito = st.selectbox(
                                            "Crédito Desembolsado",
                                            ["NO","SI"],
                                            index=1 if estado_cred=="SI" else 0,
                                            disabled=credito_bloqueado
                                        )

                                    # -------------------------
                                    # ACCIONES
                                    # -------------------------
                                    with col3:

                                        st.write("")  # alineación vertical
                                        st.write("")

                                        confirmar = st.checkbox(
                                            "Confirmar",
                                            disabled=(subsidio_bloqueado and credito_bloqueado)
                                        )

                                        guardar = st.button(
                                            "💾 Guardar",
                                            use_container_width=True
                                        )


                                        # -------- DESBLOQUEO ADMIN --------
                                        if subsidio_bloqueado or credito_bloqueado:

                                            st.caption("🔐 Admin")

                                            clave = st.text_input(
                                                "Clave",
                                                type="password",
                                                label_visibility="collapsed",
                                                placeholder="clave"
                                            )

                                            desbloquear = st.button(
                                                "Desbloquear",
                                                use_container_width=True
                                            )
                                        else:
                                            desbloquear = False


                                    # ======================================================
                                    # GUARDAR
                                    # ======================================================

                                    if guardar:

                                        if confirmar:

                                            if nuevo_sub == 0:
                                                nuevo_sub = subsidio_guardado

                                            if nuevo_cred == 0:
                                                nuevo_cred = credito_guardado


                                            st.session_state.db.at[idx_sel,"VALOR_SUBSIDIO"] = nuevo_sub
                                            st.session_state.db.at[idx_sel,"ESTADO_SUBSIDIO"] = estado_subsidio

                                            st.session_state.db.at[idx_sel,"VALOR_CREDITO"] = nuevo_cred
                                            st.session_state.db.at[idx_sel,"CREDITO_DESEMBOLSADO"] = estado_credito


                                            if nuevo_sub > 0:
                                                st.session_state.db.at[idx_sel,"SUBSIDIO_BLOQUEADO"] = True

                                            if nuevo_cred > 0:
                                                st.session_state.db.at[idx_sel,"CREDITO_BLOQUEADO"] = True


                                            st.session_state.db.to_excel("Base_Datos_TTC.xlsx",index=False)

                                            st.success("Valores guardados correctamente")

                                            st.rerun()

                                        else:

                                            st.warning("Debes confirmar los valores antes de guardar")


                                    # ======================================================
                                    # DESBLOQUEAR
                                    # ======================================================

                                    if desbloquear:

                                        if clave == "admin123":

                                            st.session_state.db.at[idx_sel,"SUBSIDIO_BLOQUEADO"] = False
                                            st.session_state.db.at[idx_sel,"CREDITO_BLOQUEADO"] = False

                                            st.session_state.db.to_excel("Base_Datos_TTC.xlsx",index=False)

                                            st.success("Campos desbloqueados")

                                            st.rerun()

                                        else:

                                            st.error("Clave incorrecta")
                            # ===============================
                            # 3️⃣ REGISTRO ABONO + RECIBO
                            # ===============================
                            with st.expander("🧾 Registro de Abono / Recibo", expanded=False):
                                st.subheader("📄 Registro abono")

                                with st.expander("⚙️ Configurar Datos del Recibo", expanded=True):

                                    # -------------------------
                                    # BUSCAR CUOTAS PENDIENTES
                                    # -------------------------
                                    num_cuota = None
                                    cuotas_pendientes = []
                                    mapa_cuotas = {}

                                    n_cuotas = int(st.session_state.db.at[idx_sel, "NUMERO_CUOTAS"])

                                    for i in range(1, n_cuotas + 1):

                                        estado = st.session_state.db.at[idx_sel, f"ESTADO_C{i}"]
                                        valor = limpiar_valor(st.session_state.db.at[idx_sel, f"VALOR_C{i}"])

                                        if estado != "PAGADO":

                                            etiqueta = f"CUOTA {i} - {formato_moneda(valor)}"
                                            cuotas_pendientes.append(etiqueta)

                                            mapa_cuotas[etiqueta] = i

                                    # -------------------------
                                    # DATOS DEL RECIBO
                                    # -------------------------

                                    col_f1, col_f2 = st.columns(2)

                                    fecha_r = col_f1.date_input("Fecha de pago:", datetime.now())
                                    ciudad_r = col_f2.text_input("Ciudad:", "NOBSA")

                                    col_f3, col_f4 = st.columns(2)

                                    concepto_r = col_f3.selectbox(
                                        "Concepto de pago:",
                                        ["SEPARACIÓN","FINANCIACIÓN CUOTA INICIAL","ABONO EXTRAORDINARIO","OTRO"]
                                    )
                                    num_cuota = None                                   

                                    # SOLO activar si el concepto es financiación cuota inicial
                                    activar_cuotas = concepto_r == "FINANCIACIÓN CUOTA INICIAL"


                                    cuota_seleccionada = st.selectbox(
                                        "Cuota que se paga:",
                                        cuotas_pendientes if cuotas_pendientes else ["Sin cuotas pendientes"],
                                        disabled=not activar_cuotas,
                                        key=f"cuota_pago_{idx_sel}"
                                    )


                                    if activar_cuotas and cuotas_pendientes:

                                        num_cuota = mapa_cuotas[cuota_seleccionada]

                                        st.info(f"Pago correspondiente a **CUOTA {num_cuota}**")
                                        st.session_state[f"num_cuota_pago_{idx_sel}"] = num_cuota
                                    # -------------------------
                                    # VALOR DEL RECIBO
                                    # -------------------------
                                    valor_sugerido = 0

                                    if num_cuota:
                                        valor_sugerido = limpiar_valor(
                                            st.session_state.db.at[idx_sel, f"VALOR_C{num_cuota}"]
                                        )

                                    valor_r = col_f4.number_input(
                                        "Valor a recibir ($):",
                                        min_value=0,
                                        value=int(valor_sugerido),
                                        step=100000,
                                        key=f"valor_recibo_{idx_sel}"
                                    )

                                    # -------------------------
                                    # TEXTO EN LETRAS
                                    # -------------------------

                                    key_letras = f"letras_recibo_{idx_sel}"

                                    texto_auto_letras = f"{numero_a_letras(valor_r)} PESOS M/CTE" if valor_r > 0 else ""

                                    # actualizar automáticamente si cambia el valor
                                    if key_letras not in st.session_state or valor_r > 0:
                                        st.session_state[key_letras] = texto_auto_letras

                                    letras_r = st.text_input(
                                        "La suma de (en letras):",
                                        key=key_letras
                                    )

                                    # -------------------------
                                    # ENTIDAD
                                    # -------------------------

                                    entidad_r = st.text_input(
                                        "Entidad de recaudo:",
                                        value="ACCION FIDUCIARIA BANCOLOMBIA",
                                        key=f"entidad_recibo_{idx_sel}"
                                    )
                                                            
                                    # -------------------------
                                    # Observaciones opcionales
                                    # -------------------------
                                    observaciones_r = st.text_area(
                                        "Observaciones (opcional):",
                                        key=f"obs_recibo_preview_{idx_sel}",
                                        max_chars=200,
                                        height=50
                                    )
                                    # -------------------------
                                    # VISTA PREVIA
                                    # -------------------------

                                    if st.button("👁️ Generar Vista Previa del Recibo"):

                                        with st.container(border=True):

                                            h1,h2,h3 = st.columns([1,1,1])

                                            with h1:
                                                st.write("**CONSTRUCTORA TTC Y C S.A.S**")
                                                st.caption("NIT: 900551615-8")
                                                st.caption("Calle 7 # 9 - 34 Local 208 NOBSA")

                                            with h2:
                                                st.write("**SEVERINO S.A.S**")
                                                st.caption("NIT: 901.922.140-8")
                                                st.caption("Tv 19 A No. 96 94 BOGOTA D.C")

                                            with h3:
                                                st.markdown("### RECIBO DE CAJA")
                                                st.markdown(f"**Fecha:** {fecha_r.strftime('%d/%m/%Y')}")

                                            st.divider()

                                            r_c1,r_c2 = st.columns(2)

                                            with r_c1:

                                                st.write(f"**RECIBIMOS DE:** {cliente[c_nom]}")
                                                st.write(f"**C.C. / NIT:** {cliente[c_cc]}")
                                                st.write(f"**CIUDAD:** {ciudad_r}")

                                            with r_c2:

                                                st.write("**PROYECTO:** ALAMEDA EL BOSQUE")
                                                st.write(f"**INMUEBLE:** Apto {cliente[c_apto]}")
                                                st.write(f"**TELÉFONO:** {cliente[c_tel]}")
                                                st.write(f"**VALOR:** {formato_moneda(valor_r)}")
                                                st.write(f"**BANCO/ENTIDAD:** {entidad_r}")

                                            if num_cuota:
                                                st.info(f"Pago correspondiente a **CUOTA {num_cuota}**")

                                            st.info(f"**LA SUMA DE:** {letras_r.upper()}")
                                            if observaciones_r:
                                                st.warning(f"**OBSERVACIONES:** {observaciones_r}")
                                            
                                            # -------------------------
                                            # GENERAR PDF
                                            # -------------------------

                                            datos_pdf_cliente = {
                                                "nombre": cliente[c_nom],
                                                "cc": cliente[c_cc],
                                                "apto": cliente[c_apto]
                                            }

                                            datos_pdf_recibo = {
                                                "fecha": fecha_r.strftime('%d/%m/%Y'),
                                                "ciudad": ciudad_r,
                                                "concepto": concepto_r,
                                                "valor_str": formato_moneda(valor_r),
                                                "letras": letras_r,
                                                "cuota": num_cuota,
                                                "observaciones": observaciones_r
                                            }
                                            
                                            # -------------------------
                                            # Generar PDF
                                            # -------------------------
                                            pdf_bytes = generar_pdf_recibo(datos_pdf_cliente, datos_pdf_recibo)

                                            # -------------------------
                                            # Botón de descarga
                                            # -------------------------
                                            st.download_button(
                                                label="📥 DESCARGAR RECIBO PDF",
                                                data=pdf_bytes,
                                                file_name=f"Recibo_{cliente[c_apto]}_{datetime.now().strftime('%Y%m%d')}.pdf",
                                                mime="application/pdf"
                                        )                                        
                            # ===============================
                            # BOTÓN GUARDAR (SIN LOOP)
                            # ===============================
                            # ==========================
                            # ACTUALIZAR CUOTA PAGADA
                            # ==========================
                            if num_cuota is not None and valor_r > 0:

                                valor_cuota = limpiar_valor(
                                    st.session_state.db.at[idx_sel, f"VALOR_C{num_cuota}"]
                                )

                                # Si paga el valor completo → marcar como pagado
                                if valor_r >= valor_cuota:
                                    st.session_state.db.at[idx_sel, f"ESTADO_C{num_cuota}"] = "PAGADO"

                                # Si quieres permitir abonos parciales (opcional)
                                else:
                                    nuevo_valor = valor_cuota - valor_r
                                    st.session_state.db.at[idx_sel, f"VALOR_C{num_cuota}"] = nuevo_valor
                            
                            if st.button("💾 Guardar Cambios Financieros", use_container_width=True):

                                fecha_mov = datetime.now().strftime("%d/%m/%Y %H:%M")
                                movimientos = []

                                # -------------------------
                                # VALORES ANTERIORES
                                # -------------------------
                                sub_estado_anterior = str(cliente.get(c_subsidio)).strip().upper()
                                des_estado_anterior = str(cliente.get(c_est_desembolso)).strip().upper()

                                valor_sub_anterior = limpiar_valor(cliente.get(c_val_subsidio))
                                valor_des_anterior = limpiar_valor(cliente.get(c_desembolso))
                                valor_ci_anterior = limpiar_valor(cliente.get(c_cancelado_ci))

                                # -------------------------
                                # VALORES NUEVOS
                                # -------------------------
                                valor_ci_nuevo = limpiar_valor(st.session_state.db.at[idx_sel, c_cancelado_ci])
                                valor_sub_nuevo = limpiar_valor(nuevo_sub)
                                valor_des_nuevo = limpiar_valor(nuevo_cred)

                                # -------------------------
                                # CUOTA INICIAL
                                # -------------------------
                                if valor_ci_nuevo != valor_ci_anterior:
                                    diferencia = valor_ci_nuevo - valor_ci_anterior

                                    if diferencia != 0:
                                        tipo = "ABONO CUOTA INICIAL" if diferencia > 0 else "AJUSTE CUOTA INICIAL"
                                        movimientos.append(
                                            f"{fecha_mov} | {tipo} | $ {abs(diferencia):,.0f}".replace(",", ".")
                                        )

                                # -------------------------
                                # SUBSIDIO
                                # -------------------------
                                if sub_estado_anterior != estado_subsidio or valor_sub_anterior != valor_sub_nuevo:

                                    if estado_subsidio == "APROBADO" and valor_sub_nuevo > 0:
                                        movimientos.append(
                                            f"{fecha_mov} | SUBSIDIO APROBADO | $ {valor_sub_nuevo:,.0f}".replace(",", ".")
                                        )

                                    elif sub_estado_anterior == "APROBADO" and estado_subsidio != "APROBADO":
                                        movimientos.append(
                                            f"{fecha_mov} | SUBSIDIO REVERSADO | $ {valor_sub_anterior:,.0f}".replace(",", ".")
                                        )

                                # -------------------------
                                # CRÉDITO
                                # -------------------------
                                if des_estado_anterior != estado_credito or valor_des_anterior != valor_des_nuevo:

                                    if estado_credito == "SI" and valor_des_nuevo > 0:
                                        movimientos.append(
                                            f"{fecha_mov} | CRÉDITO DESEMBOLSADO | $ {valor_des_nuevo:,.0f}".replace(",", ".")
                                        )

                                    elif des_estado_anterior == "SI" and estado_credito != "SI":
                                        movimientos.append(
                                            f"{fecha_mov} | CRÉDITO REVERSADO | $ {valor_des_anterior:,.0f}".replace(",", ".")
                                        )

                                # -------------------------
                                # RECIBO (SI EXISTE)
                                # -------------------------
                                historial_anterior = str(st.session_state.db.at[idx_sel, "HISTORIAL_FINANCIERO"] or "")

                                nuevo_historial = historial_anterior

                                if movimientos:
                                    nuevo_historial += "\n" + "\n".join(movimientos)
                                num_cuota = st.session_state.get(f"num_cuota_pago_{idx_sel}", None)
                                if valor_r > 0:

                                    if num_cuota:
                                        concepto_hist = f"PAGO CUOTA {num_cuota}"
                                    else:
                                        concepto_hist = concepto_r

                                    registro_recibo = (
                                        f"{fecha_mov} | {concepto_hist} | "
                                        f"{formato_moneda(valor_r)} | {observaciones_r}"
                                    )

                                    nuevo_historial += "\n" + registro_recibo
                                    
                                # -------------------------
                                # ACTUALIZAR BASE DE DATOS
                                # -------------------------
                                st.session_state.db.at[idx_sel, c_subsidio] = estado_subsidio
                                st.session_state.db.at[idx_sel, c_val_subsidio] = valor_sub_nuevo

                                st.session_state.db.at[idx_sel, c_est_desembolso] = estado_credito
                                st.session_state.db.at[idx_sel, c_desembolso] = valor_des_nuevo

                                # -------------------------
                                # GUARDAR HISTORIAL
                                # -------------------------
                                st.session_state.db.at[idx_sel, "HISTORIAL_FINANCIERO"] = nuevo_historial.strip()

                                # -------------------------
                                # GUARDAR ARCHIVO
                                # -------------------------
                                st.session_state.db.to_excel("Base_Datos_TTC.xlsx", index=False)

                                # -------------------------
                                # MENSAJES DE CONFIRMACIÓN
                                # -------------------------
                                st.toast("✅ Cambios financieros guardados correctamente", icon="✅")
                                st.success("✔ Todos los cambios financieros fueron registrados y guardados en la base de datos.")
                                if valor_r > 0:
                                    if num_cuota:
                                        st.info(f"📌 Se registró correctamente el pago de la CUOTA {num_cuota}")
                                    else:
                                        st.info("📌 Se registró el recibo correctamente")
                            # ===============================
                            # 📜 HISTORIAL FINANCIERO
                            # ===============================

                            st.markdown("---")
                            st.subheader("📜 Historial Financiero")

                            historial_actual = str(
                                st.session_state.db.at[idx_sel, "HISTORIAL_FINANCIERO"] or ""
                            )

                            st.text_area(
                                "Movimientos registrados:",
                                value=historial_actual,
                                height=200,
                                disabled=True
                            )
                        elif seccion == "📑 Trámites":                
                            st.subheader("📊 Control de Trámites y Documentación")

                            val_prom_bd = str(cliente.get(c_promesa, "")).replace("nan", "").strip()
                            tiene_promesa = val_prom_bd != "" and val_prom_bd != "0"

                            val_esc_bd = str(cliente.get(c_escritura, "")).replace("nan", "").strip()
                            tiene_escritura = val_esc_bd != "" and val_esc_bd != "0"

                            val_entrega_bd = str(cliente.get("ENTREGA APTO", "")).replace("nan", "").strip()
                            ya_tiene_fecha = val_entrega_bd != "" and val_entrega_bd != "0"

                            # ===============================
                            # 🔢 PROGRESO GENERAL
                            # ===============================
                            progreso = sum([tiene_promesa, tiene_escritura, ya_tiene_fecha]) / 3

                            st.progress(progreso)
                            st.caption(f"Progreso del trámite: {int(progreso*100)}% completado")

                            st.markdown("---")

                            # ===============================
                            # 🛠️ PROMESA
                            # ===============================
                            with st.container(border=True):
                                st.markdown("### 🛠️ Promesa de Compraventa")

                                col1, col2 = st.columns([3, 1])

                                with col1:
                                    num_prom_input = st.text_input(
                                        "Número de Promesa:",
                                        value=val_prom_bd,
                                        disabled=tiene_promesa,
                                        placeholder="Ingrese el número..."
                                    )

                                with col2:
                                    st.write("")
                                    st.write("")
                                    if not tiene_promesa:
                                        if st.button("💾 Guardar", use_container_width=True, type="primary"):
                                            if num_prom_input:
                                                st.session_state.db.at[idx_sel, c_promesa] = num_prom_input
                                                st.success("✅ Promesa registrada")
                                                st.rerun()
                                            else:
                                                st.error("Dato obligatorio")
                                    else:
                                        st.success("✔ Registrado")

                            # ===============================
                            # 🖋️ ESCRITURACIÓN
                            # ===============================
                            with st.container(border=True):
                                st.markdown("### 🖋️ Escrituración")

                                e_col1, e_col2, e_col3 = st.columns([1.5, 1.5, 1])
                                
                                with e_col1:
                                    num_esc_input = st.text_input(
                                        "Número de Escritura:",
                                        value=val_esc_bd,
                                        disabled=tiene_escritura
                                    )
                                
                                with e_col2:
                                    notaria_input = st.text_input(
                                        "Notaría / Ciudad:",
                                        value=str(cliente.get(c_notaria, "")),
                                        disabled=tiene_escritura
                                    )
                                
                                with e_col3:
                                    st.write("")
                                    st.write("")
                                    if not tiene_escritura:
                                        if st.button("💾 Guardar", use_container_width=True, type="primary", key="btn_esc"):
                                            if num_esc_input and notaria_input:
                                                st.session_state.db.at[idx_sel, c_escritura] = num_esc_input
                                                st.session_state.db.at[idx_sel, c_notaria] = notaria_input
                                                st.success("✅ Escritura registrada")
                                                st.rerun()
                                            else:
                                                st.warning("Complete ambos campos")
                                    else:
                                        st.success("✔ Registrado")

                            # ===============================
                            # 🔑 ENTREGA
                            # ===============================
                            with st.container(border=True):
                                st.markdown("### 🔑 Entrega del Inmueble")

                                f_col1, f_col2 = st.columns([3, 1])
                                
                                with f_col1:
                                    try:
                                        fecha_previa = pd.to_datetime(val_entrega_bd).date() if ya_tiene_fecha else None
                                    except:
                                        fecha_previa = None

                                    nueva_fecha = st.date_input(
                                        "Fecha de entrega:",
                                        value=fecha_previa,
                                        disabled=ya_tiene_fecha
                                    )
                                
                                with f_col2:
                                    st.write("")
                                    st.write("")
                                    if not ya_tiene_fecha:
                                        if st.button("💾 Guardar", use_container_width=True, key="btn_ent_std"):
                                            if nueva_fecha:
                                                st.session_state.db.at[idx_sel, "ENTREGA APTO"] = str(nueva_fecha)
                                                st.success(f"✅ Entrega programada: {nueva_fecha}")
                                                st.rerun()
                                            else:
                                                st.warning("Seleccione una fecha válida.")
                                    else:
                                        st.success("✔ Registrado")

                            # ===============================
                            # 📌 RESUMEN FINAL
                            # ===============================
                            st.markdown("---")

                            if progreso == 1:
                                st.success("🎉 Trámite completo: Promesa, Escritura y Entrega registrados.")
                            else:
                                st.info("ℹ️ Complete los pasos restantes para finalizar el proceso.")

                            # Footer
                            st.caption(f"Registro Alameda | {datetime.now().strftime('%d/%m/%Y %H:%M')}")
                        elif seccion == "📝 Notas":
                            st.subheader(f"📝 Expediente Digital: {cliente[c_nom]}")
                            
                            # --- PARTE A: GESTIÓN DE NOTAS ---
                            with st.container(border=True):
                                st.markdown("#### Notas y Observaciones Internas")
                                # Traemos notas existentes
                                notas_actuales = str(cliente.get("OBSERVACIONES ", "")).replace("nan", "")
                                
                                nueva_nota = st.text_area("Editar observaciones:", value=notas_actuales, height=150)
                                
                                if st.button("💾 Guardar Notas", key="btn_notas"):
                                    st.session_state.db.at[idx_sel, "OBSERVACIONES "] = nueva_nota
                                    st.success("Notas actualizadas en la base de datos.")
                                    st.rerun()

                            st.markdown("---")

                            # --- PARTE B: CARGA DE SOPORTES (Documentación) ---
                            with st.container(border=True):
                                st.markdown("#### 📂 Soportes y Documentación")
                                st.info("Formatos permitidos: PDF, JPG, PNG. Máximo 200MB.")
                                
                                archivo_subido = st.file_uploader(
                                    "Cargar documento (Cédula, Comprobantes, Promesas firmadas, etc.)", 
                                    type=['pdf', 'jpg', 'png', 'jpeg'],
                                    key="uploader_soporte"
                                )

                                if archivo_subido is not None:
                                    nombre_final = f"{cliente[c_apto]}_{archivo_subido.name}"
                                    
                                    if st.button(f"🚀 Vincular '{archivo_subido.name}' al expediente"):
                                        st.success(f"Archivo '{nombre_final}' vinculado correctamente al inmueble {cliente[c_apto]}.")                      
            with tabs[1]:
                st.header("👤 Registro de Nuevo Cliente")

                # 1. FUNCIÓN DE VENTANA EMERGENTE (CONFIRMACIÓN)
                @st.dialog("⚠️ VERIFICAR INFORMACIÓN")
                def confirmar_registro_modal(datos):
                    st.warning("Revise los datos antes de consolidar el registro en la base de datos.")
                    
                    # Resumen visual para el usuario
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write(f"🏠 **Inmueble:** {datos['apto']}")
                        st.write(f"👤 **Cliente:** {datos['nombre']}")
                        st.write(f"🆔 **Cédula:** {datos['cedula']}")
                    with c2:
                        st.write(f"💰 **Valor:** {formato_moneda(datos['valor'])}")
                        st.write(f"📞 **Celular:** {datos['celular']}")
                        st.write(f"📧 **Email:** {datos['email']}")

                    st.markdown("---")
                    st.info("¿Desea proceder con el guardado?")
                    
                    col_si, col_no = st.columns(2)
                    with col_si:
                        if st.button("✅ SÍ, REGISTRAR", use_container_width=True):
                            try:
                                # Buscamos el índice del apto para actualizar la fila existente
                                idx = st.session_state.db[st.session_state.db[c_apto] == datos['apto']].index[0]
                                
                                # Mapeo de TODOS los campos originales
                                st.session_state.db.at[idx, "TORRE"] = datos['torre']
                                st.session_state.db.at[idx, c_nom] = datos['nombre']
                                st.session_state.db.at[idx, "CEDULA"] = datos['cedula']
                                st.session_state.db.at[idx, "CELULAR"] = datos['celular']
                                st.session_state.db.at[idx, "E-MAIL"] = datos['email']
                                st.session_state.db.at[idx, "CIUDAD"] = datos['ciudad']
                                st.session_state.db.at[idx, "ESTADO"] = datos['estado']
                                st.session_state.db.at[idx, c_v_venta] = datos['valor']
                                st.session_state.db.at[idx, "DESCUENTO"] = datos['descuento']
                                st.session_state.db.at[idx, "ASESOR"] = datos['asesor']

                                st.success(f"🚀 ¡Registro del Apto {datos['apto']} completado con éxito!")
                                import time
                                time.sleep(2)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error al guardar: {e}")

                    with col_no:
                        if st.button("❌ CANCELAR", use_container_width=True):
                            st.rerun()

                # 2. OBTENER LISTA DE DISPONIBLES
                df_actual = st.session_state.db
                mask_disp = (df_actual[c_nom].isna()) | (df_actual[c_nom].astype(str).str.strip() == "")
                lista_disponibles = sorted(df_actual[mask_disp][c_apto].unique().tolist())

                # 3. FORMULARIO DE CAPTURA CON TODOS LOS CAMPOS ORIGINALES
                if lista_disponibles:
                    with st.form("form_registro_completo_seguro"):
                        st.markdown("#### 📑 Información Básica")
                        f1, f2, f3 = st.columns(3)
                        with f1: n_apto = st.selectbox("Apartamento:", lista_disponibles)
                        with f2: n_torre = st.selectbox("Torre:", [3])
                        with f3: n_asesor = st.text_input("Asesor Responsable:")

                        st.markdown("---")
                        st.markdown("#### 👤 Datos del Comprador")
                        d1, d2 = st.columns(2)
                        with d1:
                            n_nombre = st.text_input("Nombre Completo:")
                            n_cedula = st.text_input("Cédula / NIT:")
                            n_celular = st.text_input("Celular de Contacto:")
                        with d2:
                            n_email = st.text_input("Correo Electrónico:")
                            n_ciudad = st.text_input("Ciudad de Residencia:")
                            n_estado = st.selectbox("Estado Inicial:", ["RESERVADO", "VENDIDO", "PROSPECTO"])

                        st.markdown("---")
                        st.markdown("#### 💰 Condiciones Comerciales")
                        v1, v2 = st.columns(2)
                        with v1:
                            # Sugerimos el valor actual del Excel para ese apto
                            v_sug = limpiar_valor(df_actual[df_actual[c_apto] == n_apto].iloc[0].get(c_v_venta, 0))
                            n_valor = st.number_input("Valor de Venta ($):", min_value=0, value=int(v_sug), step=1000000)
                        with v2:
                            n_desc = st.text_input("Descuento Concedido:", value="0")

                        # Este botón NO guarda, solo abre la confirmación
                        validar = st.form_submit_button("🚀 PREPARAR REGISTRO", use_container_width=True)

                    # 4. DISPARADOR DE LA VENTANA DE SEGURIDAD
                    if validar:
                        if n_apto and n_nombre and n_cedula:
                            paquete_datos = {
                                "apto": n_apto, "torre": n_torre, "asesor": n_asesor.upper(),
                                "nombre": n_nombre.upper(), "cedula": n_cedula, "celular": n_celular,
                                "email": n_email, "ciudad": n_ciudad, "estado": n_estado,
                                "valor": n_valor, "descuento": n_desc
                            }
                            confirmar_registro_modal(paquete_datos)
                        else:
                            st.warning("⚠️ Los campos Apto, Nombre y Cédula son obligatorios.")
                else:
                    st.info("✅ No hay apartamentos disponibles para registro en la Torre 3.")
            with tabs[2]:
                st.subheader("📊 Análisis de Cartera")

                # 1. Preparación de Datos (Categorías Unificadas)
                data_cartera_total = []
                data_cuota_inicial = []
                data_subsidios_pend = []
                data_creditos_pend = []
                
                total_cartera_pendiente = 0
                total_pendiente_ci = 0

                for idx, row in st.session_state.db.iterrows():
                    if str(row.get(c_nom, "")).strip() in ["", "nan"]:
                        continue

                    # --- Valores Base ---
                    v_venta = int(limpiar_valor(row.get(c_v_venta)))
                    v_pago = int(limpiar_valor(row.get(c_pago)))
                    v_can_ci = int(limpiar_valor(row.get(c_cancelado_ci)))
                    
                    # Lógica Subsidios
                    val_sub_raw = row.get(c_val_subsidio)
                    est_sub_raw = str(row.get(c_subsidio)).strip().upper()
                    v_sub = int(limpiar_valor(val_sub_raw)) if est_sub_raw == "APROBADO" else 0

                    # Lógica Créditos
                    val_des_raw = row.get(c_desembolso)
                    est_des_raw = str(row.get(c_est_desembolso)).strip().upper()
                    v_des = int(limpiar_valor(val_des_raw)) if est_des_raw == "SI" else 0
                    
                   # --- Lógica de Fechas y Mora (CORREGIDA PARA 12 CUOTAS) ---
                    dias_mora_maximo = 0  # Para saber cuál es el atraso más grave
                    total_vencido_cliente = 0
                    cuotas_pendientes_info = []

                    for i in range(1, 13):
                        f_cuota = row.get(f"FECHA_C{i}")
                        v_cuota = row.get(f"VALOR_C{i}", 0)
                        e_cuota = row.get(f"ESTADO_C{i}", "PENDIENTE")
                        
                        # Si la cuota tiene fecha y no ha sido pagada
                        if pd.notnull(f_cuota) and f_cuota != "" and e_cuota == "PENDIENTE":
                            try:
                                # Normalizar fecha de la cuota
                                if hasattr(f_cuota, 'date'): f_base = f_cuota.date()
                                elif isinstance(f_cuota, str): f_base = pd.to_datetime(f_cuota).date()
                                else: f_base = f_cuota
                                
                                # Calcular diferencia de días
                                diferencia = (date.today() - f_base).days
                                
                                if diferencia > 0:
                                    # Esta cuota está vencida
                                    total_vencido_cliente += v_cuota
                                    cuotas_pendientes_info.append(f"C{i} ({diferencia} días)")
                                    # Guardamos el retraso más largo para la alerta principal
                                    if diferencia > dias_mora_maximo:
                                        dias_mora_maximo = diferencia
                            except:
                                continue

                    # Al final del ciclo, 'dias_mora_maximo'
                    dias_mora = dias_mora_maximo

                    # --- A. Cálculos ---
                    s_real = v_venta - (v_pago + v_can_ci + v_sub + v_des)
                    ci_requerida = int(v_venta * 0.10)
                    s_ci_pendiente = ci_requerida - v_can_ci

                    # Llenar Cartera Total
                    if s_real > 1000:
                        total_cartera_pendiente += s_real
                        data_cartera_total.append({
                            "Inmueble": row.get(c_apto, "N/A"), "Cliente": row.get(c_nom, "N/A"),
                            "Estado": row.get("ESTADO", "N/A"), "Saldo Pendiente": s_real,
                            "Asesor": row.get("ASESOR", "N/A"), "Mora": dias_mora
                        })

                    # Llenar Cuota Inicial
                    if s_ci_pendiente > 1000:
                        total_pendiente_ci += s_ci_pendiente
                        data_cuota_inicial.append({
                            "Inmueble": row.get(c_apto, "N/A"), "Cliente": row.get(c_nom, "N/A"),
                            "Pendiente CI": s_ci_pendiente, "CI Total": ci_requerida, "Mora": dias_mora
                        })
                    
                    # Llenar Subsidios Pendientes (Si tiene valor y NO está aprobado)
                    if int(limpiar_valor(val_sub_raw)) > 0 and est_sub_raw != "APROBADO":
                        data_subsidios_pend.append({
                            "Inmueble": row.get(c_apto, "N/A"), "Cliente": row.get(c_nom, "N/A"),
                            "Valor": limpiar_valor(val_sub_raw), "Estado": est_sub_raw
                        })

                    # Llenar Créditos Pendientes (Si tiene valor y NO está desembolsado)
                    if int(limpiar_valor(val_des_raw)) > 0 and est_des_raw != "SI":
                        data_creditos_pend.append({
                            "Inmueble": row.get(c_apto, "N/A"), "Cliente": row.get(c_nom, "N/A"),
                            "Valor": limpiar_valor(val_des_raw), "Banco": row.get(c_banco, "N/A")
                        })

                # 2. Visualización de Métricas Superiores (4 Columnas)
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Cartera Total", formato_moneda(total_cartera_pendiente))
                m2.metric("Pendiente C.I.", formato_moneda(total_pendiente_ci))
                m3.metric("Subsidios Pend.", len(data_subsidios_pend))
                m4.metric("Créditos Pend.", len(data_creditos_pend))

                st.markdown("---")

                # 3. Integración de las 4 Pestañas arriba
                sub_tabs = st.tabs([
                    "🔴 Gestión Cobro Total", 
                    "💰 Cuotas Iniciales", 
                    "📑 Subsidios", 
                    "🏦 Créditos"
                ])

                # --- PESTAÑA 1: GESTIÓN TOTAL ---
                with sub_tabs[0]:
                    if data_cartera_total:
                        df_export = pd.DataFrame(data_cartera_total).sort_values(by="Saldo Pendiente", ascending=False)
                        for _, fila in df_export.iterrows():
                            saldo = float(fila.get("Saldo Pendiente", 0))
                            mora = fila.get("Mora", 0)
                            color_alerta = "#e74c3c" if saldo > 50000000 or mora > 30 else "#f39c12"
                            with st.container(border=True):
                                c_inf, c_monto, c_mora = st.columns([2.5, 1.5, 1])
                                with c_inf:
                                    st.markdown(f"**Unidad: {fila['Inmueble']}**\n\n👤 {fila['Cliente']}")
                                    st.caption(f"Asesor: {fila['Asesor']} | Estado: {fila['Estado']}")
                                with c_monto:
                                    st.markdown(f"<div style='text-align:right;'><span style='color:{color_alerta}; font-size:1.2rem; font-weight:bold;'>{formato_moneda(saldo)}</span><br><small style='color:gray;'>SALDO TOTAL</small></div>", unsafe_allow_html=True)
                                with c_mora:
                                    if mora > 0:
                                        st.markdown(f"<div style='text-align:center; background:#fdecea; border:1px solid #e74c3c; border-radius:5px; padding:5px;'><span style='color:#e74c3c; font-weight:bold;'>{mora} Días</span><br><small style='color:#e74c3c;'>MORA</small></div>", unsafe_allow_html=True)
                                    else: st.markdown("<div style='text-align:center; color:gray; padding-top:10px;'><small>✅ Al día</small></div>", unsafe_allow_html=True)
                    else: st.success("✨ Cartera total al día.")

                # --- PESTAÑA 2: CUOTAS INICIALES ---
                with sub_tabs[1]:
                    if data_cuota_inicial:
                        df_ci = pd.DataFrame(data_cuota_inicial).sort_values(by="Pendiente CI", ascending=False)
                        for _, fila in df_ci.iterrows():
                            with st.container(border=True):
                                c_inf, c_monto, c_mora = st.columns([2.5, 1.5, 1])
                                with c_inf:
                                    st.markdown(f"**Apto: {fila['Inmueble']}**\n\n👤 {fila['Cliente']}")
                                    st.caption(f"10% Requerido: {formato_moneda(fila['CI Total'])}")
                                with c_monto:
                                    st.markdown(f"<div style='text-align:right;'><span style='color:#d35400; font-size:1.2rem; font-weight:bold;'>{formato_moneda(fila['Pendiente CI'])}</span><br><small style='color:gray;'>PENDIENTE C.I.</small></div>", unsafe_allow_html=True)
                                with c_mora:
                                    if fila['Mora'] > 0:
                                        st.markdown(f"<div style='text-align:center; background:#fff9e6; border:1px solid #f39c12; border-radius:5px; padding:5px;'><span style='color:#d35400; font-weight:bold;'>{fila['Mora']} Días</span><br><small style='color:#d35400;'>MORA</small></div>", unsafe_allow_html=True)
                    else: st.success("✨ Cuotas iniciales recaudadas.")

                # --- PESTAÑA 3: SUBSIDIOS PENDIENTES ---
                with sub_tabs[2]:
                    if data_subsidios_pend:
                        st.write("### 📌 Trámites de Subsidio en Curso")
                        for item in data_subsidios_pend:
                            with st.container(border=True):
                                c1, c2 = st.columns([3, 1])
                                c1.markdown(f"**Apto {item['Inmueble']}** - {item['Cliente']}")
                                c1.caption(f"Estado: {item['Estado']}")
                                c2.markdown(f"<div style='text-align:right; color:#2980b9; font-weight:bold;'>{formato_moneda(item['Valor'])}</div>", unsafe_allow_html=True)
                    else: st.success("✅ No hay subsidios pendientes por legalizar.")

                # --- PESTAÑA 4: CRÉDITOS SIN DESEMBOLSO ---
                with sub_tabs[3]:
                    if data_creditos_pend:
                        st.write("### 🏦 Créditos Pendientes de Desembolso")
                        for item in data_creditos_pend:
                            with st.container(border=True):
                                c1, c2 = st.columns([3, 1])
                                c1.markdown(f"**Apto {item['Inmueble']}** - {item['Cliente']}")
                                c1.caption(f"Entidad: {item['Banco']}")
                                c2.markdown(f"<div style='text-align:right; color:#27ae60; font-weight:bold;'>{formato_moneda(item['Valor'])}</div>", unsafe_allow_html=True)
                    else: st.success("✅ Todos los créditos han sido desembolsados.")

            with tabs[3]: # 📊 Informe Gerencial
                st.subheader("📊 Dashboard de Control Ejecutivo")

                if 'db' in st.session_state and not st.session_state.db.empty:
                    df_g = st.session_state.db.copy()
                    
                    # --- 1. PROCESAMIENTO ---
                    def num(v):
                        return limpiar_valor(v)

                    total_ventas = df_g[c_v_venta].apply(num).sum()
                    recaudo_total = df_g[c_pago].apply(num).sum() + df_g[c_cancelado_ci].apply(num).sum()
                    cartera_total = total_ventas - recaudo_total
                    
                    df_g['ES_DISPONIBLE'] = (df_g[c_nom].isna()) | (df_g[c_nom].astype(str).str.strip() == "")
                    condicion_prospecto = (df_g[c_nom].notna()) & (df_g[c_nom].astype(str).str.strip() != "") & \
                                        ((df_g[c_apto].isna()) | (df_g[c_apto].astype(str).str.strip() == ""))
                    
                    if "ESTADO" in df_g.columns:
                        condicion_prospecto = condicion_prospecto | (df_g["ESTADO"].astype(str).str.upper().str.strip() == "PROSPECTO")

                    df_prospectos = df_g[condicion_prospecto].copy()
                    prospectos_count = len(df_prospectos)
                    vendidas = df_g[~df_g['ES_DISPONIBLE'] & ~condicion_prospecto].copy()
                    total_unidades = len(df_g[df_g[c_apto].notna()])
                    ocupacion = round((len(vendidas) / total_unidades) * 100, 1) if total_unidades > 0 else 0

                    col_estado = "ESTADO" if "ESTADO" in df_g.columns else None
                    resumen_estados = vendidas[col_estado].fillna("VENDIDO").str.upper().value_counts().to_dict() if col_estado else {"VENDIDO": len(vendidas)}
                    
                    df_disp = df_g[df_g['ES_DISPONIBLE'] & df_g[c_apto].notna()].copy()
                    df_disp['PISO_NUM'] = df_disp[c_apto].astype(str).str[:-2]
                    pisos_disponibles = sorted(df_disp['PISO_NUM'].unique(), key=lambda x: int(x) if x.isdigit() else 0, reverse=True)
                    total_vencidas = total_vencidas if 'total_vencidas' in locals() else 0
                    total_flujo = total_flujo if 'total_flujo' in locals() else 0
                    total_pagadas_mes = total_pagadas_mes if 'total_pagadas_mes' in locals() else 0
                    cant_vencidas = cant_vencidas if 'cant_vencidas' in locals() else 0
                    cant_proximas = cant_proximas if 'cant_proximas' in locals() else 0
                    # --- 1.3 INTELIGENCIA GERENCIAL (SEPARADA) ---
                    porc_cartera = round((cartera_total / total_ventas) * 100, 1) if total_ventas > 0 else 0
                    porc_vencida = round((total_vencidas / (total_flujo + total_pagadas_mes + 1)) * 100, 1)

                    # 🟦 ANÁLISIS CORTO (DASHBOARD)
                    txt_ia = f"""
                    El proyecto presenta un {ocupacion}% de ocupación y una cartera del {porc_cartera}%.
                    Se identifican {cant_vencidas} cuotas vencidas que requieren atención.
                    """

                    # 🟨 ANÁLISIS PROFUNDO (PDF)
                    txt_analisis = f"""
                    El comportamiento financiero del proyecto refleja una ocupación del {ocupacion}%,
                    con un nivel de cartera correspondiente al {porc_cartera}% del total vendido.

                    Se identifican {cant_vencidas} cuotas en estado de mora, lo que representa un riesgo del {porc_vencida}% 
                    sobre el flujo proyectado. Adicionalmente, existen {cant_proximas} cuotas próximas a vencer, lo que exige 
                    una gestión preventiva para evitar deterioro en la cartera.

                    El flujo proyectado del mes asciende a {formato_moneda(total_flujo)}, lo cual permite estimar la capacidad 
                    de recaudo en el corto plazo y tomar decisiones financieras oportunas.
                    """

                    # Sugerencias (se mantiene igual)
                    sugerencias = []

                    if cant_vencidas > 0:
                        sugerencias.append(f"Priorizar gestión de recaudo inmediato sobre {cant_vencidas} cuotas vencidas.")

                    if cant_proximas > 0:
                        sugerencias.append(f"Activar recordatorios preventivos para {cant_proximas} cuotas próximas a vencer.")

                    if prospectos_count > 0:
                        sugerencias.append(f"Convertir {prospectos_count} prospectos activos en ventas.")

                    if ocupacion < 70:
                        sugerencias.append("Fortalecer estrategia comercial para aumentar velocidad de ventas.")

                    if not sugerencias:
                        sugerencias.append("El proyecto presenta un comportamiento estable. Mantener estrategia actual.")

                    txt_sug = "💡 **Sugerencias IA:**<br>" + "<br>".join([f"• {s}" for s in sugerencias])
                    # --- 1.1 CUOTAS CUOTA INICIAL 
                    from datetime import datetime

                    cuotas_mes = []
                    cuotas_pagadas = []

                    hoy = datetime.now()
                    mes_actual = hoy.month
                    anio_actual = hoy.year

                    for _, row in df_g.iterrows():
                        for i in range(1, 13):  # C1 a C12
                            try:
                                fecha = pd.to_datetime(row.get(f"FECHA_C{i}"), errors='coerce')
                                estado = str(row.get(f"ESTADO_C{i}", "")).upper().strip()
                                valor = num(row.get(f"VALOR_C{i}", 0))

                                if pd.notnull(fecha) and valor > 0:
                                    if fecha.month == mes_actual and fecha.year == anio_actual:
                                        
                                        if estado == "PAGADA":
                                            cuotas_pagadas.append(valor)
                                        else:
                                            cuotas_mes.append(valor)

                            except:
                                pass

                    total_cuotas_mes = sum(cuotas_mes)
                    total_pagadas_mes = sum(cuotas_pagadas)
                    cantidad_cuotas_mes = len(cuotas_mes)
                    cantidad_pagadas_mes = len(cuotas_pagadas)
                    # --- 1.2 SEMÁFORO DE CARTERA (AVANZADO) ---
                    from datetime import timedelta

                    cuotas_vencidas = []
                    cuotas_proximas = []
                    flujo_proyectado = []

                    for _, row in df_g.iterrows():
                        for i in range(1, 13):
                            try:
                                fecha = pd.to_datetime(row.get(f"FECHA_C{i}"), errors='coerce')
                                estado = str(row.get(f"ESTADO_C{i}", "")).upper().strip()
                                valor = num(row.get(f"VALOR_C{i}", 0))

                                if pd.notnull(fecha) and valor > 0:

                                    # SOLO CUOTAS NO PAGADAS
                                    if estado != "PAGADA":

                                        # 🔴 VENCIDAS
                                        if fecha < hoy:
                                            cuotas_vencidas.append(valor)

                                        # 🟡 PRÓXIMAS (7 días)
                                        elif hoy <= fecha <= hoy + timedelta(days=7):
                                            cuotas_proximas.append(valor)

                                        # 🔵 PROYECCIÓN DEL MES
                                        if fecha.month == mes_actual and fecha.year == anio_actual:
                                            flujo_proyectado.append(valor)

                            except:
                                pass

                    # RESULTADOS
                    total_vencidas = sum(cuotas_vencidas)
                    total_proximas = sum(cuotas_proximas)
                    total_flujo = sum(flujo_proyectado)

                    cant_vencidas = len(cuotas_vencidas)
                    cant_proximas = len(cuotas_proximas)
                    cant_flujo = len(flujo_proyectado)

                    # --- 2. RENDERIZADO DASHBOARD (PANTALLA) ---
                    filas_html = ""
                    for p in pisos_disponibles:
                        aptos_p = df_disp[df_disp['PISO_NUM'] == p].sort_values(by=c_apto)
                        btns = "".join([f'<div style="background:white; border:1.5px solid #1F4E79; color:#1F4E79; border-radius:4px; padding:3px 8px; font-weight:bold; min-width:48px; text-align:center; font-size:14px; box-shadow:1px 1px 3px rgba(0,0,0,0.1);">{f[c_apto]}</div>' for _, f in aptos_p.iterrows()])
                        filas_html += f'<div style="display:flex; align-items:center; gap:10px; margin-bottom:8px;"><div style="min-width:70px; background:#1F4E79; color:white; padding:5px; border-radius:4px; text-align:center; font-size:11px; font-weight:bold;">PISO {p}</div><div style="display:flex; flex-wrap:nowrap; gap:6px; overflow-x:auto; padding-bottom:2px;">{btns}</div></div>'

                    html_estados = "".join([f"<div style='display:flex; justify-content:space-between; padding:3px 0; border-bottom:1px solid #eee; font-size:13px;'><span>{k}</span><b>{v} Unds</b></div>" for k, v in resumen_estados.items()])
                    html_prosp_lista = "".join([f"<li style='font-size:13px; margin-bottom:2px;'>{r[c_nom]}</li>" for _, r in df_prospectos.head(8).iterrows()])

                    html_ui = f"""
                    <div style="font-family:sans-serif; background:#f4f7f9; padding:20px; border-radius:15px; border:1px solid #cfd8dc;">
                        <div style="display:flex; justify-content:space-between; border-bottom:2px solid #1F4E79; padding-bottom:10px; margin-bottom:15px;">
                            <h2 style="color:#1F4E79; margin:0; font-size:22px;">REPORTE ALAMEDA T3</h2>
                            <b style="font-size:18px; color:#1F4E79;">{ocupacion}% Vendido</b>
                        </div>
                        <div style="background:#e3f2fd; padding:12px; border-radius:10px; border-left:6px solid #2196f3; margin-bottom:20px;">
                            <p style="font-size:14px; margin:4px 0;">{txt_ia}</p>
                            <p style="font-size:14px; margin:0; font-weight:bold; color:#0d47a1;">{txt_sug}</p>
                        </div>
                        <div style="display:grid; grid-template-columns: 1fr 1fr 1fr; gap:12px; margin-bottom:20px;">
                            <div style="background:white; padding:12px; border-radius:10px; border-top:4px solid #28a745; text-align:center; box-shadow:0 2px 4px rgba(0,0,0,0.05);"><small style="color:gray;">RECAUDO</small><br><b style="font-size:17px;">{formato_moneda(recaudo_total)}</b></div>
                            <div style="background:white; padding:12px; border-radius:10px; border-top:4px solid #dc3545; text-align:center; box-shadow:0 2px 4px rgba(0,0,0,0.05);"><small style="color:gray;">CARTERA</small><br><b style="font-size:17px;">{formato_moneda(cartera_total)}</b></div>
                            <div style="background:white; padding:12px; border-radius:10px; border-top:4px solid #f39c12; text-align:center; box-shadow:0 2px 4px rgba(0,0,0,0.05);"><small style="color:gray;">PROSPECTOS</small><br><b style="font-size:17px;">{prospectos_count}</b></div>
                            <div style="background:white; padding:12px; border-radius:10px; border-top:4px solid #6f42c1; text-align:center; box-shadow:0 2px 4px rgba(0,0,0,0.05);">
                                <small style="color:gray;">CUOTAS MES (PENDIENTES)</small><br>
                                <b style="font-size:17px;">{cantidad_cuotas_mes} | {formato_moneda(total_cuotas_mes)}</b>
                            </div>

                            <div style="background:white; padding:12px; border-radius:10px; border-top:4px solid #20c997; text-align:center; box-shadow:0 2px 4px rgba(0,0,0,0.05);">
                                <small style="color:gray;">CUOTAS PAGADAS MES</small><br>
                                <b style="font-size:17px;">{cantidad_pagadas_mes} | {formato_moneda(total_pagadas_mes)}</b>
                            </div>
                            <div style="background:white; padding:12px; border-radius:10px; border-top:4px solid #dc3545; text-align:center; box-shadow:0 2px 4px rgba(0,0,0,0.05);">
                                <small style="color:gray;">🔴 CUOTAS VENCIDAS</small><br>
                                <b style="font-size:17px;">{cant_vencidas} | {formato_moneda(total_vencidas)}</b>
                            </div>

                            <div style="background:white; padding:12px; border-radius:10px; border-top:4px solid #ffc107; text-align:center; box-shadow:0 2px 4px rgba(0,0,0,0.05);">
                                <small style="color:gray;">🟡 PRÓXIMAS (7 DÍAS)</small><br>
                                <b style="font-size:17px;">{cant_proximas} | {formato_moneda(total_proximas)}</b>
                            </div>

                            <div style="background:white; padding:12px; border-radius:10px; border-top:4px solid #17a2b8; text-align:center; box-shadow:0 2px 4px rgba(0,0,0,0.05);">
                                <small style="color:gray;">🔵 FLUJO PROYECTADO MES</small><br>
                                <b style="font-size:17px;">{cant_flujo} | {formato_moneda(total_flujo)}</b>
                            </div> 
                        </div>
                        <div style="display:grid; grid-template-columns: 1.3fr 1fr; gap:15px;">
                            <div style="background:white; padding:15px; border-radius:12px; border:1px solid #eee; box-shadow:0 2px 4px rgba(0,0,0,0.02);">
                                <h5 style="margin:0 0 12px 0; font-size:15px; color:#1F4E79; border-bottom:1px solid #eee; padding-bottom:5px;">🏢 MAPA DE DISPONIBILIDAD</h5>
                                <div style="max-height:280px; overflow-y:auto; padding-right:5px;">{filas_html}</div>
                            </div>
                            <div style="display:flex; flex-direction:column; gap:15px;">
                                <div style="background:white; padding:15px; border-radius:12px; border:1px solid #eee; box-shadow:0 2px 4px rgba(0,0,0,0.02);">
                                    <h5 style="margin:0 0 8px 0; font-size:14px; color:#1F4E79;">ESTADO DE VENTAS</h5>{html_estados}
                                </div>
                                <div style="background:#fff9e6; padding:15px; border-radius:12px; border:1px solid #f39c12;">
                                    <h5 style="margin:0 0 8px 0; font-size:14px; color:#d35400;">PROSPECTOS NUEVOS</h5>
                                    <ul style="margin:0; padding-left:18px; color:#555;">{html_prosp_lista if prospectos_count > 0 else '<li>Sin prospectos</li>'}</ul>
                                </div>
                            </div>
                        </div>
                    </div>
                    """
                    st.components.v1.html(html_ui, height=620, scrolling=True)

                    # --- 3. GENERACIÓN DE PDF ---
                    st.markdown("---")
                    try:
                        import matplotlib.pyplot as plt
                        from reportlab.lib.pagesizes import A4
                        from reportlab.lib import colors
                        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, ListFlowable, ListItem
                        from reportlab.lib.styles import getSampleStyleSheet
                        from io import BytesIO

                        pdf_buf = BytesIO()
                        doc = SimpleDocTemplate(pdf_buf, pagesize=A4, margin=40)
                        elems = []
                        sd = getSampleStyleSheet()
                        from reportlab.lib.styles import ParagraphStyle
                        style_h2 = ParagraphStyle(
                            'CustomH2',
                            parent=sd['Heading2'],
                            fontSize=12,
                            leading=15,
                            spaceAfter=6,
                            spaceBefore=4
                        )

                        style_h3 = ParagraphStyle(
                            'CustomH3',
                            parent=sd['Heading3'],
                            fontSize=10,
                            leading=12,
                            spaceAfter=4,
                            spaceBefore=2
                        )

                        from reportlab.lib.enums import TA_JUSTIFY
                        style_normal = ParagraphStyle(
                            'CustomNormal',
                            parent=sd['Normal'],
                            fontName='Helvetica',
                            fontSize=9,
                            leading=15,  # 🔥 clave para que se vea bien justificado
                            spaceAfter=6,
                            alignment=TA_JUSTIFY
                        )
                        from reportlab.lib.enums import TA_CENTER

                        style_title = ParagraphStyle(
                            'CustomTitle',
                            parent=sd['Title'],
                            fontName='Helvetica-Bold',
                            fontSize=14,
                            leading=16,
                            alignment=TA_CENTER,
                            spaceAfter=8
                        )
                        from datetime import datetime
                        fecha_reporte = datetime.now().strftime("%d/%m/%Y")
                        version_reporte = "Versión 1.0"
                        elems.append(Paragraph("INFORME ESTRATÉGICO ALAMEDA", style_title))
                        elems.append(Spacer(1, 4))
                        info_doc = f"Fecha: {fecha_reporte} | {version_reporte}"
                        elems.append(Paragraph(info_doc, style_normal))
                        elems.append(Spacer(1, 6))
                        elems.append(Paragraph("ANÁLISIS ESTRATÉGICO", style_h2))
                        elems.append(Spacer(1, 6))

                        # 🔥 LIMPIAR TEXTO (CLAVE)
                        texto_limpio = " ".join(str(txt_analisis).split())

                        # 🔥 AGREGAR CORRECTAMENTE
                        elems.append(Paragraph(texto_limpio, style_normal))
                        
                        # Sugerencias limpias para PDF (sin HTML conflictivo)
                        elems.append(Paragraph("RECOMENDACIONES", style_h3))

                        sug_items = [ListItem(Paragraph(s, style_normal)) for s in sugerencias]
                        elems.append(ListFlowable(sug_items, bulletType='bullet'))
                        elems.append(Spacer(1, 6))
                        # --- RESUMEN EJECUTIVO ---
                        elems.append(Paragraph("RESUMEN EJECUTIVO", style_h2))
                        elems.append(Spacer(1, 6))

                        data_resumen = [
                            ["Indicador", "Valor"],
                            ["Ocupación del Proyecto", f"{ocupacion}%"],
                            ["Total Ventas", formato_moneda(total_ventas)],
                            ["Recaudo Total", formato_moneda(recaudo_total)],
                            ["Cartera Pendiente", formato_moneda(cartera_total)],
                            ["Cuotas Vencidas", f"{cant_vencidas} / {formato_moneda(total_vencidas)}"],
                            ["Cuotas Próximas (7 días)", f"{cant_proximas} / {formato_moneda(total_proximas)}"],
                            ["Flujo Proyectado Mes", f"{cant_flujo} / {formato_moneda(total_flujo)}"],
                        ]

                        t_resumen = Table(data_resumen, colWidths=[240, 160])
                        t_resumen.setStyle(TableStyle([
                            ('BACKGROUND',(0,0),(-1,0),colors.HexColor("#1F4E79")),
                            ('TEXTCOLOR',(0,0),(-1,0),colors.white),
                            ('GRID',(0,0),(-1,-1),0.5,colors.grey),
                            ('FONTSIZE',(0,0),(-1,-1),10)
                        ]))
                        elems.append(t_resumen)
                        elems.append(Spacer(1, 10))

                        # Tabla de Estados y KPIs
                        data_pdf = [["INDICADOR / ESTADO", "CANTIDAD / VALOR"], ["RECAUDO TOTAL", formato_moneda(recaudo_total)], ["CARTERA TOTAL", formato_moneda(cartera_total)]]
                        for k, v in resumen_estados.items(): data_pdf.append([f"UNIDADES EN {k}", f"{v} Unds"])
                        t = Table(data_pdf, colWidths=[240, 160])
                        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor("#1F4E79")),('TEXTCOLOR',(0,0),(-1,0),colors.white),('GRID',(0,0),(-1,-1),0.5,colors.grey),('FONTSIZE',(0,0),(-1,-1),10)]))
                        elems.append(t)
                        elems.append(Spacer(1, 10))

                        # Mapa de Pisos en PDF (RESTAURADO)
                        elems.append(Paragraph("MAPA DE DISPONIBILIDAD (UNIDADES LIBRES)", style_h3))
                        for piso in pisos_disponibles:
                            aptos = df_disp[df_disp['PISO_NUM'] == piso].sort_values(by=c_apto)[c_apto].tolist()
                            if aptos:
                                f_pdf = [f"PISO {piso}"] + aptos
                                t_p = Table([f_pdf], colWidths=[70] + [50]*(len(f_pdf)-1), rowHeights=28)
                                t_p.setStyle(TableStyle([('BACKGROUND', (0,0), (0,0), colors.HexColor("#1F4E79")), ('TEXTCOLOR', (0,0), (0,0), colors.white), ('GRID', (1,0), (-1,0), 1, colors.HexColor("#1F4E79")), ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('FONTSIZE', (0,0), (-1,-1), 10)]))
                                elems.append(t_p)
                                elems.append(Spacer(1, 5))

                        # Lista de Prospectos en PDF (RESTAURADO)
                        if not df_prospectos.empty:
                            elems.append(Spacer(1, 8))
                            elems.append(Paragraph("LISTADO DE PROSPECTOS RECIENTES", style_h3))
                            p_items = [ListItem(Paragraph(str(r[c_nom]), style_normal)) for _, r in df_prospectos.iterrows()]
                            elems.append(ListFlowable(p_items, bulletType='bullet'))
                        def agregar_pie(canvas, doc):
                            canvas.saveState()
                            width, height = A4

                            # Línea
                            canvas.setStrokeColor(colors.grey)
                            canvas.setLineWidth(0.5)
                            canvas.line(40, 40, width - 40, 40)

                            # Texto branding
                            canvas.setFont("Helvetica", 8)
                            canvas.drawString(40, 25, "Proyecto Alameda T3 | Informe Confidencial")

                            # Número de página
                            canvas.drawRightString(width - 40, 25, f"Página {doc.page}")

                            canvas.restoreState()
                        doc.build(elems, onFirstPage=agregar_pie, onLaterPages=agregar_pie)
                        st.download_button(label="📩 Descargar Reporte PDF Completo", data=pdf_buf.getvalue(), file_name="Reporte_Alameda_T3.pdf", mime="application/pdf", use_container_width=True)

                    except Exception as e:
                        st.error(f"Error en PDF: {e}")

                else:

                    st.warning("Cargue la base de datos para ver el informe.")
