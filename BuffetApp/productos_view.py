import tkinter as tk
from tkinter import messagebox
from db_utils import get_connection, generate_unique_product_code
from theme import (
    TITLE_FONT,
    TEXT_FONT,
    apply_button_style,
    apply_treeview_style,
)


class ProductosView(tk.Frame):
    def actualizar_estilos(self, config):
        self.btn_ancho = config.get("ancho_boton", 20)
        self.btn_alto = config.get("alto_boton", 2)
        self.btn_font = config.get("fuente_boton", "Arial")
        self.color_boton = config.get("color_boton", "#f0f0f0")

    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.label = tk.Label(self, text="Gestión de Productos", font=TITLE_FONT)
        self.label.pack(pady=10)

        from tkinter import ttk
        style = apply_treeview_style()
        style.map("App.Treeview", background=[('selected', '#CCE5FF')])
        style.layout("App.Treeview", [
            ('Treeview.field', {'sticky': 'nswe', 'border': '1', 'children': [
                ('Treeview.padding', {'sticky': 'nswe', 'children': [
                    ('Treeview.treearea', {'sticky': 'nswe'})
                ]})
            ]})
        ])

        self.frame_tabla = tk.Frame(self)
        self.frame_tabla.pack(pady=10, padx=60, fill="x")
        self.tree = ttk.Treeview(
            self.frame_tabla,
            columns=("id", "codigo", "nombre", "precio", "stock", "categoria", "activo", "visible"),
            show="headings",
            height=12,
            style="App.Treeview",
        )
        self.tree.heading("codigo", text="Código")
        self.tree.heading("nombre", text="Descripción")
        self.tree.heading("precio", text="Precio Venta")
        self.tree.heading("stock", text="Stock")
        self.tree.heading("categoria", text="Categoría")
        self.tree.heading("visible", text="Visible")
        self.tree.column("id", width=0, stretch=False)
        self.tree.column("codigo", width=80)
        self.tree.column("nombre", width=150)
        self.tree.column("precio", width=80)
        self.tree.column("stock", width=80)
        self.tree.column("categoria", width=110)
        self.tree.column("activo", width=0, stretch=False)
        self.tree.column("visible", width=60)
        self.tree.pack(ipadx=10, ipady=10, fill="x", expand=True)

        self.colores_categoria = {
            'Comida': '#FFDD99',
            'Bebida': '#99CCFF',
            'Otros': '#DDFFDD',
            'Sin categoría': '#F4CCCC',
        }

        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.tree.bind("<Double-1>", self.abrir_edicion_producto)

        self.frame_form = tk.Frame(self)
        self.frame_form.pack(pady=10)
        self.btn_agregar = tk.Button(self.frame_form, text="Agregar\nNuevo", command=self.iniciar_agregar)
        apply_button_style(self.btn_agregar, style="productos")
        apply_button_style(self.btn_agregar, style="success")
        self.btn_agregar.grid(row=6, column=0, pady=6, padx=3)
        self.btn_editar = tk.Button(self.frame_form, text="Editar", command=self.abrir_edicion_producto_btn)
        apply_button_style(self.btn_editar, style="productos")
        apply_button_style(self.btn_editar, style="primary")
        self.btn_editar.grid(row=6, column=1, pady=6, padx=3)
        self.btn_eliminar = tk.Button(self.frame_form, text="Eliminar", command=self.eliminar_producto)
        apply_button_style(self.btn_eliminar, style="productos")
        apply_button_style(self.btn_eliminar, style="danger")
        self.btn_eliminar.grid(row=6, column=2, pady=6, padx=3)

        self.producto_seleccionado = None
        self.btn_editar.config(state='disabled')
        self.btn_eliminar.config(state='disabled')
        self.label_stock_info = tk.Label(self, text="Solo se descuenta stock si 'Contabilizar stock' está activado.", font=TEXT_FONT, fg="#555")
        self.label_stock_info.pack(pady=(0, 8))

        self.cargar_categorias()
        self.cargar_productos()

    def cargar_categorias(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, descripcion FROM Categoria_Producto")
        cats = cursor.fetchall()
        conn.close()
        self.categorias = {str(cid): desc for cid, desc in cats}

    def cargar_productos(self):
        self.tree.delete(*self.tree.get_children())
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT p.id, p.codigo_producto, p.nombre, p.precio_venta, p.stock_actual, c.descripcion, p.stock_minimo, p.categoria_id, p.visible, COALESCE(p.contabiliza_stock,1) FROM products p LEFT JOIN Categoria_Producto c ON p.categoria_id = c.id")
        except Exception:
            cursor.execute("SELECT p.id, p.codigo_producto, p.nombre, p.precio_venta, p.stock_actual, c.descripcion, p.stock_minimo, p.categoria_id, p.visible, 1 as contabiliza_stock FROM products p LEFT JOIN Categoria_Producto c ON p.categoria_id = c.id")
        productos = cursor.fetchall()
        conn.close()
        for pid, codigo, nombre, precio, stock, categoria, activo, categoria_id, visible, contabiliza in productos:
            cat = categoria if categoria else 'Sin categoría'
            color = self.colores_categoria.get(cat, '#EAF1FB')
            tag = f'cat_{cat}'
            if not self.tree.tag_has(tag):
                self.tree.tag_configure(tag, background=color)
            extra = ' (No cont.)' if int(contabiliza or 1) == 0 else ''
            nombre_txt = (nombre or '') + extra
            try:
                act_txt = 'Sí' if int(activo or 0) > 0 else 'No'
            except Exception:
                act_txt = 'Sí' if (1 if activo else 0) > 0 else 'No'
            vis_txt = 'Sí' if int(visible or 0) > 0 else 'No'
            self.tree.insert("", tk.END, values=(pid, (codigo or '').upper(), nombre_txt, precio, stock, categoria, act_txt, vis_txt), tags=(tag,))

        self.producto_seleccionado = None
        self.btn_editar.config(state='disabled')
        self.btn_eliminar.config(state='disabled')

    def on_select(self, event):
        seleccion = self.tree.selection()
        if not seleccion:
            self.producto_seleccionado = None
            self.btn_editar.config(state='disabled')
            self.btn_eliminar.config(state='disabled')
            return
        item = self.tree.item(seleccion[0])['values']
        self.producto_seleccionado = item[0]
        self.btn_editar.config(state='normal')
        self.btn_eliminar.config(state='normal')

    def iniciar_agregar(self):
        self._abrir_agregar_producto()

    def abrir_edicion_producto(self, event=None):
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Edición", "Seleccione un producto para editar.")
            return
        item = self.tree.item(seleccion[0])['values']
        self._abrir_edicion_producto(item)

    def abrir_edicion_producto_btn(self):
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Edición", "Seleccione un producto para editar.")
            return
        item = self.tree.item(seleccion[0])['values']
        self._abrir_edicion_producto(item)

    def cancelar_accion(self):
        self.producto_seleccionado = None
        self.btn_editar.config(state='disabled')
        self.btn_eliminar.config(state='disabled')

    def eliminar_producto(self):
        if not self.producto_seleccionado:
            messagebox.showwarning("Eliminación", "Seleccione un producto para eliminar.")
            return
        nombre = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT nombre FROM products WHERE id=?", (self.producto_seleccionado,))
            row = cursor.fetchone()
            if row:
                nombre = row[0]
            conn.close()
        except Exception:
            pass
        if not messagebox.askyesno("Confirmar eliminación", f"¿Está seguro que desea eliminar el producto '{nombre if nombre else ''}'?"):
            return
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM products WHERE id=?", (self.producto_seleccionado,))
            conn.commit()
            conn.close()
            self.cargar_productos()
            messagebox.showinfo("Producto", "Producto eliminado definitivamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo eliminar el producto.\n{e}")
        self.cancelar_accion()

    def _abrir_agregar_producto(self):
        add_win = tk.Toplevel(self)
        add_win.title("Agregar Producto")
        add_win.transient(self)
        add_win.grab_set()
        ancho = 350
        alto = 520
        x = self.winfo_screenwidth() // 2 - ancho // 2
        y = self.winfo_screenheight() // 2 - alto // 2
        add_win.geometry(f"{ancho}x{alto}+{x}+{y}")

        tk.Label(add_win, text="Descripción:", font=("Arial", 12)).pack(pady=6)
        entry_nombre = tk.Entry(add_win, font=("Arial", 12))
        entry_nombre.pack(pady=2)

        tk.Label(add_win, text="Precio Venta:", font=("Arial", 12)).pack(pady=6)
        entry_precio = tk.Entry(add_win, font=("Arial", 12))
        entry_precio.pack(pady=2)

        tk.Label(add_win, text="Categoría:", font=("Arial", 12)).pack(pady=6)
        from tkinter import ttk
        combo_categoria = ttk.Combobox(add_win, values=list(self.categorias.values()), state="readonly", font=("Arial", 12))
        combo_categoria.pack(pady=2)
        combo_categoria.set('')

        var_visible = tk.IntVar(value=1)
        var_contab = tk.IntVar(value=1)
        check_visible = tk.Checkbutton(add_win, text="Visible", variable=var_visible, font=("Arial", 12))
        check_visible.pack(pady=6)

        # Contabilizar antes del Stock
        check_contab = tk.Checkbutton(add_win, text="Contabilizar stock", variable=var_contab, font=("Arial", 12))
        check_contab.pack(pady=6)

        tk.Label(add_win, text="Stock:", font=("Arial", 12)).pack(pady=6)
        entry_stock = tk.Entry(add_win, font=("Arial", 12))
        entry_stock.pack(pady=2)

        def _toggle_stock_state():
            if var_contab.get() == 1:
                entry_stock.config(state='normal')
            else:
                entry_stock.delete(0, tk.END)
                entry_stock.insert(0, '0')
                entry_stock.config(state='disabled')

        check_contab.configure(command=_toggle_stock_state)
        _toggle_stock_state()

        frame_btns = tk.Frame(add_win)
        frame_btns.pack(pady=18)

        def confirmar():
            # Generar código automáticamente a partir del nombre
            nombre = entry_nombre.get().strip()
            precio = entry_precio.get().strip()
            stock = entry_stock.get().strip()
            cat_desc_sel = combo_categoria.get().strip()
            visible = var_visible.get()
            if not nombre or not precio or not cat_desc_sel:
                messagebox.showwarning("Datos incompletos", "Complete todos los campos.")
                return
            conn = get_connection()
            cursor = conn.cursor()
            # Código único generado
            codigo = generate_unique_product_code(nombre)
            try:
                precio_val = float(precio)
            except Exception:
                messagebox.showerror("Error", "Precio debe ser un valor numérico.")
                return
            if int(var_contab.get()) == 1:
                try:
                    stock_val = int(stock)
                except Exception:
                    messagebox.showerror("Error", "Stock debe ser un número entero.")
                    return
            else:
                stock_val = 0
            if stock_val > 999:
                messagebox.showerror("Error", "El stock máximo permitido es 999.")
                return
            if precio_val > 999999:
                messagebox.showerror("Error", "El precio máximo permitido es 999999.")
                return
            categoria_id = None
            try:
                categoria_id = [k for k, v in self.categorias.items() if v == cat_desc_sel][0]
            except Exception:
                categoria_id = None
            cursor.execute("SELECT COUNT(*) FROM products WHERE nombre=? AND categoria_id=?", (nombre, categoria_id))
            if cursor.fetchone()[0]:
                conn.close()
                messagebox.showerror("Error", "Ya existe un producto con esa descripción en la misma categoría.")
                return
            try:
                # calcular siguiente orden_visual (al final)
                # Forzar cast a INTEGER por si la columna quedó como TEXT en alguna DB vieja
                cursor.execute("SELECT COALESCE(MAX(CAST(orden_visual AS INTEGER)), 0) FROM products")
                try:
                    next_order = int((cursor.fetchone() or [0])[0]) + 1
                except Exception:
                    next_order = 1
                cursor.execute(
                    "INSERT INTO products (codigo_producto, nombre, precio_venta, stock_actual, stock_minimo, categoria_id, precio_compra, visible, contabiliza_stock, orden_visual) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (codigo, nombre, float(precio_val), int(stock_val), 3, (int(categoria_id) if categoria_id is not None else None), 0, int(visible), int(var_contab.get()), int(next_order))
                )
                conn.commit()
                conn.close()
                self.cargar_productos()
                add_win.destroy()
                messagebox.showinfo("Producto", "Producto agregado correctamente.")
            except Exception as e:
                conn.close()
                messagebox.showerror("Error", f"No se pudo guardar el producto.\n{e}")

        def cancelar():
            add_win.destroy()

        btn_confirmar = tk.Button(frame_btns, text="Confirmar", command=confirmar, bg="#4CAF50", fg="white", font=("Arial", 12), width=10)
        btn_confirmar.pack(side=tk.LEFT, padx=8)
        btn_cancelar = tk.Button(frame_btns, text="Cancelar", command=cancelar, font=("Arial", 12), width=10)
        btn_cancelar.pack(side=tk.LEFT, padx=8)

    def _abrir_edicion_producto(self, item):
        edit_win = tk.Toplevel(self)
        edit_win.title("Editar Producto")
        edit_win.transient(self)
        edit_win.grab_set()
        ancho = 350
        alto = 520
        x = self.winfo_screenwidth() // 2 - ancho // 2
        y = self.winfo_screenheight() // 2 - alto // 2
        edit_win.geometry(f"{ancho}x{alto}+{x}+{y}")

        tk.Label(edit_win, text="Descripción:", font=("Arial", 12)).pack(pady=6)
        entry_nombre = tk.Entry(edit_win, font=("Arial", 12))
        entry_nombre.pack(pady=2)
        entry_nombre.insert(0, item[2])

        tk.Label(edit_win, text="Precio Venta:", font=("Arial", 12)).pack(pady=6)
        entry_precio = tk.Entry(edit_win, font=("Arial", 12))
        entry_precio.pack(pady=2)
        entry_precio.insert(0, item[3])

        tk.Label(edit_win, text="Categoría:", font=("Arial", 12)).pack(pady=6)
        from tkinter import ttk
        combo_categoria = ttk.Combobox(edit_win, values=list(self.categorias.values()), state="readonly", font=("Arial", 12))
        combo_categoria.pack(pady=2)
        cat_desc = item[5]
        idx = list(self.categorias.values()).index(cat_desc) if cat_desc in self.categorias.values() else 0
        combo_categoria.current(idx)

        var_visible = tk.IntVar(value=1 if item[7] == 'Sí' else 0)

        contabiliza_val = 1
        try:
            conn0 = get_connection()
            cur0 = conn0.cursor()
            cur0.execute("SELECT COALESCE(contabiliza_stock,1) FROM products WHERE id=?", (item[0],))
            row0 = cur0.fetchone()
            conn0.close()
            if row0 and row0[0] is not None:
                contabiliza_val = int(row0[0])
        except Exception:
            contabiliza_val = 1
        var_contab = tk.IntVar(value=contabiliza_val)

        check_visible = tk.Checkbutton(edit_win, text="Visible", variable=var_visible, font=("Arial", 12))
        check_visible.pack(pady=6)

        check_contab = tk.Checkbutton(edit_win, text="Contabilizar stock", variable=var_contab, font=("Arial", 12))
        check_contab.pack(pady=6)

        tk.Label(edit_win, text="Stock:", font=("Arial", 12)).pack(pady=6)
        entry_stock = tk.Entry(edit_win, font=("Arial", 12))
        entry_stock.pack(pady=2)
        entry_stock.insert(0, item[4])

        def _toggle_stock_state_edit():
            if var_contab.get() == 1:
                entry_stock.config(state='normal')
            else:
                entry_stock.delete(0, tk.END)
                entry_stock.insert(0, '0')
                entry_stock.config(state='disabled')

        check_contab.configure(command=_toggle_stock_state_edit)
        _toggle_stock_state_edit()

        frame_btns = tk.Frame(edit_win)
        frame_btns.pack(pady=18)

        def confirmar():
            nombre = entry_nombre.get().strip()
            precio = entry_precio.get().strip()
            stock = entry_stock.get().strip()
            cat_desc_sel = combo_categoria.get().strip()
            visible = var_visible.get()
            if not nombre or not precio or not cat_desc_sel:
                messagebox.showwarning("Datos incompletos", "Complete todos los campos.")
                return
            conn = get_connection()
            cursor = conn.cursor()
            try:
                precio_val = float(precio)
            except Exception:
                messagebox.showerror("Error", "Precio debe ser un valor numérico.")
                return
            if int(var_contab.get()) == 1:
                try:
                    stock_val = int(stock)
                except Exception:
                    messagebox.showerror("Error", "Stock debe ser un número entero.")
                    return
            else:
                stock_val = 0
            if stock_val > 999:
                messagebox.showerror("Error", "El stock máximo permitido es 999.")
                return
            if precio_val > 999999:
                messagebox.showerror("Error", "El precio máximo permitido es 999999.")
                return
            categoria_id = None
            try:
                categoria_id = [k for k, v in self.categorias.items() if v == cat_desc_sel][0]
            except Exception:
                categoria_id = None
            cursor.execute("SELECT COUNT(*) FROM products WHERE nombre=? AND categoria_id=? AND id<>?", (nombre, categoria_id, item[0]))
            if cursor.fetchone()[0]:
                conn.close()
                messagebox.showerror("Error", "Ya existe un producto con esa descripción en la misma categoría.")
                return
            try:
                # Si el código actual está vacío/NULL, generarlo automáticamente a partir del nombre
                code_to_set = None
                try:
                    cursor.execute("SELECT codigo_producto FROM products WHERE id=?", (int(item[0]),))
                    rcode = cursor.fetchone()
                    current_code = (rcode[0] if rcode else None)
                    if not current_code or not str(current_code).strip():
                        code_to_set = generate_unique_product_code(nombre)
                except Exception:
                    code_to_set = None

                if code_to_set:
                    cursor.execute(
                        "UPDATE products SET codigo_producto=?, nombre=?, precio_venta=?, stock_actual=?, categoria_id=?, visible=?, contabiliza_stock=? WHERE id=?",
                        (code_to_set, nombre, float(precio_val), int(stock_val), (int(categoria_id) if categoria_id is not None else None), int(visible), int(var_contab.get()), int(item[0]))
                    )
                else:
                    cursor.execute(
                        "UPDATE products SET nombre=?, precio_venta=?, stock_actual=?, categoria_id=?, visible=?, contabiliza_stock=? WHERE id=?",
                        (nombre, float(precio_val), int(stock_val), (int(categoria_id) if categoria_id is not None else None), int(visible), int(var_contab.get()), int(item[0]))
                    )
                conn.commit()
                conn.close()
                self.cargar_productos()
                edit_win.destroy()
                messagebox.showinfo("Producto", "Producto editado correctamente.")
            except Exception as e:
                conn.close()
                messagebox.showerror("Error", f"No se pudo guardar el producto.\n{e}")

        def cancelar():
            edit_win.destroy()

        btn_confirmar = tk.Button(frame_btns, text="Confirmar", command=confirmar, bg="#4CAF50", fg="white", font=("Arial", 12), width=10)
        btn_confirmar.pack(side=tk.LEFT, padx=8)
        btn_cancelar = tk.Button(frame_btns, text="Cancelar", command=cancelar, font=("Arial", 12), width=10)
        btn_cancelar.pack(side=tk.LEFT, padx=8)
