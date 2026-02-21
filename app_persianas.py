import streamlit as st
from fpdf import FPDF
import requests
import json
from datetime import datetime

# --- CONFIGURACIÓN DE TU INFRAESTRUCTURA ---
# URL de tu Google Apps Script (Implementación "Histórico cotizaciones")
URL_APPSCRIPT = "https://script.google.com/macros/s/AKfycbycgEmOPs4jcFbAL2teXmaDUamNnP-ZhAExYwvKjM9aTe-DiNzAiLlrgZ5SUwkAxM01LQ/exec"

# --- LÓGICA DE CONSECUTIVO DESDE LA NUBE ---
def obtener_consecutivo():
    try:
        # Consultamos el último folio registrado en la hoja de cálculo
        response = requests.get(URL_APPSCRIPT, timeout=10)
        if response.status_code == 200:
            # El script devuelve el último número; sumamos 1 para el nuevo
            return int(response.text) + 1
        return 100
    except Exception:
        # Si hay error de conexión, iniciamos en 100 por defecto
        return 100

def registrar_en_nube(datos):
    try:
        # Enviamos los datos en formato JSON a la hoja de cálculo
        response = requests.post(URL_APPSCRIPT, data=json.dumps(datos), timeout=10)
        return response.status_code == 200
    except Exception:
        return False

# --- FUNCIÓN PDF ---
def crear_pdf(datos_cliente, lista_items):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(200, 15, txt='Persianas Steven', ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(100, 10, txt=f"Cotización No: {datos_cliente['consecutivo']}")
    pdf.cell(100, 10, txt=f"Fecha: {datos_cliente['fecha']}", ln=True, align='R')
    pdf.cell(200, 10, txt=f"Cliente: {datos_cliente['cliente']}", ln=True)
    pdf.ln(5)

    # Encabezados de Tabla
    pdf.set_fill_color(230, 230, 230)
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(12, 10, "Cant.", border=1, fill=True, align='C')
    pdf.cell(65, 10, "Descripción", border=1, fill=True, align='C')
    pdf.cell(35, 10, "Medidas", border=1, fill=True, align='C')
    pdf.cell(38, 10, "Precio Unit.", border=1, fill=True, align='C')
    pdf.cell(40, 10, "Subtotal", border=1, fill=True, align='C', ln=True)

    pdf.set_font("Arial", size=9)
    subtotal_acumulado = 0
    resumen_items = []
    for item in lista_items:
        pdf.cell(12, 10, str(item['cantidad']), border=1, align='C')
        pdf.cell(65, 10, f"{item['tela']} ({item['motor']})", border=1)
        pdf.cell(35, 10, f"{item['ancho']}x{item['largo']} {item['unit']}", border=1, align='C')
        pdf.cell(38, 10, f"${item['precio_unitario']:,.0f}", border=1, align='R')
        pdf.cell(40, 10, f"${item['subtotal_item']:,.0f}", border=1, align='R', ln=True)
        subtotal_acumulado += item['subtotal_item']
        resumen_items.append(f"{item['cantidad']} {item['tela']}")

    pdf.ln(5)
    impuesto = subtotal_acumulado * 0.07
    total_gral = subtotal_acumulado + impuesto

    pdf.set_font("Arial", 'B', 10)
    pdf.cell(150, 8, "SUBTOTAL:", align='R')
    pdf.cell(40, 8, f"${subtotal_acumulado:,.0f}", border=1, ln=True, align='R')
    pdf.cell(150, 8, "IMPUESTO (7%):", align='R')
    pdf.cell(40, 8, f"${impuesto:,.0f}", border=1, ln=True, align='R')
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(150, 10, "TOTAL COTIZADO:", align='R')
    pdf.cell(40, 10, f"${total_gral:,.0f}", border=1, ln=True, align='R')
    
    return pdf.output(dest='S').encode('latin-1'), subtotal_acumulado, impuesto, total_gral, " | ".join(resumen_items)

# --- CONFIGURACIÓN DE APP STREAMLIT ---
st.set_page_config(page_title='Cotizaciones Persianas', layout="centered")
st.title('🪟 Persianas Steven')

if 'n_folio' not in st.session_state:
    st.session_state.n_folio = obtener_consecutivo()
if 'carrito' not in st.session_state:
    st.session_state.carrito = []

# Encabezado de Cliente y Folio
col_head1, col_head2 = st.columns([2, 1])
with col_head1:
    cliente = st.text_input("Nombre del Cliente", placeholder="Ej: Pablo Pérez")
with col_head2:
    st.write(f"Folio Actual")
    st.subheader(f"#{st.session_state.n_folio}")

st.divider()

# Parámetros de la persiana
usar_pulgadas = st.toggle("📐 Usar Pulgadas (in)", value=False)
unidad = "in" if usar_pulgadas else "m"

col1, col2 = st.columns(2)
with col1:
    ancho = st.number_input(f"Ancho ({unidad})", min_value=0.1, value=1.5 if not usar_pulgadas else 60.0)
    tipo_tela = st.selectbox("Tipo de Tela", ["Blackout", "Screen", "Sheer Elegance"])
with col2:
    largo = st.number_input(f"Largo ({unidad})", min_value=0.1, value=1.5 if not usar_pulgadas else 60.0)
    motor = st.radio("Accionamiento", ["Manual", "Motorizada"], horizontal=True)

cantidad = st.number_input("Cantidad de persianas", min_value=1, value=1)

# Lógica de Cálculos (se mantiene tu fórmula original)
factor = 0.0254 if usar_pulgadas else 1.0
a_m = ancho * factor
l_m = largo * factor
area_f = (a_m * l_m) * 1.15
precios_m2 = {"Blackout": 48000, "Screen": 58000, "Sheer Elegance": 88000}
p_unit = (area_f * precios_m2[tipo_tela]) + (165000 if motor == "Motorizada" else 0)
sub_item = p_unit * cantidad

st.info(f"Área facturable: {area_f:.2f} m² (incluye 15% desperdicio)")
st.success(f"## Subtotal Ítem: ${sub_item:,.0f}")

if st.button("➕ Agregar al carrito", use_container_width=True):
    st.session_state.carrito.append({
        "cantidad": cantidad, "tela": tipo_tela, "motor": motor,
        "ancho": ancho, "largo": largo, "unit": unidad, 
        "precio_unitario": p_unit, "subtotal_item": sub_item
    })
    st.toast("Añadido al carrito")

# --- RESUMEN Y ACCIÓN DE GUARDADO ---
if st.session_state.carrito:
    st.divider()
    st.subheader("🛒 Carrito de Cotización")
    
    for idx, it in enumerate(st.session_state.carrito):
        st.write(f"**{it['cantidad']}x** {it['tela']} ({it['ancho']}x{it['largo']} {it['unit']}) - ${it['subtotal_item']:,.0f}")

    if st.button("💾 Guardar en Historial y Generar PDF", use_container_width=True):
        datos_pdf = {
            "consecutivo": st.session_state.n_folio, 
            "fecha": datetime.now().strftime("%d/%m/%Y"), 
            "cliente": cliente if cliente else "Prospecto General"
        }
        
        pdf_bytes, sub, imp, tot, res = crear_pdf(datos_pdf, st.session_state.carrito)
        
        # Preparar datos para Google Sheets
        datos_registro = {
            "folio": st.session_state.n_folio,
            "fecha": datos_pdf["fecha"],
            "cliente": datos_pdf["cliente"],
            "items": res,
            "total": tot
        }

        # Registrar en la nube
        with st.spinner("Registrando cotización en la nube..."):
            if registrar_en_nube(datos_registro):
                st.success(f"✅ Cotización #{st.session_state.n_folio} guardada en Google Sheets")
                # Solo si se guardó con éxito, actualizamos el folio para la siguiente
                st.session_state.n_folio += 1
            else:
                st.error("❌ Error al guardar en la nube. Revisa tu conexión.")

        # Botón de descarga del PDF generado
        st.download_button(
            label="📩 Descargar PDF para enviar",
            data=pdf_bytes,
            file_name=f"Cotizacion_{datos_pdf['consecutivo']}.pdf",
            mime="application/pdf"
        )
