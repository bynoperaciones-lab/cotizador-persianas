import streamlit as st
from fpdf import FPDF
import os
from datetime import datetime

# --- LÓGICA DEL CONSECUTIVO AUTOMÁTICO ---
if not os.path.exists("ultimo_consecutivo.txt"):
    with open("ultimo_consecutivo.txt", "w") as f:
        f.write("100")

def obtener_consecutivo():
    with open("ultimo_consecutivo.txt", "r") as f:
        return int(f.read())

def actualizar_consecutivo(nuevo_valor):
    with open("ultimo_consecutivo.txt", "w") as f:
        f.write(str(nuevo_valor))

# --- FUNCIÓN PARA GENERAR EL PDF (VERSION LIMPIA) ---
def crear_pdf(datos):
    pdf = FPDF()
    pdf.add_page()
    
    # Encabezado
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(200, 15, txt='Persianas "Empresa de Prueba"', ln=True, align='C')
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(200, 10, txt="Cotización de Productos", ln=True, align='C')
    pdf.ln(10)
    
    # Información básica
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(100, 10, txt=f"Cotización No: {datos['consecutivo']}")
    pdf.cell(100, 10, txt=f"Fecha: {datos['fecha']}", ln=True, align='R')
    pdf.cell(200, 10, txt=f"Cliente: {datos['cliente']}", ln=True)
    pdf.ln(10)
    
    # Detalles del producto (Sin mostrar desperdicio)
    pdf.set_fill_color(245, 245, 245)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="DESCRIPCIÓN DEL PEDIDO", ln=True, align='L', fill=True)
    
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Producto: Persiana en Tela {datos['tela']}", ln=True)
    pdf.cell(200, 10, txt=f"Dimensiones: {datos['ancho']}m (Ancho) x {datos['largo']}m (Largo)", ln=True)
    pdf.cell(200, 10, txt=f"Sistema de accionamiento: {datos['motor']}", ln=True)
    pdf.ln(15)
    
    # Precio Final
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 15, txt=f"VALOR TOTAL: ${datos['total']:,.0f}", ln=True, align='R')
    
    pdf.set_font("Arial", 'I', 9)
    pdf.ln(20)
    pdf.multi_cell(0, 5, txt="Esta cotización tiene una validez de 15 días. Los precios incluyen instalación básica.")
    
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFAZ DE USUARIO ---
st.set_page_config(page_title='Persianas "Empresa de Prueba"', page_icon="🪟")
st.title('🪟 Persianas "Empresa de Prueba"')

if 'n_folio' not in st.session_state:
    st.session_state.n_folio = obtener_consecutivo()

col_top1, col_top2 = st.columns([2, 1])
with col_top1:
    cliente = st.text_input("Nombre del Cliente", placeholder="Nombre completo")
with col_top2:
    st.metric("Cotización actual", f"#{st.session_state.n_folio}")

st.divider()

c1, c2 = st.columns(2)
with c1:
    ancho = st.number_input("Ancho de la persiana (m)", min_value=0.1, value=1.5, step=0.01)
    tipo_tela = st.selectbox("Seleccione la Tela", ["Blackout", "Screen", "Sheer Elegance"])
with c2:
    largo = st.number_input("Largo de la persiana (m)", min_value=0.1, value=1.5, step=0.01)
    motor = st.radio("¿Tipo de accionamiento?", ["Manual", "Motorizada"])

# --- CÁLCULOS INTERNOS (Aquí se gestiona el desperdicio) ---
precios_m2 = {"Blackout": 48000, "Screen": 58000, "Sheer Elegance": 88000}
costo_motor = 165000 if motor == "Motorizada" else 0

# Calculamos desperdicio (15%) pero NO lo mostramos en el PDF
area_real = ancho * largo
area_con_desperdicio = area_real * 1.15 

total_final = (area_con_desperdicio * precios_m2[tipo_tela]) + costo_motor

# Resumen solo para tu vista en la app
st.info(f"**Cálculo interno:** Área real {area_real:.2f} m² | Con desperdicio: {area_con_desperdicio:.2f} m²")
st.success(f"### Precio al público: ${total_final:,.0f}")

datos_para_pdf = {
    "consecutivo": st.session_state.n_folio,
    "fecha": datetime.now().strftime("%d/%m/%Y"),
    "cliente": cliente if cliente else "Cliente Particular",
    "ancho": ancho,
    "largo": largo,
    "tela": tipo_tela,
    "motor": motor,
    "total": total_final
}

if st.download_button(
    label="📩 Generar y Descargar Cotización",
    data=crear_pdf(datos_para_pdf),
    file_name=f"Cotizacion_{st.session_state.n_folio}.pdf",
    mime="application/pdf"
):
    actualizar_consecutivo(st.session_state.n_folio + 1)
    st.session_state.n_folio = obtener_consecutivo()
    st.rerun()