from fpdf import FPDF
import streamlit as st
import pandas as pd
import os
from io import BytesIO
from datetime import datetime

# --- 1. CONFIGURACIÓN VISUAL Y SEGURIDAD ---
st.set_page_config(page_title="CRM TTC Alameda", layout="wide", page_icon="🏢")

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
# 2. DEFINICIÓN DE FUNCIONES (Primero se definen)
# ==========================================

def login():
    _, col_central, _ = st.columns([1, 1.5, 1])
    with col_central:
        st.image("https://cdn-icons-png.flaticon.com/512/6073/6073873.png", width=80)
        st.title("Acceso TTC Alameda")
        with st.form("login_form"):
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("INGRESAR AL SISTEMA"):
                # CONFIGURACIÓN DE USUARIOS
                if u == "Administrador" and p == "admin123":
                    st.session_state.autenticado = True
                    st.session_state.perfil = "ADMINISTRADOR"
                    st.session_state.usuario_actual = u
                    st.rerun()
                elif u == "Ventas" and p == "ventas123":
                    st.session_state.autenticado = True
                    st.session_state.perfil = "COMERCIAL"
                    st.session_state.usuario_actual = u
                    st.rerun()
                else:
                    st.error("❌ Credenciales incorrectas")

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
                unidad_p = c2.selectbox("¿Qué unidad busca?", ["Apartamento", "Local Comercial", "Parqueadero Extra"])
                
                notas_p = st.text_area("Observaciones de la preventa")
                
                if st.form_submit_button("💾 GUARDAR INTERESADO"):
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
            if st.session_state.prospectos.empty:
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
                    num_str = str(v).replace("$", "").replace(".", "").replace(",", "").replace(" ", "").strip()
                    return f"$ {int(num_str):,.0f}".replace(",", ".")
                except:
                    return "$ 0"

            def limpiar_valor(v):
                try:
                    if pd.isna(v) or str(v).strip() == "" or str(v).lower() == "nan":
                        return 0
                    s_val = str(v).replace("$", "").replace(".", "").replace(",", "").replace(" ", "").strip()
                    return int(float(s_val))
                except:
                    return 0

            # --- FUNCION PARA GENERAR PDF (NUEVA) ---
            def generar_pdf_recibo(datos_cliente, datos_recibo):
                pdf = FPDF()
                pdf.add_page()
                
                # --- LOGO EN EL PDF ---
                # Posición: x=10, y=8 | Ancho: 30mm (puedes ajustar el 30 si se ve muy pequeño o grande)
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
                        df_temp[col] = df_temp[col].astype(str).replace(r'\.0$', '', regex=True).replace("nan", "")
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
            cols = db.columns.tolist()

            # Mapeo de columnas (Tus variables originales)
            c_apto = next((c for c in cols if any(x in c for x in ["INMUEBLE", "APTO", "UNIDAD"])), cols[0])
            c_nom  = next((c for c in cols if any(x in c for x in ["RECIBIMOS", "NOMBRE", "CLIENTE"])), cols[1])
            c_cc = next((c for c in cols if any(x in c for x in ["CEDULA", "NIT", "IDENTI", "DOCUMENTO", "C.C", "CC"])), None)
            c_cedula = "CEDULA"
            c_promesa = "# PROMESA"
            c_cancelado_ci = next((c for c in cols if "TOTAL" in c and "CANCELADO" in c and "C.I" in c), "TOTAL_CANCELADO_CI")
            c_pago = next((c for c in cols if any(x in c for x in ["NETO", "PAGADO", "VALOR_RECIBIDO", "TOTAL_ABONADO"])), "TOTAL_ABONADO")
            c_saldo = next((c for c in cols if any(x in c for x in ["SALDO", "PENDIENTE"])), "SALDO_PENDIENTE")
            c_v_venta = next((c for c in cols if "VENTA" in c and "VALOR" in c), "VALOR_VENTA")
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
            nombres_tabs = ["🔍 Gestión Comercial", "➕ Registro", "💰 Cartera Ejecutiva", "📊 Informe Gerencial"]
            tabs = st.tabs(nombres_tabs)

                # --- TAB 1: BUSCADOR ---
            with tabs[0]:
                st.markdown("### 🔎 Central de Información")            
                query_externa = st.session_state.get('busqueda_input', '')
                if query_externa:
                    st.info(f"📍 Revisando Cartera del Inmueble: **{query_externa}**")
                    if st.button("✅ Cargar Datos del Cliente"):
                        query = query_externa
                    else:
                        query = query_externa        
                col_busq_espacio, col_busq_real = st.columns([1, 2])
                with col_busq_real:
                    with st.form(key="search_form"):
                        c_txt, c_btn = st.columns([3, 1])
                        query = c_txt.text_input("Buscar cliente:", value=query_externa, placeholder="Inmueble o Nombre...").strip().upper()
                        submit_search = c_btn.form_submit_button("🔍 Consultar")
                if query or submit_search or query_externa:
                    final_query = query if query else query_externa
                    mask = st.session_state.db.apply(lambda row: row.astype(str).str.contains(final_query, case=False).any(), axis=1)
                    resultados = st.session_state.db[mask]
                    if query_externa != "" and submit_search:
                        st.session_state.busqueda_input = ""
                    if not resultados.empty:
                        opciones = {f"Apto {row[c_apto]} - {row[c_nom]}": idx for idx, row in resultados.iterrows()}
                        indice_default = 0 if len(opciones) > 1 else 1                
                        seleccion = st.selectbox("🎯 Seleccionado:", options=["-- Seleccionar --"] + list(opciones.keys()), index=indice_default)               
                        if seleccion != "-- Seleccionar --":
                            idx_sel = opciones[seleccion]
                            cliente = st.session_state.db.loc[idx_sel]
                            # -------- CUOTA INICIAL = 10% DEL VALOR DE VENTA --------
                            valor_venta = limpiar_valor(cliente.get(c_v_venta))
                            cuota_inicial_automatica = round(valor_venta * 0.10, 2)

                            # Cálculos Financieros Rápidos
                            venta = limpiar_valor(cliente.get(c_v_venta))
                            abonos_base = limpiar_valor(cliente.get(c_pago)) 
                            cancelado_ci = limpiar_valor(cliente.get(c_cancelado_ci)) 
                            sub_valor = limpiar_valor(cliente.get(c_val_subsidio))
                            desembolso_val = limpiar_valor(cliente.get(c_desembolso))
                            
                            estado_des_actual = str(cliente.get(c_est_desembolso)).strip().upper()
                            desembolso_efectivo = desembolso_val if estado_des_actual == "SI" else 0
                            estado_sub_actual = str(cliente.get(c_subsidio)).strip().upper()
                            subsidio_efectivo = sub_valor if estado_sub_actual == "APROBADO" else 0
                            
                            total_abonado_real = abonos_base + cancelado_ci + subsidio_efectivo + desembolso_efectivo
                            saldo_real = venta - total_abonado_real
                            
                            st.divider()
                            st.markdown(f"## 👤 {cliente[c_nom]}")
                            st.markdown(f"**🆔 CC:** {cliente[c_cedula]} | **📍 Inmueble:** Apto {cliente[c_apto]}")

                            seccion = st.pills("Sección:", ["📋 Contacto", "💰 Financiero", "📑 Trámites", "📝 Notas"], selection_mode="single", default="📋 Contacto")

                            if seccion == "📋 Contacto":
                                c1, c2, c3 = st.columns(3)
                                c1.info(f"📞 **Teléfono:**\n{cliente.get(c_tel, 'No registrado')}")
                                c2.info(f"📧 **Email:**\n{cliente.get(c_mail, 'No registrado')}")
                                c3.info(f"🏙️ **Ubicación:**\n{cliente.get(c_direc, 'No registrado')}")
                        
                            elif seccion == "💰 Financiero":
                                # ===============================
                                # 1️⃣ MÉTRICAS
                                # ===============================
                                f1, f2 = st.columns(2)
                                f1.metric("Valor Venta", formato_moneda(venta))

                                col_colores1, col_colores2 = st.columns(2)
                                with col_colores1:
                                    st.info(f"### Abonado Total: {formato_moneda(total_abonado_real)}")
                                with col_colores2:
                                    st.error(f"### Saldo pendiente: {formato_moneda(saldo_real)}")
                                st.markdown("---")
                                st.metric(
                                    "💰 Cuota Inicial Requerida (10%)",
                                    formato_moneda(cuota_inicial_automatica)
                                )
                                # -------- CÁLCULO REAL CUOTA INICIAL --------
                                cuota_inicial_real = float(cuota_inicial_automatica)
                                total_cancelado_ci_real = limpiar_valor(cliente.get(c_cancelado_ci))
                                porcentaje_ci = 0
                                if cuota_inicial_real > 0:
                                    porcentaje_ci = (total_cancelado_ci_real / cuota_inicial_real) * 100
                                st.write(f"💵 Total abonado C.I.: {formato_moneda(total_cancelado_ci_real)}")
                                st.write(f"📊 Cumplimiento Cuota Inicial: {porcentaje_ci:.2f}%")
                                st.progress(min(int(porcentaje_ci), 100))
                                from datetime import date, datetime
                                fecha_compromiso_guardada = cliente.get("FECHA_COMPROMISO_CI")
                                # -------- CONVERTIR FECHA SI ES STRING --------
                                if fecha_compromiso_guardada:
                                    if isinstance(fecha_compromiso_guardada, str):
                                        try:
                                            fecha_compromiso_guardada = datetime.strptime(
                                                fecha_compromiso_guardada, "%Y-%m-%d"
                                            ).date()
                                        except:
                                            fecha_compromiso_guardada = None
                                # -------- VALIDAR ESTADO --------
                                if fecha_compromiso_guardada:

                                    dias_diferencia = (date.today() - fecha_compromiso_guardada).days

                                    if porcentaje_ci >= 100:
                                        st.success("✅ Cuota inicial completada")

                                    else:
                                        if dias_diferencia > 0:
                                            st.error(f"🚨 Cuota inicial vencida hace {dias_diferencia} días")
                                        else:
                                            dias_restantes = abs(dias_diferencia)
                                            st.warning(f"⏳ Faltan {dias_restantes} días para cumplir la cuota inicial")

                                # ===============================
                                # 2️⃣ DATOS DE CRÉDITO Y SUBSIDIO
                                # ===============================
                                with st.container(border=True):
                                    st.subheader("Datos de Crédito y Subsidio")
                                    c_cred1, c_cred2 = st.columns(2)
                                    with c_cred1:
                                        nuevo_ccf = st.text_input("CCF (Caja Compensación):", value=str(cliente[c_ccf]))
                                        nuevo_c_ini = st.text_input("Cuota Inicial ($):", value=formato_moneda(cliente[c_c_inicial]))
                                        nuevo_can_ci = st.text_input("Total Cancelado C.I. ($):", value=formato_moneda(cliente[c_cancelado_ci]))
                                        fecha_compromiso_ci = st.date_input(
                                            "📅 Fecha Compromiso Cuota Inicial",
                                            value=cliente.get("FECHA_COMPROMISO_CI")
                                        )

                                    with c_cred2:
                                        st.write(f"🏦 **Entidad:** {cliente.get(c_entidad)}")
                                    st.divider()
                                    c_sub_est, c_des_est = st.columns(2)
                                    with c_sub_est:
                                        ops_sub = ["TRAMITADO", "POR TRAMITAR", "NO APLICA", "APROBADO"]
                                        idx_sub = ops_sub.index(estado_sub_actual) if estado_sub_actual in ops_sub else 1
                                        nuevo_sub_est = st.selectbox("Estado Subsidio:", ops_sub, index=idx_sub)
                                    with c_des_est:
                                        nuevo_est_des = st.selectbox(
                                            "¿Credito Desembolsado?",
                                            ["NO", "SI"],
                                            index=1 if estado_des_actual == "SI" else 0
                                        )
                                    c_sub_val, c_des_val = st.columns(2)
                                    nuevo_val_sub_str = c_sub_val.text_input("Monto Subsidio ($):", value=formato_moneda(sub_valor))
                                    nuevo_val_des_str = c_des_val.text_input("Monto Crédito ($):", value=formato_moneda(desembolso_val))

                                # ===============================
                                # 3️⃣ REGISTRO ABONO + RECIBO
                                # ===============================
                                st.subheader("📄 Registro abono")
                                with st.expander("⚙️ Configurar Datos del Recibo", expanded=True):
                                    col_f1, col_f2 = st.columns(2)
                                    fecha_r = col_f1.date_input("Fecha de pago:", datetime.now())
                                    ciudad_r = col_f2.text_input("Ciudad:", "NOBSA")
                                    col_f3, col_f4 = st.columns(2)
                                    concepto_r = col_f3.selectbox(
                                        "Concepto de pago:",
                                        ["SEPARACIÓN", "CUOTA INICIAL", "ABONO EXTRAORDINARIO", "OTRO"]
                                    )
                                    valor_r = col_f4.number_input("Valor a recibir ($):", min_value=0, step=100000)

                                    texto_auto_letras = f"{numero_a_letras(valor_r)} PESOS M/CTE" if valor_r > 0 else ""
                                    letras_r = st.text_input("La suma de (en letras):", value=texto_auto_letras)

                                    entidad_r = st.text_input(
                                        "Entidad de recaudo:",
                                        value="BANCOLOMBIA"
                                    )
                                    if st.button("👁️ Generar Vista Previa del Recibo"):
                                        with st.container(border=True):
                                            h1, h2, h3 = st.columns([1, 1, 1])
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
                                            r_c1, r_c2 = st.columns(2)
                                            with r_c1:
                                                st.write(f"**RECIBIMOS DE:** {cliente[c_nom]}")
                                                st.write(f"**C.C. / NIT:** {cliente[c_cc]}")
                                                st.write(f"**CIUDAD:** {ciudad_r}")
                                            with r_c2:
                                                st.write("**PROYECTO:** ALAMEDA EL BOSQUE")
                                                st.write(f"**INMUEBLE:** Apto {cliente[c_apto]}")
                                                st.write(f"**TELÉFONO:** {cliente[c_tel]}")

                                            st.info(f"**LA SUMA DE:** {letras_r.upper()}")
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
                                                "letras": letras_r
                                            }

                                            pdf_bytes = generar_pdf_recibo(datos_pdf_cliente, datos_pdf_recibo)
                                            # =========================================
                                            # SUMAR ABONO AUTOMÁTICO AL GENERAR RECIBO
                                            # =========================================
                                            if valor_r > 0:

                                                valor_actual = limpiar_valor(st.session_state.db.at[idx_sel, c_pago])
                                                nuevo_total = valor_actual + valor_r
                                                st.session_state.db.at[idx_sel, c_pago] = str(int(nuevo_total))

                                                # Registrar en historial
                                                fecha_mov = datetime.now().strftime("%d/%m/%Y %H:%M")
                                                historial_actual = str(st.session_state.db.at[idx_sel, "HISTORIAL_FINANCIERO"])

                                                movimiento = f"{fecha_mov} | ABONO RECIBO ({concepto_r}) | $ {valor_r:,.0f}".replace(",", ".")
                                                nuevo_historial = (historial_actual + "\n" + movimiento).strip()

                                                st.session_state.db.at[idx_sel, "HISTORIAL_FINANCIERO"] = nuevo_historial

                                            st.download_button(
                                                label="📥 DESCARGAR RECIBO PDF",
                                                data=pdf_bytes,
                                                file_name=f"Recibo_{cliente[c_apto]}_{datetime.now().strftime('%Y%m%d')}.pdf",
                                                mime="application/pdf"
                                            )

                                # ===============================
                                # 4️⃣ BOTÓN GUARDAR (AL FINAL)
                                # ===============================
                                
                                if st.button("💾 Guardar Cambios Financieros", use_container_width=True):
                                    # 1. Actualización en memoria
                                    st.session_state.db.at[idx_sel, c_ccf] = nuevo_ccf
                                    st.session_state.db.at[idx_sel, c_c_inicial] = str(limpiar_valor(nuevo_c_ini))
                                    st.session_state.db.at[idx_sel, c_cancelado_ci] = str(limpiar_valor(nuevo_can_ci))
                                    st.session_state.db.at[idx_sel, "FECHA_COMPROMISO_CI"] = fecha_compromiso_ci
                                    st.session_state.db.at[idx_sel, c_subsidio] = nuevo_sub_est
                                    st.session_state.db.at[idx_sel, c_val_subsidio] = str(limpiar_valor(nuevo_val_sub_str))
                                    st.session_state.db.at[idx_sel, c_est_desembolso] = nuevo_est_des
                                    st.session_state.db.at[idx_sel, c_desembolso] = str(limpiar_valor(nuevo_val_des_str))

                                    # 2. Lógica de movimientos e historial
                                    fecha_mov = datetime.now().strftime("%d/%m/%Y %H:%M")
                                    movimientos = []
                                    
                                    valor_ci_anterior = limpiar_valor(cliente.get(c_cancelado_ci))
                                    valor_ci_nuevo = limpiar_valor(nuevo_can_ci)

                                    if valor_ci_nuevo != valor_ci_anterior:
                                        diferencia = valor_ci_nuevo - valor_ci_anterior
                                        if diferencia != 0:
                                            tipo = "ABONO CUOTA INICIAL" if diferencia > 0 else "AJUSTE CUOTA INICIAL"
                                            movimientos.append(f"{fecha_mov} | {tipo} | $ {abs(diferencia):,.0f}".replace(",", "."))

                                    # 3. Guardar historial
                                    hist_act = str(st.session_state.db.at[idx_sel, "HISTORIAL_FINANCIERO"] or "")
                                    if movimientos:
                                        nuevo_hist = hist_act + "\n" + "\n".join(movimientos)
                                        st.session_state.db.at[idx_sel, "HISTORIAL_FINANCIERO"] = nuevo_hist.strip()

                                    # 4. Guardado físico (Persistencia)
                                    if guardar_cambios_db():
                                        st.success("✅ Cambios guardados permanentemente.")
                                        st.rerun()
                                    else:
                                        st.error("❌ Error al escribir en el archivo. ¿Está abierto en Excel?")

                                    # -------- Guardar valores en base --------
                                    st.session_state.db.at[idx_sel, c_ccf] = nuevo_ccf
                                    st.session_state.db.at[idx_sel, c_c_inicial] = str(limpiar_valor(nuevo_c_ini))
                                    st.session_state.db.at[idx_sel, c_cancelado_ci] = str(limpiar_valor(nuevo_can_ci))
                                    st.session_state.db.at[idx_sel, c_subsidio] = nuevo_sub_est
                                    st.session_state.db.at[idx_sel, c_val_subsidio] = str(limpiar_valor(nuevo_val_sub_str))
                                    st.session_state.db.at[idx_sel, c_est_desembolso] = nuevo_est_des
                                    st.session_state.db.at[idx_sel, c_desembolso] = str(limpiar_valor(nuevo_val_des_str))

                                    # -------- HISTORIAL FINANCIERO INTELIGENTE --------
                                    fecha_mov = datetime.now().strftime("%d/%m/%Y %H:%M")
                                    movimientos = []

                                    # Valores anteriores (antes de guardar)
                                    sub_estado_anterior = str(cliente.get(c_subsidio)).strip().upper()
                                    des_estado_anterior = str(cliente.get(c_est_desembolso)).strip().upper()
                                    valor_sub_anterior = limpiar_valor(cliente.get(c_val_subsidio))
                                    valor_des_anterior = limpiar_valor(cliente.get(c_desembolso))
                                    valor_ci_anterior = limpiar_valor(cliente.get(c_cancelado_ci))

                                    # Valores nuevos
                                    valor_ci_nuevo = limpiar_valor(nuevo_can_ci)
                                    valor_sub_nuevo = limpiar_valor(nuevo_val_sub_str)
                                    valor_des_nuevo = limpiar_valor(nuevo_val_des_str)

                                    # ---- CUOTA INICIAL ----
                                    if valor_ci_nuevo != valor_ci_anterior:
                                        diferencia = valor_ci_nuevo - valor_ci_anterior
                                        if diferencia != 0:
                                            tipo = "ABONO CUOTA INICIAL" if diferencia > 0 else "AJUSTE CUOTA INICIAL"
                                            movimientos.append(
                                                f"{fecha_mov} | {tipo} | $ {abs(diferencia):,.0f}".replace(",", ".")
                                            )

                                    # ---- SUBSIDIO ----
                                    if sub_estado_anterior != nuevo_sub_est or valor_sub_anterior != valor_sub_nuevo:

                                        if nuevo_sub_est == "APROBADO" and valor_sub_nuevo > 0:
                                            movimientos.append(
                                                f"{fecha_mov} | SUBSIDIO APROBADO | $ {valor_sub_nuevo:,.0f}".replace(",", ".")
                                            )

                                        elif sub_estado_anterior == "APROBADO" and nuevo_sub_est != "APROBADO":
                                            movimientos.append(
                                                f"{fecha_mov} | SUBSIDIO REVERSADO | $ {valor_sub_anterior:,.0f}".replace(",", ".")
                                            )

                                    # ---- CRÉDITO ----
                                    if des_estado_anterior != nuevo_est_des or valor_des_anterior != valor_des_nuevo:

                                        if nuevo_est_des == "SI" and valor_des_nuevo > 0:
                                            movimientos.append(
                                                f"{fecha_mov} | CRÉDITO DESEMBOLSADO | $ {valor_des_nuevo:,.0f}".replace(",", ".")
                                            )

                                        elif des_estado_anterior == "SI" and nuevo_est_des != "SI":
                                            movimientos.append(
                                                f"{fecha_mov} | CRÉDITO REVERSADO | $ {valor_des_anterior:,.0f}".replace(",", ".")
                                            )

                                    # ---- GUARDAR HISTORIAL ----
                                    historial_anterior = str(st.session_state.db.at[idx_sel, "HISTORIAL_FINANCIERO"] or "")
                                    if movimientos:
                                        nuevo_historial = historial_anterior + "\n" + "\n".join(movimientos)
                                        st.session_state.db.at[idx_sel, "HISTORIAL_FINANCIERO"] = nuevo_historial.strip()
                                    st.success("Cambios guardados correctamente.")
                                    st.rerun()
                                # ===============================
                                # 📜 HISTORIAL FINANCIERO
                                # ===============================

                                st.markdown("---")
                                st.subheader("📜 Historial Financiero")

                                historial_actual = str(st.session_state.db.at[idx_sel, "HISTORIAL_FINANCIERO"] or "")

                                st.text_area(
                                    "Movimientos registrados:",
                                    value=historial_actual,
                                    height=200,
                                    disabled=True
                                )
                            elif seccion == "📑 Trámites":
                                st.subheader("📊 Control de Trámites y Documentación")
                                
                                # --- DATOS DE LA BASE ---
                                val_prom_bd = str(cliente.get(c_promesa, "")).replace("nan", "").strip()
                                tiene_promesa = val_prom_bd != "" and val_prom_bd != "0"

                                # --- DISEÑO: TARJETA DE ESTADO SUPERIOR ---
                                with st.container(border=True):
                                    col_icon, col_txt, col_badge = st.columns([0.6, 3, 1.5])
                                    
                                    with col_icon:
                                        # Icono centralizado
                                        st.markdown("<h1 style='text-align: center; margin-top: 10px;'>📜</h1>", unsafe_allow_html=True)
                                    
                                    with col_txt:
                                        st.markdown(f"### Promesa de Compraventa")
                                        if tiene_promesa:
                                            st.write(f"Documento vinculado legalmente al inmueble **{cliente[c_apto]}**.")
                                        else:
                                            st.write("Pendiente de asignación de número de Promesa.")

                                    with col_badge:
                                        st.write("") 
                                        if tiene_promesa:
                                            st.markdown(f"""
                                                <div style='background-color:#d4edda; color:#155724; padding:12px; border-radius:10px; 
                                                text-align:center; font-weight:bold; border: 1px solid #c3e6cb;'>
                                                    ✅ VALIDADO<br>
                                                    <span style='font-size: 0.8em; font-weight: normal;'>Ref: {val_prom_bd}</span>
                                                </div>
                                            """, unsafe_allow_html=True)
                                        else:
                                            st.markdown("""
                                                <div style='background-color:#fff3cd; color:#856404; padding:12px; border-radius:10px; 
                                                text-align:center; font-weight:bold; border: 1px solid #ffeeba;'>
                                                    ⏳ PENDIENTE
                                                </div>
                                            """, unsafe_allow_html=True)

                                st.markdown(" ") 

                                # --- SECCIÓN DE ACCIÓN Y REGISTRO ---
                                with st.container(border=True):
                                    st.markdown("#### 🛠️ Datos de Promesa")
                                    t1, t2 = st.columns([2, 1])
                                    
                                    with t1:
                                        num_prom_input = st.text_input(
                                            "Número de Promesa de Compraventa:",
                                            value=val_prom_bd,
                                            disabled=tiene_promesa,
                                            placeholder="Ingreselo aquí...",
                                            label_visibility="visible"
                                        )

                                    with t2:
                                        st.write("") 
                                        st.write("") 
                                        if not tiene_promesa:
                                            if st.button("📝 GUARDAR", use_container_width=True, type="primary"):
                                                if num_prom_input:
                                                    st.session_state.db.at[idx_sel, c_promesa] = num_prom_input
                                                    st.success("✅ Registro exitoso")
                                                    st.rerun()
                                                else:
                                                    st.error("Dato obligatorio")
                                        else:
                                            st.button("🔒 DOCUMENTO CERRADO", use_container_width=True, disabled=True)

                                # Pie de página ejecutivo
                                st.divider()
                                st.caption(f"Registro Alameda | Fecha de consulta: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
                                st.markdown(" ") 
                                st.subheader("🖋️ Escrituración")

                                # --- DATOS DE ESCRITURA ---
                                val_esc_bd = str(cliente.get(c_escritura, "")).replace("nan", "").strip()
                                tiene_escritura = val_esc_bd != "" and val_esc_bd != "0"

                                with st.container(border=True):
                                    col_icon2, col_txt2, col_badge2 = st.columns([0.6, 3, 1.5])
                                    
                                    with col_icon2:
                                        st.markdown("<h1 style='text-align: center; margin-top: 10px;'>⚖️</h1>", unsafe_allow_html=True)
                                    
                                    with col_txt2:
                                        st.markdown("### Firma de Escrituras")
                                        st.write("Registro de protocolo notarial y titulación del inmueble.")

                                    with col_badge2:
                                        st.write("") 
                                        if tiene_escritura:
                                            st.markdown(f"""
                                                <div style='background-color:#e3f2fd; color:#0d47a1; padding:12px; border-radius:10px; 
                                                text-align:center; font-weight:bold; border: 1px solid #bbdefb;'>
                                                    📝 FIRMADO<br>
                                                    <span style='font-size: 0.8em; font-weight: normal;'>Esc: {val_esc_bd}</span>
                                                </div>
                                            """, unsafe_allow_html=True)
                                        else:
                                            st.markdown("""
                                                <div style='background-color:#f5f5f5; color:#616161; padding:12px; border-radius:10px; 
                                                text-align:center; font-weight:bold; border: 1px solid #e0e0e0;'>
                                                    🌑 SIN FIRMAR
                                                </div>
                                            """, unsafe_allow_html=True)

                                # --- CAMPOS DE REGISTRO DE ESCRITURA ---
                                with st.container(border=True):
                                    e_col1, e_col2, e_col3 = st.columns([1.5, 1.5, 1])
                                    
                                    with e_col1:
                                        num_esc_input = st.text_input("Número de Escritura:", value=val_esc_bd, disabled=tiene_escritura)
                                    
                                    with e_col2:
                                        notaria_input = st.text_input("Notaría / Ciudad:", value=str(cliente.get(c_notaria, "")), disabled=tiene_escritura)
                                    
                                    with e_col3:
                                        st.write("") # Alineación
                                        st.write("")
                                        if not tiene_escritura:
                                            if st.button("💾 REGISTRAR", use_container_width=True, type="primary", key="btn_esc"):
                                                if num_esc_input and notaria_input:
                                                    st.session_state.db.at[idx_sel, c_escritura] = num_esc_input
                                                    st.session_state.db.at[idx_sel, c_notaria] = notaria_input
                                                    st.success("✅ Registrado")
                                                    st.rerun()
                                                else:
                                                    st.warning("Complete ambos campos")
                                        else:
                                            st.button("🔒 CERRADO", use_container_width=True, disabled=True, key="btn_esc_lock")
                                # --- BLOQUE DE ENTREGA DEL INMUEBLE  ---
                                st.markdown("---")                                              
                                val_entrega_bd = str(cliente.get("ENTREGA APTO", "")).replace("nan", "").strip()
                                ya_tiene_fecha = val_entrega_bd != "" and val_entrega_bd != "0"

                                # 2. Tarjeta Visual Ejecutiva
                                with st.container(border=True):
                                    col_icon3, col_txt3, col_badge3 = st.columns([0.6, 3, 1.5])
                                    
                                    with col_icon3:
                                        st.markdown("<h1 style='text-align: center; margin-top: 10px;'>🔑</h1>", unsafe_allow_html=True)
                                    
                                    with col_txt3:
                                        st.markdown("### Entrega del Inmueble")
                                        st.write("Programación de entrega de llaves y firma de acta de recibo.")

                                    with col_badge3:
                                        st.write("") 
                                        if ya_tiene_fecha:
                                            st.markdown(f"""
                                                <div style='background-color:#fff3e0; color:#e65100; padding:12px; border-radius:10px; 
                                                text-align:center; font-weight:bold; border: 1px solid #ffe0b2;'>
                                                    📅 PROGRAMADA<br>
                                                    <span style='font-size: 0.8em; font-weight: normal;'>{val_entrega_bd}</span>
                                                </div>
                                            """, unsafe_allow_html=True)
                                        else:
                                            st.markdown("""
                                                <div style='background-color:#fafafa; color:#9e9e9e; padding:12px; border-radius:10px; 
                                                text-align:center; font-weight:bold; border: 1px solid #eeeeee;'>
                                                    ⏳ SIN FECHA
                                                </div>
                                            """, unsafe_allow_html=True)

                                # 3. Formulario de Selección de Fecha
                                with st.container(border=True):
                                    f_col1, f_col2 = st.columns([3, 1])
                                    
                                    with f_col1:
                                        # Intentamos convertir el valor de la BD a formato fecha para el calendario
                                        try:
                                            fecha_previa = pd.to_datetime(val_entrega_bd).date() if ya_tiene_fecha else None
                                        except:
                                            fecha_previa = None

                                        nueva_fecha = st.date_input(
                                            "Seleccione Fecha Tentativa de Entrega:",
                                            value=fecha_previa,
                                            disabled=ya_tiene_fecha,
                                            help="Haga clic para abrir el calendario."
                                        )
                                    
                                    with f_col2:
                                        st.write("") # Espaciadores para alinear con el input
                                        st.write("")
                                        if not ya_tiene_fecha:
                                            # Botón estándar (sin type="primary" para que sea gris/normal)
                                            if st.button("💾 AGENDAR", use_container_width=True, key="btn_ent_std"):
                                                if nueva_fecha:
                                                    st.session_state.db.at[idx_sel, "ENTREGA APTO"] = str(nueva_fecha)
                                                    st.success(f"✅ Entrega programada para el {nueva_fecha}")
                                                    st.rerun()
                                                else:
                                                    st.warning("Seleccione una fecha válida.")
                                        else:
                                            # Botón deshabilitado cuando ya está guardado
                                            st.button("🔒 REGISTRADO", use_container_width=True, disabled=True, key="btn_ent_lock_std")
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
                    else:
                        st.warning(f"No se encontraron resultados para: {final_query}")               
            with tabs[1]:
                # --- SECCIÓN: REGISTRO DE NUEVOS CLIENTES ---
                st.header("👤 Registro de Nuevo Cliente")

                with st.container(border=True):
                    st.markdown("#### 📑 Información Básica del Inmueble")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        nuevo_apto = st.text_input("Apartamento (Ej: 101):")
                    with col2:
                        nuevo_torre = st.selectbox("Torre:", [3]) # Por ahora fijo en Torre 3
                    with col3:
                        nuevo_asesor = st.text_input("Asesor Responsable:")

                    st.markdown("---")
                    st.markdown("#### 👤 Datos del Comprador")
                    c1, c2 = st.columns(2)
                    
                    with c1:
                        nuevo_nombre = st.text_input("Nombre Completo:")
                        nueva_cedula = st.text_input("Cédula / NIT:")
                        nuevo_celular = st.text_input("Celular de Contacto:")
                    
                    with c2:
                        nuevo_email = st.text_input("Correo Electrónico:")
                        nueva_ciudad = st.text_input("Ciudad de Residencia:")
                        nuevo_estado = st.selectbox("Estado Inicial:", ["RESERVADO", "SEPARADO"])

                    st.markdown("---")
                    st.markdown("#### 💰 Condiciones Comerciales")
                    v1, v2 = st.columns(2)
                    
                    with v1:
                        nuevo_valor = st.number_input("Valor de Venta ($):", min_value=0, step=1000000)
                    with v2:
                        nuevo_descuento = st.text_input("Descuento Concedido:", value="0")

                    # BOTÓN DE REGISTRO (Estilo Ejecutivo)
                    st.write("")
                    if st.button("🚀 REGISTRAR NUEVO CLIENTE", use_container_width=True):
                        if nuevo_apto and nuevo_nombre and nueva_cedula:
                            # Crear la nueva fila (Diccionario)
                            nueva_fila = {
                                "TORRE": nuevo_torre,
                                "APTO ": nuevo_apto,
                                "NOMBRE COMPLETO": nuevo_nombre.upper(),
                                "CEDULA": nueva_cedula,
                                "CELULAR": nuevo_celular,
                                "E-MAIL": nuevo_email,
                                "CIUDAD": nueva_ciudad,
                                "ESTADO": nuevo_estado,
                                "VALOR VENTA": nuevo_valor,
                                "DESCUENTO": nuevo_descuento,
                                "ASESOR": nuevo_asesor.upper()
                            }
                            
                            # Lógica para añadir al DataFrame
                            try:
                                import pandas as pd
                                nuevo_df = pd.DataFrame([nueva_fila])
                                st.session_state.db = pd.concat([st.session_state.db, nuevo_df], ignore_index=True)
                                
                                # Guardar cambios en el archivo físico
                                # st.session_state.db.to_csv("Nombre_de_tu_archivo.csv", index=False)
                                
                                st.success(f"✅ Cliente {nuevo_nombre} registrado con éxito en el Apto {nuevo_apto}")
                                st.balloons() # Toque de celebración
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error al guardar: {e}")
                        else:
                            st.warning("⚠️ Los campos Apto, Nombre y Cédula son obligatorios.")
            with tabs[2]:
                st.subheader("📊 Análisis de Cartera y Recuperación")

                # 1. Cálculo de Cartera
                data_cartera = []
                total_cartera_pendiente = 0

                for idx, row in st.session_state.db.iterrows():
                    if str(row.get(c_nom, "")).strip() in ["", "nan"]:
                        continue

                    v_venta = limpiar_valor(row.get(c_v_venta))
                    v_pago = limpiar_valor(row.get(c_pago))
                    v_can_ci = limpiar_valor(row.get(c_cancelado_ci))
                    v_sub = limpiar_valor(row.get(c_val_subsidio)) if str(row.get(c_subsidio)).strip().upper() == "APROBADO" else 0
                    v_des = limpiar_valor(row.get(c_desembolso)) if str(row.get(c_est_desembolso)).strip().upper() == "SI" else 0
                    
                    s_real = v_venta - (v_pago + v_can_ci + v_sub + v_des)

                    if s_real > 1000:
                        total_cartera_pendiente += s_real
                        data_cartera.append({
                            "Inmueble": row.get(c_apto, "N/A"),
                            "Cliente": row.get(c_nom, "N/A"),
                            "Estado": row.get("ESTADO", "N/A"),
                            "Saldo Pendiente": s_real,
                            "Asesor": row.get("ASESOR", "N/A")
                        })

                # 2. Visualización de Métricas
                m1, m2 = st.columns(2)
                with m1:
                    st.metric("Cartera Total Pendiente", formato_moneda(total_cartera_pendiente), delta_color="inverse")
                with m2:
                    st.metric("Clientes con Saldo Mora", len(data_cartera))

                st.markdown("---")

                # 3. Listado Prioritario o Mensaje de Éxito
                if data_cartera:
                    st.write("### 📋 Gestión de Cobro Prioritaria")
                    df_export = pd.DataFrame(data_cartera).sort_values(by="Saldo Pendiente", ascending=False)

                    for _, fila in df_export.iterrows():
                        color_alerta = "#e74c3c" if fila['Saldo Pendiente'] > 50000000 else "#f39c12"
                        
                        with st.container(border=True):
                            c_inf, c_monto, c_accion = st.columns([2.5, 1.5, 1])
                            with c_inf:
                                st.markdown(f"**Unidad: {fila['Inmueble']}**")
                                st.markdown(f"👤 {fila['Cliente']}")
                                st.caption(f"Asesor: {fila['Asesor']} | Estado: {fila['Estado']}")
                            with c_monto:
                                st.markdown(f"<div style='text-align:right;'><span style='color:{color_alerta}; font-size:1.2rem; font-weight:bold;'>{formato_moneda(fila['Saldo Pendiente'])}</span><br><small style='color:gray;'>SALDO PENDIENTE</small></div>", unsafe_allow_html=True)
                            
                    # 4. Botón de descarga (Alineado correctamente fuera del bucle for)
                    st.markdown(" ")
                    csv_data = df_export.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Descargar Reporte de Cartera",
                        data=csv_data,
                        file_name=f"cartera_alameda_{datetime.now().strftime('%d_%m_%y')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                else:
                    st.success("✨ Cartera al día. No se registran saldos pendientes.")
            with tabs[3]:
                st.header("📊 Tablero de Control Gerencial - Proyecto")
                st.write(f"Corte al: {datetime.now().strftime('%d/%m/%Y')}")

                from datetime import date, timedelta, datetime

                df = st.session_state.db
                cols = df.columns.tolist()

                # ===============================
                # 1️⃣ MAPEO DE COLUMNAS
                # ===============================
                col_venta = next((c for c in cols if 'VALOR VENTA' in c.upper()), None)
                col_recaudo = next((c for c in cols if 'TOTAL CANCELADO C.I' in c.upper()), None)
                col_val_sub = next((c for c in cols if 'VALOR SUBSIDIO' in c.upper()), None)
                col_est_sub = next((c for c in cols if 'ESTADO SUBSIDIO' in c.upper()), None)
                col_val_cred = next((c for c in cols if 'VALOR CRÉDITO' in c.upper()), None)
                col_desembolso = next((c for c in cols if 'DESEMBOLSO' in c.upper() and 'VALOR' not in c.upper()), None)
                col_apto = next((c for c in cols if 'APTO' in c.upper()), None)
                col_nombre = next((c for c in cols if 'NOMBRE' in c.upper()), None)
                col_torre = next((c for c in cols if 'TORRE' in c.upper()), None)
                col_estado = next((c for c in cols if 'ESTADO' in c.upper()), None)
                col_fecha_ci = next((c for c in cols if 'FECHA_COMPROMISO_CI' in c.upper()), None)

                if col_venta and col_recaudo:

                    # ===============================
                    # 2️⃣ CÁLCULOS GENERALES
                    # ===============================
                    total_ventas = df[col_venta].apply(limpiar_valor).sum()
                    total_ci = df[col_recaudo].apply(limpiar_valor).sum()

                    subs_efectivos = df.apply(
                        lambda r: limpiar_valor(r[col_val_sub]) 
                        if col_est_sub and "APROBADO" in str(r[col_est_sub]).upper() else 0, axis=1
                    ).sum()

                    cred_efectivos = df.apply(
                        lambda r: limpiar_valor(r[col_val_cred]) 
                        if col_desembolso and "SI" in str(r[col_desembolso]).upper() else 0, axis=1
                    ).sum()

                    recaudo_total = total_ci + subs_efectivos + cred_efectivos
                    cartera_pendiente = total_ventas - recaudo_total
                    porcentaje_recaudo = (recaudo_total / total_ventas) if total_ventas > 0 else 0

                    # ===============================
                    # 3️⃣ CUOTAS INICIALES (ALERTAS)
                    # ===============================
                    mañana = date.today() + timedelta(days=1)
                    vencen_manana = 0
                    cartera_vencida = 0

                    for _, fila in df.iterrows():

                        valor_venta = limpiar_valor(fila[col_venta])
                        abonado = limpiar_valor(fila[col_recaudo])
                        cuota_requerida = valor_venta * 0.10

                        fecha_ci = fila.get(col_fecha_ci)

                        if fecha_ci:
                            if isinstance(fecha_ci, str):
                                try:
                                    fecha_ci = datetime.strptime(fecha_ci, "%Y-%m-%d").date()
                                except:
                                    fecha_ci = None

                        if fecha_ci:
                            if fecha_ci < date.today() and abonado < cuota_requerida:
                                cartera_vencida += 1

                            if fecha_ci == mañana and abonado < cuota_requerida:
                                vencen_manana += 1

                    # ===============================
                    # 4️⃣ DISPONIBILIDAD
                    # ===============================
                    disponibles = []

                    if col_estado:
                        for _, fila in df.iterrows():
                            if str(fila[col_estado]).upper() == "DISPONIBLE":
                                disponibles.append(
                                    f"{fila.get(col_torre,'')} - {fila.get(col_apto,'')}"
                                )

                    # ===============================
                    # 5️⃣ KPI EJECUTIVOS
                    # ===============================
                    st.markdown("### 📌 Indicadores Clave")
                    col_k1, col_k2, col_k3 = st.columns(3)
                    col_k4, col_k5 = st.columns(2)

                    with col_k1:
                        st.caption("Venta Total")
                        st.markdown(f"**{formato_moneda(total_ventas)}**")

                    with col_k2:
                        st.caption("Recaudo Total")
                        st.markdown(f"**{formato_moneda(recaudo_total)}**")

                    with col_k3:
                        st.caption("Cartera Pendiente")
                        st.markdown(f"**{formato_moneda(cartera_pendiente)}**")

                    with col_k4:
                        st.caption("C.I. Vencidas")
                        st.markdown(f"**{cartera_vencida}**")

                    with col_k5:
                        st.caption("Vencen Mañana")
                        st.markdown(f"**{vencen_manana}**")
                    #===============================
                    # 6️⃣ SEMÁFORO GLOBAL
                    # ===============================
                    st.divider()
                    c_sem, c_txt = st.columns([1, 4])

                    with c_sem:
                        if porcentaje_recaudo > 0.8:
                            st.markdown("## 🟢")
                        elif porcentaje_recaudo > 0.5:
                            st.markdown("## 🟡")
                        else:
                            st.markdown("## 🔴")
                    with c_txt:
                        st.subheader(f"Estado del Recaudo: {porcentaje_recaudo*100:.1f}%")
                        st.write(f"Cartera total por recuperar: **{formato_moneda(cartera_pendiente)}**")

                    # ===============================
                    # 4️⃣ DISPONIBILIDAD
                    # ===============================
                    st.markdown("### 🏢 Disponibilidad Actual")

                    disponibles = []

                    for _, fila in df.iterrows():

                        nombre_val = str(fila.get(col_nombre, "")).strip()

                        # Si no tiene cliente asignado → disponible
                        if nombre_val == "" or nombre_val.lower() == "nan":
                            
                            torre = str(fila.get(col_torre, "")).strip()
                            apto = str(fila.get(col_apto, "")).strip()

                            if torre or apto:
                                disponibles.append(f"Torre {torre} - Apto {apto}")

                    # Mostrar total
                    st.markdown(f"**{len(disponibles)} apartamentos disponibles**")

                    # Mostrar lista
                    if disponibles:
                        with st.expander("Ver listado"):
                            for apt in disponibles:
                                st.write("•", apt)
                    else:
                        st.success("No hay apartamentos disponibles")


                    # ===============================
                    # 8️⃣ ALERTAS GESTIÓN (LO TUYO ORIGINAL)
                    # ===============================
                    st.divider()
                    st.subheader("🚧 Alertas de Gestión por Apartamento")

                    tab_sub, tab_cred = st.tabs(["📌 Subsidios Pendientes", "📌 Créditos sin Desembolso"])

                    with tab_sub:
                        mask_sub = (
                            (df[col_est_sub].astype(str).str.upper() != "APROBADO") &
                            (df[col_val_sub].apply(limpiar_valor) > 0)
                        )
                        df_sub_pend = df[mask_sub][[col_apto, col_nombre, col_est_sub, col_val_sub]].copy()

                        if not df_sub_pend.empty:
                            st.error(f"{len(df_sub_pend)} subsidios pendientes:")
                            st.dataframe(df_sub_pend, use_container_width=True, hide_index=True)
                        else:
                            st.success("No hay subsidios pendientes.")

                    with tab_cred:
                        mask_cred = (
                            (df[col_desembolso].astype(str).str.upper() != "SI") &
                            (df[col_val_cred].apply(limpiar_valor) > 0)
                        )
                        df_cred_pend = df[mask_cred][[col_apto, col_nombre, col_val_cred, col_desembolso]].copy()

                        if not df_cred_pend.empty:
                            st.warning(f"{len(df_cred_pend)} créditos pendientes:")
                            st.dataframe(df_cred_pend, use_container_width=True, hide_index=True)
                        else:
                            st.success("Todos los créditos desembolsados.")

                    # ===============================
                    # 9️⃣ EXPORTACIÓN (TU HTML ORIGINAL CONSERVADO)
                    # ===============================
                    st.divider()
                    st.subheader("🖨️ Exportar Informe Profesional")

                    html_report = f"""
                    <html>
                    <head><meta charset="UTF-8"></head>
                    <body>
                    <h1>Reporte Gerencial - Proyecto</h1>
                    <p>Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
                    <h3>Venta Total: {formato_moneda(total_ventas)}</h3>
                    <h3>Recaudo Total: {formato_moneda(recaudo_total)}</h3>
                    <h3>Cartera Pendiente: {formato_moneda(cartera_pendiente)}</h3>
                    <h3>Cuotas Iniciales Vencidas: {cartera_vencida}</h3>
                    <h3>Vencen Mañana: {vencen_manana}</h3>
                    </body>
                    </html>
                    """

                    st.download_button(
                        label="📩 Descargar Informe Ejecutivo",
                        data=html_report,
                        file_name="Reporte_Gerencial.html",
                        mime="text/html",
                        use_container_width=True
                    )