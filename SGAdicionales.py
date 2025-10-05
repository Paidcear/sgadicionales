import streamlit as st
import json
import os
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests  # 🔹 Para WhatsApp

# Archivos JSON
PRODUCTOS_FILE = "productos.json"
VENTAS_FILE = "ventas.json"

# Inicializar archivos si no existen
if not os.path.exists(PRODUCTOS_FILE):
    with open(PRODUCTOS_FILE, "w") as f:
        json.dump([], f)

if not os.path.exists(VENTAS_FILE):
    with open(VENTAS_FILE, "w") as f:
        json.dump([], f)

# -----------------------
# Función de envío de correo usando st.secrets
# -----------------------
def enviar_correo_venta(venta):
    remitente = st.secrets["EMAIL"]["USER"]
    password = st.secrets["EMAIL"]["PASSWORD"]
    destino = st.secrets["EMAIL"]["DESTINO"]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Nueva venta por ${venta['total_venta']:.2f} - Venta #{venta['venta_num']}"
    msg["From"] = remitente
    msg["To"] = destino

    if venta["productos"]:
        df = pd.DataFrame(venta["productos"])
        df["subtotal"] = df["precio"] * df["cantidad"]
        tabla_html = df.to_html(index=False, justify="center")
    else:
        tabla_html = "<p>No hay productos en esta venta</p>"

    totales_html = f"""
    <p><b>Total productos:</b> ${venta['total_productos']:.2f}</p>
    <p><b>Total bebidas:</b> ${venta['bebidas']:.2f}</p>
    <p><b>Total general:</b> ${venta['total_venta']:.2f}</p>
    """

    cuerpo = f"""
    <h2>Detalle de la Venta #{venta['venta_num']}</h2>
    {tabla_html}
    <br>
    {totales_html}
    <p><i>Registro generado automáticamente por el sistema de ventas. CDelgado</i></p>
    """

    msg.attach(MIMEText(cuerpo, "html"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(remitente, password)
        server.sendmail(remitente, destino, msg.as_string())
        server.quit()
        st.success(f"Correo enviado al dueño con el detalle de la venta #{venta['venta_num']}")
    except Exception as e:
        st.error(f"Error al enviar correo: {e}")

# -----------------------
# Función de envío de WhatsApp usando API Cloud
# -----------------------
def enviar_whatsapp_venta(venta):
    """Envía resumen de venta por WhatsApp en texto formateado"""
    token = st.secrets["WHATSAPP"]["TOKEN"]
    phone_number_id = st.secrets["WHATSAPP"]["PHONE_NUMBER_ID"]
    recipient_number = st.secrets["WHATSAPP"]["RECIPIENT_NUMBER"]

    # Formatear productos
    lista_productos = ""
    for p in venta["productos"]:
        lista_productos += f"🍔 {p['nombre']} ({p['cantidad']}) - ${p['precio']:.2f}\n"

    # Formatear bebidas
    if venta["bebidas"] > 0:
        lista_bebidas = f"🥤 Bebidas - ${venta['bebidas']:.2f}\n"
    else:
        lista_bebidas = ""

    mensaje = f"""
🟢 *Nueva venta por ${venta['total_venta']:.2f} - Venta #{venta['venta_num']}*

🧾 *Detalles de la venta:*
---------------------------------
{lista_productos}{lista_bebidas}---------------------------------
💰 *Total productos:* ${venta['total_productos']:.2f}
💸 *Total bebidas:* ${venta['bebidas']:.2f}
🧮 *Total general:* ${venta['total_venta']:.2f}
"""

    url = f"https://graph.facebook.com/v21.0/{phone_number_id}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient_number,
        "type": "text",
        "text": {"body": mensaje}
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        requests.post(url, headers=headers, json=payload)
        st.info("✅ Mensaje de WhatsApp enviado correctamente.")
    except Exception as e:
        st.error(f"Error al enviar mensaje de WhatsApp: {e}")

# -----------------------
# Funciones de persistencia
# -----------------------
def cargar_productos():
    with open(PRODUCTOS_FILE, "r") as f:
        return json.load(f)

def guardar_productos(productos):
    with open(PRODUCTOS_FILE, "w") as f:
        json.dump(productos, f, indent=4)

def cargar_ventas():
    with open(VENTAS_FILE, "r") as f:
        return json.load(f)

def guardar_ventas(ventas):
    with open(VENTAS_FILE, "w") as f:
        json.dump(ventas, f, indent=4)

# -----------------------
# Sidebar con selectbox
# -----------------------
st.sidebar.title("Menú")
opcion = st.sidebar.selectbox("Selecciona una opción:", ["Ventas", "Productos"], label_visibility="collapsed")

# -----------------------
# Módulo de Productos
# -----------------------
if opcion == "Productos":
    productos = cargar_productos()
    menu = st.sidebar.radio("Acción:", ["Registrar Producto", "Editar Producto", "Consultar Productos"], label_visibility="collapsed")
    
    if menu == "Registrar Producto":
        st.sidebar.write("---")
        nombre = st.sidebar.text_input("Nombre del producto")
        precio = st.sidebar.number_input("Precio", min_value=0.0, step=0.01)
        if st.sidebar.button("Agregar Producto"):
            if nombre:
                productos.append({"nombre": nombre, "precio": precio})
                guardar_productos(productos)
                st.success(f"Producto '{nombre}' agregado con éxito")
            else:
                st.error("Debe ingresar un nombre de producto")
    
    elif menu == "Editar Producto":
        st.sidebar.write("---")
        if productos:
            nombres = [p["nombre"] for p in productos]
            seleccionado = st.sidebar.selectbox("Selecciona un producto", nombres)
            producto = next(p for p in productos if p["nombre"] == seleccionado)
            
            nuevo_nombre = st.sidebar.text_input("Nombre", value=producto["nombre"])
            nuevo_precio = st.sidebar.number_input("Precio", value=producto["precio"], min_value=0.0, step=0.01)
            
            if st.sidebar.button("Guardar Cambios"):
                producto["nombre"] = nuevo_nombre
                producto["precio"] = nuevo_precio
                guardar_productos(productos)
                st.success("Producto actualizado correctamente")
        else:
            st.info("No hay productos registrados")
    
    elif menu == "Consultar Productos":
        st.sidebar.write("---")
        if productos:
            df = pd.DataFrame(productos)
            df.index = df.index + 1
            st.sidebar.dataframe(df)
        else:
            st.info("No hay productos registrados")


# -----------------------
# Módulo de Ventas
# -----------------------
elif opcion == "Ventas":
    productos = cargar_productos()
    ventas = cargar_ventas()

    menu = st.radio("Acción:", ["Registrar Venta", "Consultar Ventas"], label_visibility="collapsed", horizontal=True)

    if menu == "Registrar Venta":
        if productos:
            venta_num = len(ventas) + 1
            st.subheader(f"Registrar Venta #{venta_num}")

            with st.form("form_venta", clear_on_submit=True):
                # Campo de bebidas
                bebidas = st.text_input(
                    "**Bebidas**",
                    key="bebidas_input",
                    value="",
                    placeholder="0.00"
                )

                productos_ordenados = sorted(productos, key=lambda x: x['precio'])
                total_productos = len(productos_ordenados)
                mitad = (total_productos + 1) // 2
                col1, col2 = st.columns(2)

                cantidades = {}
                for p in productos_ordenados[:mitad]:
                    cantidades[p['nombre']] = col1.number_input(
                        f"**{p['nombre']} (${p['precio']})**", min_value=0, step=1, key=f"col1_{p['nombre']}"
                    )
                for p in productos_ordenados[mitad:]:
                    cantidades[p['nombre']] = col2.number_input(
                        f"**{p['nombre']} (${p['precio']})**", min_value=0, step=1, key=f"col2_{p['nombre']}"
                    )

                # Campo opcional de EXTRAS
                extras = st.text_input(
                    "Monto de extras (opcional)",
                    value="",
                    placeholder="0.00",
                    key="extras_input"
                )

                calcular = st.form_submit_button("Calcular total")

                if calcular:
                    # Validar productos seleccionados
                    productos_seleccionados = [
                        {"nombre": p['nombre'], "precio": p['precio'], "cantidad": cantidades[p['nombre']]}
                        for p in productos_ordenados if cantidades[p['nombre']] > 0
                    ]

                    if not productos_seleccionados:
                        st.warning("⚠️ Debe seleccionar al menos un producto para registrar la venta.")
                        st.session_state.pop("venta_calculada", None)
                    else:
                        subtotal_productos = sum(p['precio'] * p['cantidad'] for p in productos_seleccionados)
                        try:
                            subtotal_bebidas = float(bebidas) if bebidas.strip() != "" else 0.0
                        except ValueError:
                            subtotal_bebidas = 0.0
                        try:
                            subtotal_extras = float(extras) if extras.strip() != "" else 0.0
                        except ValueError:
                            subtotal_extras = 0.0

                        # Total venta
                        total_venta = subtotal_productos + subtotal_bebidas + subtotal_extras

                        # Agregar extras como producto si > 0
                        productos_finales = productos_seleccionados.copy()
                        if subtotal_extras > 0:
                            productos_finales.append({"nombre": "Extras", "precio": subtotal_extras, "cantidad": 1})

                        st.session_state["venta_calculada"] = {
                            "venta_num": venta_num,
                            "productos": productos_finales,
                            "total_productos": subtotal_productos,
                            "bebidas": subtotal_bebidas,
                            "extras": subtotal_extras,
                            "total_venta": total_venta
                        }

                        st.success(f"Total a cobrar: **${total_venta:.2f}**")

            # Botón de registro solo si hay productos
            if "venta_calculada" in st.session_state:
                venta_data = st.session_state["venta_calculada"]

                if venta_data["productos"]:
                    if st.button("Registrar Venta"):
                        ventas.append(venta_data)
                        guardar_ventas(ventas)

                        # Envío por correo
                        enviar_correo_venta(venta_data)
                        # Envío por WhatsApp
                        enviar_whatsapp_venta(venta_data)

                        st.success(
                            f"Venta {venta_data['venta_num']} registrada con éxito. Total: ${venta_data['total_venta']:.2f}"
                        )
                        del st.session_state["venta_calculada"]
                        st.rerun()
                else:
                    st.info("Agrega al menos un producto para habilitar el registro de venta.")

        else:
            st.info("No hay productos disponibles para vender")

    elif menu == "Consultar Ventas":
        if st.sidebar.checkbox("Restablecer ventas"):
            st.sidebar.warning("⚠️ Esta acción eliminará todas las ventas y reiniciará el contador.")
            if st.sidebar.button("Confirmar restablecimiento"):
                ventas.clear()
                guardar_ventas(ventas)
                st.sidebar.success("Ventas y contador restablecidos correctamente")
                st.rerun()

        if ventas:
            opciones_ventas = ["Todas"] + [f"Venta {v['venta_num']}" for v in ventas]
            venta_seleccionada = st.selectbox("Filtar ventas", opciones_ventas)

            total_general = 0.0
            subtotal_productos = 0.0
            subtotal_bebidas = 0.0

            for v in ventas:
                if venta_seleccionada != "Todas" and venta_seleccionada != f"Venta {v['venta_num']}":
                    continue

                st.write(f"### Venta {v['venta_num']}")
                col1, col2 = st.columns([3, 1])

                if v["productos"]:
                    df = pd.DataFrame(v["productos"])
                    df["subtotal"] = df["precio"] * df["cantidad"]

                    df["precio"] = df["precio"].map(lambda x: f"${x:,.2f}")
                    df["subtotal"] = df["subtotal"].map(lambda x: f"${x:,.2f}")
                    df["cantidad"] = df["cantidad"].astype(int)

                    df.index = df.index + 1
                    col1.table(df[["nombre", "cantidad", "precio", "subtotal"]])
                else:
                    col1.write("No hay productos en esta venta")

                col2.write(f"- Productos: ${v['total_productos']:.2f}")
                col2.write(f"- Bebidas: ${v['bebidas']:.2f}")
                col2.success(f"**Total: ${v['total_venta']:.2f}**")

                subtotal_productos += v['total_productos']
                subtotal_bebidas += v['bebidas']
                total_general += v['total_venta']

                st.write("___")

            st.sidebar.info(f"**Subtotal de productos: ${subtotal_productos:.2f}**")
            st.sidebar.warning(f"**Subtotal de bebidas: ${subtotal_bebidas:.2f}**")
            st.sidebar.success(f"**Total general de todas las ventas: ${total_general:.2f}**")

        else:
            st.info("No hay ventas registradas")

