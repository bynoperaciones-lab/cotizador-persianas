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
        response = requests.get(URL_APPSCRIPT, timeout=5)
        if response.status_code == 200:
            content = response.text.strip()
            # Si el Excel está vacío o devuelve un valor no numérico, empezamos en 1
            if not content or content in ["null", "undefined", ""]:
                return 1
            val = int(content)
            # OBLIGAMOS AL CÓDIGO: Si el valor es mayor a 0, sigue la secuencia.
            # Si quieres forzar el 1 incluso si hay datos, cambia val por 0 aquí.
            return val + 1
        return 1
    except: 
        return 1

def registrar_en_nube(datos):
    try:
        response = requests.post(URL_APPSCRIPT, data=json.dumps(datos), timeout=10)
        return response.status_code == 200
    except: return False

# --- FUNCIÓN PDF ---
def generar_pdf_pro(n_folio, nombre_cliente, carrito):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(200, 15, txt='Persianas Steven', ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    # Mostramos el folio forzado
    pdf.cell(100, 10, txt=f"Cotizacion No: {n_folio}")
    pdf.cell(100, 10, txt=f"Fecha: {datetime.now().strftime('%d/%m/%Y')}", ln=True, align='R')
    pdf.set_font("Arial", '', 12)
    pdf.cell(200, 10, txt=f"Cliente: {nombre_cliente}", ln=True)
    pdf.ln(5)
    
    pdf.set_fill_color(230, 230, 230)
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(12, 10, "Cant.", border=1, fill=True, align='C')
    pdf.cell(85, 10, u"Descripcion", border=1, fill=True, align='C')
    pdf.cell(43, 10, "Precio Unit.", border=1, fill=True, align='C')
    pdf.cell(50, 10, "Subtotal", border=1, fill=True, align='C', ln=True)
    
    pdf.set_font("Arial", size=9)
    subtotal_acumulado = 0
    for item in carrito:
        pdf.cell(12, 10, str(item['cantidad']), border=1, align='C')
        pdf.cell(85, 10, item['descripcion'], border=1)
        pdf.cell(43, 10, f"${(item['subtotal_item']/item['cantidad']):,.0f}", border=1, align='R')
        pdf.cell(50, 10, f"${item['subtotal_item']:,.0f}", border=1, align='R', ln=True)
        subtotal_acumulado += item['subtotal_item']
    
    pdf.ln(5)
    total_gral = subtotal_acumulado * 1.07
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(140, 10, "TOTAL COTIZADO (con 7% Imp.):", align='R')
    pdf.cell(50, 10, f"${total_gral:,.0f}", border=1, ln=True, align='R', fill=True)
    return pdf.output(dest='S').encode('latin-1'), total_gral

# --- ESTADO DE SESIÓN ---
# Si quieres resetear a 1 hoy mismo, puedes cambiar esto temporalmente a 1
if 'n_folio' not in st.session_state:
    st.session_state.n_folio = obtener_consecutivo()
if 'carrito' not in st.session_state:
    st.session_state.carrito = []
if 'item_id' not in st.session_state:
    st.session_state.item_id = 0
if 'cliente_limpio' not in st.session_state:
    st.session_state.cliente_limpio = 0

# --- TÍTULO ---
st.markdown("<h1 style='text-align: center; color: #4F8BF9;'>🪟 Persianas Steven</h1>", unsafe_allow_html=True)

# --- CLIENTE EN MAYÚSCULAS ---
nombre_input = st.text_input("Nombre del Cliente", placeholder="Ej: PABLO PEREZ", key=f"cli_{st.session_state.cliente_limpio}")
cliente = nombre_input.upper()

st.write(f"Folio Actual: **#{st.session_state.n_folio}**")
st.divider()

# --- DATOS DEL ÍTEM ---
usar_pulgadas = st.toggle("📐 Usar Pulgadas (in)", value=False, key=f"pulg_{st.session_state.item_id}")
unidad = "in" if usar_pulgadas else "m"

col1, col2 = st.columns(2)
with col1:
    ancho = st.number_input(f"Ancho ({unidad})", min_value=0.0, step=0.01, key=f"anc_{st.session_state.item_id}")
    tipo_tela = st.selectbox("Tipo de Tela", ["Seleccione...", "Blackout", "Screen", "Sheer Elegance"], key=f"tel_{st.session_state.item_id}")
with col2:
    largo = st.number_input(f"Largo ({unidad})", min_value=0.0, step=0.01, key=f"lar_{st.session_state.item_id}")
    motor = st.radio("Accionamiento", ["Manual", "Motorizada"], key=f"mot_{st.session_state.item_id}")

cantidad = st.number_input("Cantidad", min_value=1, step=1, key=f"can_{st.session_state.item_id}")

# [cite_start]Cálculos (Sin cambios en la lógica de desperdicio [cite: 4, 6])
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
        st.session_state.item_id += 1
        st.rerun()

# --- REGISTRO Y LIMPIEZA ---
if st.session_state.carrito:
    st.divider()
    st.subheader("🛒 Resumen de Cotización")
    for it in st.session_state.carrito:
        st.write(f"**{it['cantidad']}x** {it['descripcion']} — ${it['subtotal_item']:,.0f}")
    
    pdf_output, total_final = generar_pdf_pro(st.session_state.n_folio, cliente, st.session_state.carrito)
    
    st.download_button(label="📩 Descargar PDF", data=pdf_output, file_name=f"Cotizacion_{st.session_state.n_folio}.pdf", mime="application/pdf", use_container_width=True)

    if st.button("💾 REGISTRAR Y LIMPIAR TODO", use_container_width=True, type="primary"):
        datos = {"folio": st.session_state.n_folio, "cliente": cliente, "total": total_final, "items": st.session_state.carrito}
        if registrar_en_nube(datos):
            st.success("✅ Registrado con éxito.")
            # RESET TOTAL
            st.session_state.carrito = []
            st.session_state.cliente_limpio += 1
            st.session_state.item_id += 1
            st.session_state.n_folio = obtener_consecutivo()
            st.rerun()
