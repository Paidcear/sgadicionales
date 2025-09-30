import streamlit as st
import json
import os
import pandas as pd

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

# Funciones de persistencia
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

# Sidebar con selectbox
st.sidebar.title("Menú")
opcion = st.sidebar.selectbox("Selecciona una opción:", ["Ventas", "Productos"], label_visibility="collapsed")

# -----------------------
# Módulo de Productos
# -----------------------
if opcion == "Productos":
    #st.title("Gestión de Productos")
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
            #st.subheader("Lista de Productos")
            # Convertir a DataFrame
            df = pd.DataFrame(productos)
            df.index = df.index + 1  # índice comenzando desde 1
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
            
            # Formulario de captura
            with st.form("form_venta", clear_on_submit=True):
                bebidas = st.text_input("**Bebidas**", key="bebidas_input")

                # 🔹 Ordenar productos por precio (ascendente)
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
                
                calcular = st.form_submit_button("Calcular total")
                
                if calcular:
                    # Calcular subtotal de productos
                    subtotal_productos = sum(p['precio'] * cantidades[p['nombre']] for p in productos_ordenados)
                    try:
                        subtotal_bebidas = float(bebidas) if bebidas.strip() != "" else 0.0
                    except ValueError:
                        subtotal_bebidas = 0.0
                    total_venta = subtotal_productos + subtotal_bebidas
                    
                    # Guardar en session_state para usar afuera del form
                    st.session_state["venta_calculada"] = {
                        "venta_num": venta_num,
                        "productos": [
                            {"nombre": p['nombre'], "precio": p['precio'], "cantidad": cantidades[p['nombre']]}
                            for p in productos_ordenados if cantidades[p['nombre']] > 0
                        ],
                        "total_productos": subtotal_productos,
                        "bebidas": subtotal_bebidas,
                        "total_venta": total_venta
                    }
                    
                    st.success(f"Total a cobrar: **${total_venta}**")

            
            # Botón de registrar fuera del form
            if "venta_calculada" in st.session_state:
                if st.button("Registrar Venta"):
                    venta_data = st.session_state["venta_calculada"]
                    
                    if venta_data["productos"] or venta_data["bebidas"] > 0:
                        ventas.append(venta_data)
                        guardar_ventas(ventas)
                        st.success(f"Venta {venta_data['venta_num']} registrada con éxito. Total: ${venta_data['total_venta']}")
                        del st.session_state["venta_calculada"]  # limpiar
                        st.rerun()
                    else:
                        st.warning("Debe ingresar al menos un producto o monto en bebidas")
        
        else:
            st.info("No hay productos disponibles para vender")


        
    elif menu == "Consultar Ventas":
        # Checkbox en el sidebar para activar la opción de restablecer
        if st.sidebar.checkbox("Restablecer ventas"):
            st.sidebar.warning("⚠️ Esta acción eliminará todas las ventas y reiniciará el contador.")
            if st.sidebar.button("Confirmar restablecimiento"):
                ventas.clear()
                guardar_ventas(ventas)
                st.sidebar.success("Ventas y contador restablecidos correctamente")
                st.rerun()

        if ventas:
            #st.subheader("Ventas Registradas")

            # 🔹 Filtro por venta
            opciones_ventas = ["Todas"] + [f"Venta {v['venta_num']}" for v in ventas]
            venta_seleccionada = st.selectbox("Filtar ventas", opciones_ventas)

            total_general = 0.0
            subtotal_productos = 0.0
            subtotal_bebidas = 0.0

            for v in ventas:
                if venta_seleccionada != "Todas" and venta_seleccionada != f"Venta {v['venta_num']}":
                    continue  # saltar ventas que no coinciden con el filtro

                st.write(f"### Venta {v['venta_num']}")
                col1, col2 = st.columns([3, 1])

                # Columna 1: tabla con productos
                if v["productos"]:
                    df = pd.DataFrame(v["productos"])
                    df["subtotal"] = df["precio"] * df["cantidad"]

                    # Formatear columnas
                    df["precio"] = df["precio"].map(lambda x: f"${x:,.2f}")
                    df["subtotal"] = df["subtotal"].map(lambda x: f"${x:,.2f}")
                    df["cantidad"] = df["cantidad"].astype(int)

                    df.index = df.index + 1
                    col1.table(df[["nombre", "cantidad", "precio", "subtotal"]])
                else:
                    col1.write("No hay productos en esta venta")

                # Columna 2: totales
                col2.write(f"- Productos: ${v['total_productos']:.2f}")
                col2.write(f"- Bebidas: ${v['bebidas']:.2f}")
                col2.success(f"**Total: ${v['total_venta']:.2f}**")

                # Acumular totales
                subtotal_productos += v['total_productos']
                subtotal_bebidas += v['bebidas']
                total_general += v['total_venta']

                st.write("___")

            # Totales acumulados en sidebar
            st.sidebar.info(f"**Subtotal de productos: ${subtotal_productos:.2f}**")
            st.sidebar.warning(f"**Subtotal de bebidas: ${subtotal_bebidas:.2f}**")
            st.sidebar.success(f"**Total general de todas las ventas: ${total_general:.2f}**")

        else:
            st.info("No hay ventas registradas")


