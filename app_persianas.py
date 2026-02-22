# -*- coding: utf-8 -*-
import streamlit as st
from fpdf import FPDF
import requests
import json
from datetime import datetime
import pandas as pd

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Persianas Steven", page_icon="🪟", layout="centered")

# URL DE TU IMPLEMENTACIÓN ACTUAL
URL_APPSCRIPT = "https://script.google.com/macros/s/AKfycbxhHjthaZnGzWbsnyckIVSYPI31hq4os8tQXfNGngSbHZy8IhZ_lKfCZRc1tuSkrGcBg/exec"

# --- FUNCIONES NUBE (CORREGIDA PARA EVITAR ERROR DE COMUNICACIÓN) ---
def registrar_en_nube(datos):
    try:
        # Enviamos con headers explícitos y un tiempo de espera más largo
        response = requests.post(
            URL_APPSCRIPT, 
            data=json.dumps(datos), 
            headers={'Content-Type': 'application/json'},
            timeout=20 
        )
        # Verificamos si la respuesta fue exitosa (200) o si contiene el texto que envía el script
        return response.status_code == 200 or "Éxito" in response.text
    except: 
        return False

# --- FUNCIÓN PDF PROFESIONAL (CON U.M) ---
def generar_pdf_pro(n_folio, nombre_cliente, carrito):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(200, 15, txt='Persianas Steven', ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(100, 10, txt=f"Cotizacion No: {n_folio}")
    pdf.cell(100, 10, txt=f"Fecha: {datetime.now().strftime('%d/%m/%Y')}", ln=True, align='R')
    pdf.set_font("Arial", '', 12)
    pdf.cell(200, 10, txt=f"Cliente: {nombre_cliente}", ln=True)
    pdf.ln(5)
    
    pdf.set_fill_color(230, 230, 230)
    pdf.set_font("Arial", 'B', 9)
    # Columnas: Descripción, U.M, Precio Unit, Cant, Subtotal
    pdf.cell(80, 10, u"Descripcion", border=1, fill=True, align='C')
    pdf.cell(15, 10, "U.M", border=1, fill=True, align='C')
    pdf.cell(35, 10, "Precio Unit.", border=1, fill=True, align='C')
    pdf.cell(15, 10, "Cant.", border=1, fill=True, align='C')
    pdf.cell(45, 10, "Subtotal", border=1, fill=True, align='C', ln=True)
    
    pdf.set_font("Arial", size=9)
    subtotal_acumulado = 0
    for item in carrito:
        pdf.cell(80, 10, item['descripcion'], border=1)
        pdf.cell(15, 10, item['unidad'], border=1, align='C')
        pdf.cell(35, 10, f"${item['valor_item']:,.0f}", border=1, align='R')
        pdf.cell(15, 10, str(item['cantidad']), border=1, align='C')
        pdf.cell(45, 10, f"${item['subtotal_item']:,.0f}", border=1, align='R', ln=True)
        subtotal_acumulado += item['subtotal_item']
    
    pdf.ln(5)
    impuesto = subtotal_acumulado * 0.07
    total_gral = subtotal_acumulado + impuesto
    pdf.set_font("Arial", 'B', 12)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(145, 10, "TOTAL COTIZADO (con 7% Imp.):", align='R')
    pdf.cell(45, 10, f"${total_gral:,.0f}", border=1, ln=True, align='R', fill=True)
    return pdf.output(dest='S').encode('latin-1'), total_gral

# --- ESTADO DE SESIÓN ---
if 'n_folio' not in st.session_state:
    st.session_state.n_folio = 1 # Empieza siempre en 1
if 'carrito' not in st.session_state:
    st.session_state.carrito = []
if 'item_id' not in st.session_state:
    st.session_state.item_id = 0
if 'cliente_limpio' not in st.session_state:
    st.session_state.cliente_limpio = 0

# --- TÍTULO ---
st.markdown('<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">', unsafe_allow_html=True)
st.markdown("<h1 style='display: flex; align-items: center;'><i class='material-icons' style='font-size: 45px; margin-right: 15px; color: #4F8BF9;'>window</i>Persianas Steven</h1>", unsafe_allow_html=True)

# --- CLIENTE ---
input_cliente = st.text_input("Nombre del Cliente", placeholder="EJ: JUAN PEREZ", key=f"cli_{st.session_state.cliente_limpio}")
cliente = input_cliente.upper()
st.write(f"Folio Actual: **#{st.session_state.n_folio}**")
st.divider()

# --- DATOS DEL ÍTEM ---
usar_pulgadas = st.toggle("📐 Usar Pulgadas (in)", value=False, key=f"pulg_{st.session_state.item_id}")
unidad = "in" if usar_pulgadas else "m"
unidad_area = "in²" if usar_pulgadas else "m²"

col1, col2 = st.columns(2)
with col1:
    ancho = st.number_input(f"Ancho ({unidad})", min_value=0.0, step=0.01, format="%.2f", key=f"anc_{st.session_state.item_id}")
    tipo_tela = st.selectbox("Tipo de Tela", ["Seleccione...", "Blackout", "Screen", "Sheer Elegance"], key=f"tel_{st.session_state.item_id}")
with col2:
    largo = st.number_input(f"Largo ({unidad})", min_value=0.0, step=0.01, format="%.2f", key=f"lar_{st.session_state.item_id}")
    motor = st.radio("Accionamiento", ["Manual", "Motorizada"], key=f"mot_{st.session_state.item_id}")

cantidad = st.number_input("Cantidad", min_value=1, step=1, key=f"can_{st.session_state.item_id}")

if ancho > 0 and largo > 0 and tipo_tela != "Seleccione...":
    area_visual = (ancho * largo) * 1.15
    factor_m = 0.0254 if usar_pulgadas else 1.0
    area_m2 = (ancho * factor_m * largo * factor_m) * 1.15
    precios = {"Blackout": 48000, "Screen": 58000, "Sheer Elegance": 88000}
    p_unit = (area_m2 * precios[tipo_tela]) + (165000 if motor == "Motorizada" else 0)
    sub_total_item = p_unit * cantidad
    
    st.info(f"Área facturable (con 15% desp.): {area_visual:.2f} {unidad_area}")
    st.success(f"## Subtotal Ítem: ${sub_total_item:,.0f}")
    
    if st.button("➕ Agregar al carrito"):
        st.session_state.carrito.append({
            "descripcion": f"{tipo_tela} ({ancho}x{largo})",
            "unidad": unidad,
            "cantidad": cantidad,
            "valor_item": p_unit,
            "subtotal_item": sub_total_item
        })
        st.toast("Ítem añadido")
        st.session_state.item_id += 1
        st.rerun()

# --- TABLA DE RESUMEN Y REGISTRO ---
if st.session_state.carrito:
    st.divider()
    st.subheader("🛒 Resumen")
    df_resumen = pd.DataFrame(st.session_state.carrito)
    total_cotizacion = df_resumen['subtotal_item'].sum() * 1.07
    
    df_mostrar = pd.DataFrame()
    df_mostrar['Folio'] = [st.session_state.n_folio] * len(df_resumen)
    df_mostrar['Fecha'] = datetime.now().strftime("%d/%m/%Y")
    df_mostrar['Cliente'] = cliente
    df_mostrar['Descripción'] = df_resumen['descripcion']
    df_mostrar['U.M'] = df_resumen['unidad']
    df_mostrar['Cantidad'] = df_resumen['cantidad']
    df_mostrar['Valor ítem'] = df_resumen['valor_item'].map('${:,.0f}'.format)
    df_mostrar['Total cotización'] = f"${total_cotizacion:,.0f}"
    st.table(df_mostrar)
    
    pdf_output, total_final = generar_pdf_pro(st.session_state.n_folio, cliente, st.session_state.carrito)
    st.download_button(label="📩 Descargar PDF", data=pdf_output, file_name=f"Cotizacion_{st.session_state.n_folio}.pdf", mime="application/pdf", use_container_width=True)

    if st.button("💾 REGISTRAR Y LIMPIAR TODO", use_container_width=True, type="primary"):
        datos_envio = {
            "folio": st.session_state.n_folio,
            "fecha": datetime.now().strftime("%d/%m/%Y"),
            "cliente": cliente if cliente else "CONSUMIDOR FINAL",
            "total_general": total_final,
            "items_detalle": st.session_state.carrito
        }
        if registrar_en_nube(datos_envio):
            st.success("✅ ¡Registro exitoso en Drive!")
            st.session_state.carrito = []
            st.session_state.cliente_limpio += 1
            st.session_state.item_id += 1 
            st.session_state.n_folio += 1 
            st.rerun()
        else:
            st.error("❌ Error de comunicación con Drive. Revisa que el Script esté publicado para 'Cualquiera'.")
