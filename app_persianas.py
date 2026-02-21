# -*- coding: utf-8 -*-
import streamlit as st
from fpdf import FPDF
import requests
import json
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Persianas Steven", page_icon="🪟", layout="centered")

# URL DE TU ÚLTIMA IMPLEMENTACIÓN
URL_APPSCRIPT = "https://script.google.com/macros/s/AKfycbzeA8z6WynVu_R6ZKLrB3Ss8r1xuoTNSsIqXGrjr4_8M4zKDikp-qHgywgDUcpSucz34w/exec"

# --- FUNCIONES NUBE ---
def obtener_consecutivo():
    try:
        response = requests.get(URL_APPSCRIPT, timeout=10)
        return int(response.text) + 1 if response.status_code == 200 else 100
    except: return 100

def registrar_en_nube(datos):
    try:
        response = requests.post(URL_APPSCRIPT, data=json.dumps(datos), timeout=10)
        return response.status_code == 200
    except: return False

# --- FUNCIÓN GENERAR PDF ---
def generar_pdf(n_folio, nombre_cliente, carrito, total):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "Persianas Steven - Cotización", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, f"Folio: #{n_folio} | Fecha: {datetime.now().strftime('%d/%m/%Y')}", ln=True)
    pdf.cell(200, 10, f"Cliente: {nombre_cliente}", ln=True)
    pdf.ln(10)
    
    # Encabezados
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(100, 10, u"Descripción", 1)
    pdf.cell(30, 10, "Cant.", 1, align='C')
    pdf.cell(60, 10, "Subtotal", 1, ln=True, align='C')
    
    pdf.set_font("Arial", size=10)
    for it in carrito:
        pdf.cell(100, 10, it['descripcion'], 1)
        pdf.cell(30, 10, str(it['cantidad']), 1, align='C')
        pdf.cell(60, 10, f"${it['subtotal_item']:,.0f}", 1, ln=True, align='R')
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(130, 10, "TOTAL (Inc. 7%):", 1, align='R')
    pdf.cell(60, 10, f"${total:,.0f}", 1, ln=True, align='R')
    
    return pdf.output(dest='S').encode('latin-1')

# --- TÍTULO ---
st.markdown('<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">', unsafe_allow_html=True)
st.markdown("<h1 style='display: flex; align-items: center;'><i class='material-icons' style='font-size: 45px; margin-right: 15px; color: #4F8BF9;'>window</i>Persianas Steven</h1>", unsafe_allow_html=True)

# --- ESTADO DE SESIÓN ---
if 'n_folio' not in st.session_state:
    st.session_state.n_folio = obtener_consecutivo()
if 'carrito' not in st.session_state:
    st.session_state.carrito = []

# --- ENTRADA DE DATOS ---
cliente = st.text_input("Nombre del Cliente", placeholder="Escriba aquí...", key="cli")
st.write(f"Folio Actual: **#{st.session_state.n_folio}**")

st.divider()

# REINSTALACIÓN DE OPCIÓN PULGADAS
usar_pulgadas = st.toggle("📐 Usar Pulgadas (in)", value=False, key="pulg")
unidad = "in" if usar_pulgadas else "m"

col1, col2 = st.columns(2)
with col1:
    ancho = st.number_input(f"Ancho ({unidad})", min_value=0.0, step=0.01, format="%.2f", key="anc")
    tipo_tela = st.selectbox("Tipo de Tela", ["Seleccione...", "Blackout", "Screen", "Sheer Elegance"], key="tel")
with col2:
    largo = st.number_input(f"Largo ({unidad})", min_value=0.0, step=0.01, format="%.2f", key="lar")
    motor = st.radio("Accionamiento", ["Manual", "Motorizada"], key="mot")

cantidad = st.number_input("Cantidad", min_value=1, step=1, key="can")

# LÓGICA DE CÁLCULOS CON CONVERSIÓN Y DESPERDICIO
if ancho > 0 and largo > 0 and tipo_tela != "Seleccione...":
    # Convertir a metros si es necesario (1 pulgada = 0.0254 metros)
    factor = 0.0254 if usar_pulgadas else 1.0
    ancho_m = ancho * factor
    largo_m = largo * factor
    
    # Área con 15% de desperdicio
    area_f = (ancho_m * largo_m) * 1.15
    
    precios = {"Blackout": 48000, "Screen": 58000, "Sheer Elegance": 88000}
    p_unit = (area_f * precios[tipo_tela]) + (165000 if motor == "Motorizada" else 0)
    sub_total_item = p_unit * cantidad
    
    st.info(f"Área facturable (con 15% desp.): {area_f:.2f} m²")
    st.success(f"Subtotal Ítem: ${sub_total_item:,.0f}")
    
    if st.button("➕ Agregar Ítem al Carrito"):
        st.session_state.carrito.append({
            "cantidad": cantidad,
            "descripcion": f"{tipo_tela} ({ancho}x{largo}{unidad}) {motor}",
            "subtotal_item": sub_total_item
        })
        st.toast("Ítem añadido")

# --- RESUMEN, PDF Y ENVÍO ---
if st.session_state.carrito:
    st.divider()
    st.subheader("🛒 Resumen de la Cotización")
    for it in st.session_state.carrito:
        st.write(f"**{it['cantidad']}** | {it['descripcion']} | **${it['subtotal_item']:,.0f}**")
    
    total_neto = sum(i['subtotal_item'] for i in st.session_state.carrito)
    total_con_iva = total_neto * 1.07 

    # PDF
    pdf_bytes = generar_pdf(st.session_state.n_folio, cliente, st.session_state.carrito, total_con_iva)
    st.download_button(
        label="📄 Descargar PDF de Cotización",
        data=pdf_bytes,
        file_name=f"Cotizacion_{st.session_state.n_folio}.pdf",
        mime="application/pdf",
        use_container_width=True
    )

    # REGISTRO Y LIMPIEZA
    if st.button("💾 REGISTRAR EN EXCEL Y LIMPIAR APP", use_container_width=True, type="primary"):
        datos_nube = {
            "folio": st.session_state.n_folio,
            "fecha": datetime.now().strftime("%d/%m/%Y"),
            "cliente": cliente if cliente else "Consumidor Final",
            "items_detalle": st.session_state.carrito,
            "total_general": total_con_iva
        }
        
        if registrar_en_nube(datos_nube):
            st.success("✅ Guardado y App reseteada.")
            st.session_state.carrito = []
            st.session_state.n_folio = obtener_consecutivo()
            st.rerun()
        else:
            st.error("❌ Error de comunicación con la nube.")
