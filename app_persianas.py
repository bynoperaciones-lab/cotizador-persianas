# -*- coding: utf-8 -*-
import streamlit as st
from fpdf import FPDF
import requests
import json
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Persianas Steven", page_icon="🪟", layout="centered")

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

# --- FUNCIÓN PDF (RESTAURADA A LA VERSIÓN PROFESIONAL) ---
def generar_pdf_pro(n_folio, nombre_cliente, carrito):
    pdf = FPDF()
    pdf.add_page()
    
    # Encabezado Principal
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(200, 15, txt='Persianas Steven', ln=True, align='C')
    pdf.ln(10)
    
    # Información de Cotización
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(100, 10, txt=f"Cotización No: {n_folio}")
    pdf.cell(100, 10, txt=f"Fecha: {datetime.now().strftime('%d/%m/%Y')}", ln=True, align='R')
    pdf.set_font("Arial", '', 12)
    pdf.cell(200, 10, txt=f"Cliente: {nombre_cliente}", ln=True)
    pdf.ln(5)

    # Tabla de Ítems con Formato
    pdf.set_fill_color(230, 230, 230)
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(12, 10, "Cant.", border=1, fill=True, align='C')
    pdf.cell(65, 10, u"Descripción", border=1, fill=True, align='C')
    pdf.cell(35, 10, "Medidas", border=1, fill=True, align='C')
    pdf.cell(38, 10, "Precio Unit.", border=1, fill=True, align='C')
    pdf.cell(40, 10, "Subtotal", border=1, fill=True, align='C', ln=True)

    pdf.set_font("Arial", size=9)
    subtotal_acumulado = 0
    
    for item in carrito:
        # Extraemos medidas del texto de descripción para la columna de medidas del PDF
        # El formato guardado es "Tela (Ancho x Largo Unidad) Motor"
        pdf.cell(12, 10, str(item['cantidad']), border=1, align='C')
        pdf.cell(65, 10, item['descripcion'], border=1)
        pdf.cell(35, 10, "Ver desc.", border=1, align='C') # Simplificado para evitar errores de parseo
        pdf.cell(38, 10, f"${(item['subtotal_item']/item['cantidad']):,.0f}", border=1, align='R')
        pdf.cell(40, 10, f"${item['subtotal_item']:,.0f}", border=1, align='R', ln=True)
        subtotal_acumulado += item['subtotal_item']

    pdf.ln(5)
    impuesto = subtotal_acumulado * 0.07
    total_gral = subtotal_acumulado + impuesto

    # Totales Finales con Estilo
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(150, 8, "SUBTOTAL:", align='R')
    pdf.cell(40, 8, f"${subtotal_acumulado:,.0f}", border=1, ln=True, align='R')
    pdf.cell(150, 8, "IMPUESTO (7%):", align='R')
    pdf.cell(40, 8, f"${impuesto:,.0f}", border=1, ln=True, align='R')
    pdf.set_font("Arial", 'B', 12)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(150, 10, "TOTAL COTIZADO:", align='R')
    pdf.cell(40, 10, f"${total_gral:,.0f}", border=1, ln=True, align='R', fill=True)
    
    return pdf.output(dest='S').encode('latin-1'), total_gral

# --- TÍTULO Y LOGO ---
st.markdown('<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">', unsafe_allow_html=True)
st.markdown("<h1 style='display: flex; align-items: center;'><i class='material-icons' style='font-size: 45px; margin-right: 15px; color: #4F8BF9;'>window</i>Persianas Steven</h1>", unsafe_allow_html=True)

# --- ESTADO DE SESIÓN ---
if 'n_folio' not in st.session_state:
    st.session_state.n_folio = obtener_consecutivo()
if 'carrito' not in st.session_state:
    st.session_state.carrito = []

# --- ENTRADA DE DATOS ---
cliente = st.text_input("Nombre del Cliente", placeholder="Ej: Pablo Pérez", key="cli")
st.write(f"Folio Actual: **#{st.session_state.n_folio}**")

st.divider()

usar_pulgadas = st.toggle("📐 Usar Pulgadas (in)", value=False, key="pulg")
unidad = "in" if usar_pulgadas else "m"

col1, col2 = st.columns(2)
with col1:
    ancho = st.number_input(f"Ancho ({unidad})", min_value=0.0, step=0.01, format="%.2f", key="anc")
    tipo_tela = st.selectbox("Tipo de Tela", ["Seleccione...", "Blackout", "Screen", "Sheer Elegance"], key="tel")
with col2:
    largo = st.number_input(f"Largo ({unidad})", min_value=0.0, step=0.01, format="%.2f", key="lar")
    motor = st.radio("Accionamiento", ["Manual", "Motorizada"], key="mot")

cantidad = st.number_input("Cantidad de persianas", min_value=1, step=1, key="can")

# Cálculos Exactos
if ancho > 0 and largo > 0 and tipo_tela != "Seleccione...":
    factor = 0.0254 if usar_pulgadas else 1.0
    area_f = (ancho * factor * largo * factor) * 1.15
    precios = {"Blackout": 48000, "Screen": 58000, "Sheer Elegance": 88000}
    p_unit = (area_f * precios[tipo_tela]) + (165000 if motor == "Motorizada" else 0)
    sub_total_item = p_unit * cantidad
    
    st.info(f"Área facturable (con 15% desp.): {area_f:.2f} m²")
    st.success(f"## Subtotal Ítem: ${sub_total_item:,.0f}")
    
    if st.button("➕ Agregar al carrito"):
        st.session_state.carrito.append({
            "cantidad": cantidad,
            "descripcion": f"{tipo_tela} ({ancho}x{largo}{unidad}) {motor}",
            "subtotal_item": sub_total_item
        })
        st.toast("Añadido")

# --- RESUMEN Y ACCIONES ---
if st.session_state.carrito:
    st.divider()
    st.subheader("🛒 Resumen")
    for it in st.session_state.carrito:
        st.write(f"**{it['cantidad']}x** {it['descripcion']} — ${it['subtotal_item']:,.0f}")
    
    # Generamos el PDF profesional
    pdf_output, total_final = generar_pdf_pro(st.session_state.n_folio, cliente, st.session_state.carrito)
    
    st.download_button(
        label="📩 Descargar Cotización PDF (Versión Profesional)",
        data=pdf_output,
        file_name=f"Cotizacion_{st.session_state.n_folio}.pdf",
        mime="application/pdf",
        use_container_width=True
    )

    if st.button("💾 REGISTRAR Y LIMPIAR TODO", use_container_width=True, type="primary"):
        datos_nube = {
            "folio": st.session_state.n_folio,
            "fecha": datetime.now().strftime("%d/%m/%Y"),
            "cliente": cliente if cliente else "Consumidor Final",
            "items_detalle": st.session_state.carrito,
            "total_general": total_final
        }
        
        if registrar_en_nube(datos_nube):
            st.success("✅ ¡Éxito! Hoja actualizada y App limpia.")
            st.session_state.carrito = []
            st.session_state.n_folio = obtener_consecutivo()
            st.rerun()
