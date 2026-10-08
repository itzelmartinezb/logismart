import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime

from app.config import settings
from app.db.mongo import MongoDB
from app.repositories.repository import Repository
from app.services.rules_engine import evaluar_camion, tabla_verdad
from app.services.llm_service import LLMService
from app.services.classifier import hybrid_classify
from app.services.reports import export_json, export_csv, export_pdf


COLLECTIONS = [
    "camiones",
    "accesos",
    "incidentes",
    "riesgos_eticos",
    "evaluaciones_llm",
]


class LogiSmartGUI(tk.Tk):

    def __init__(self):
        super().__init__()

        self.title("LogiSmart | Control Logístico Inteligente")
        self.geometry("1250x800")
        self.minsize(1050, 700)
        self.configure(bg="#F7E7CE")

        self.db = MongoDB(settings.mongodb_uri, settings.database)
        self.repo = Repository(self.db)
        self.llm = LLMService(
            settings.ollama_host,
            settings.ollama_model,
            settings.llm_timeout
        )

        self.status = tk.StringVar(value="Conectando...")

        self._style()
        self._build()
        self._connect()

    # =========================================================
    # ESTILO
    # =========================================================

    def _style(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure(
            "TButton",
            font=("Segoe UI", 10),
            padding=(12, 8)
        )

        style.configure(
            "Title.TLabel",
            font=("Segoe UI", 22, "bold"),
            foreground="#075B66",
            background="#FFF8EC"
        )

        style.configure(
            "Subtitle.TLabel",
            font=("Segoe UI", 10),
            foreground="#6B7C80",
            background="#FFF8EC"
        )

        style.configure(
            "Card.TFrame",
            background="#FFFFFF"
        )

        style.configure(
            "CardTitle.TLabel",
            font=("Segoe UI", 10, "bold"),
            foreground="#6B7C80",
            background="#FFFFFF"
        )

        style.configure(
            "CardValue.TLabel",
            font=("Segoe UI", 26, "bold"),
            foreground="#075B66",
            background="#FFFFFF"
        )

        style.configure(
            "Menu.TButton",
            font=("Segoe UI", 10, "bold"),
            padding=(15, 12),
            foreground="#FFFFFF",
            background="#087E8B"
        )

        style.map(
            "Menu.TButton",
            background=[
                ("active", "#20B2AA"),
                ("pressed", "#075B66")
            ]
        )

        style.configure(
            "Treeview",
            rowheight=30,
            font=("Segoe UI", 9)
        )

        style.configure(
            "Treeview.Heading",
            font=("Segoe UI", 9, "bold")
        )

    # =========================================================
    # CONSTRUCCIÓN GENERAL
    # =========================================================

    def _build(self):

        self.main = tk.Frame(
            self,
            bg="#F7E7CE"
        )
        self.main.pack(fill="both", expand=True)

        # ---------------- SIDEBAR ----------------

        self.sidebar = tk.Frame(
            self.main,
            bg="#075B66",
            width=220
        )
        self.sidebar.pack(
            side="left",
            fill="y"
        )
        self.sidebar.pack_propagate(False)

        logo = tk.Label(
            self.sidebar,
            text="LOGISMART",
            bg="#075B66",
            fg="#FFFFFF",
            font=("Segoe UI", 20, "bold")
        )
        logo.pack(
            pady=(28, 3)
        )

        subtitle = tk.Label(
            self.sidebar,
            text="Control logístico inteligente",
            bg="#075B66",
            fg="#BDEDE8",
            font=("Segoe UI", 8)
        )
        subtitle.pack(
            pady=(0, 25)
        )

        self._menu_button("⌂  Inicio", 0)
        self._menu_button("▣  Control de acceso", 1)
        self._menu_button("✓  Tablas de verdad", 2)
        self._menu_button("⚠  Incidentes", 3)
        self._menu_button("☁  Asistente", 4)
        self._menu_button("⚖  Riesgos éticos", 5)
        self._menu_button("▤  Base de datos", 6)
        self._menu_button("▤  Reportes", 7)
        self._menu_button("⚙  Configuración", 8)

        spacer = tk.Frame(
            self.sidebar,
            bg="#075B66"
        )
        spacer.pack(
            fill="both",
            expand=True
        )

        tk.Label(
            self.sidebar,
            textvariable=self.status,
            bg="#075B66",
            fg="#BDEDE8",
            font=("Segoe UI", 8),
            wraplength=190,
            justify="left"
        ).pack(
            padx=15,
            pady=(5, 20),
            anchor="w"
        )

        # ---------------- CONTENIDO ----------------

        self.content = tk.Frame(
            self.main,
            bg="#FFF8EC"
        )
        self.content.pack(
            side="left",
            fill="both",
            expand=True
        )

        self.nb = ttk.Notebook(
            self.content
        )
        self.nb.pack(
            fill="both",
            expand=True
        )

        self._dashboard()
        self._access()
        self._truth()
        self._incidents()
        self._assistant()
        self._risks()
        self._crud()
        self._reports()
        self._config()

        # Ocultar pestañas del Notebook.
        style = ttk.Style(self)
        style.layout(
            "TNotebook.Tab",
            []
        )

    def _menu_button(self, text, index):
        button = ttk.Button(
            self.sidebar,
            text=text,
            style="Menu.TButton",
            command=lambda i=index: self.show_tab(i)
        )

        button.pack(
            fill="x",
            padx=12,
            pady=3
        )

    def show_tab(self, index):
        self.nb.select(index)

        if index == 0:
            self.refresh_dashboard()

        elif index == 2:
            self.refresh_truth()

        elif index == 5:
            self.refresh_risks()

        elif index == 6:
            self.load_crud()

    # =========================================================
    # CONEXIÓN
    # =========================================================

    def _connect(self):
        ok, msg = self.db.connect()
        self.status.set(msg)

        if not ok:
            messagebox.showwarning(
                "MongoDB",
                msg
            )

        self.refresh_all()

    # =========================================================
    # PESTAÑAS
    # =========================================================

    def _tab(self, name):
        frame = tk.Frame(
            self.nb,
            bg="#FFF8EC"
        )

        self.nb.add(
            frame,
            text=name
        )

        return frame

    # =========================================================
    # DASHBOARD
    # =========================================================

    def _dashboard(self):

        self.dashboard = self._tab("Inicio")

        header = tk.Frame(
            self.dashboard,
            bg="#FFF8EC"
        )
        header.pack(
            fill="x",
            padx=30,
            pady=(25, 10)
        )

        tk.Label(
            header,
            text="Buenos días 👋",
            bg="#FFF8EC",
            fg="#075B66",
            font=("Segoe UI", 25, "bold")
        ).pack(
            anchor="w"
        )

        tk.Label(
            header,
            text="Panel de control de LogiSmart",
            bg="#FFF8EC",
            fg="#6B7C80",
            font=("Segoe UI", 11)
        ).pack(
            anchor="w",
            pady=(3, 0)
        )

        self.cards = tk.Frame(
            self.dashboard,
            bg="#FFF8EC"
        )
        self.cards.pack(
            fill="x",
            padx=25,
            pady=20
        )

        self.card_camiones = self._card(
            self.cards,
            "CAMIONES",
            "0"
        )

        self.card_accesos = self._card(
            self.cards,
            "ACCESOS",
            "0"
        )

        self.card_incidentes = self._card(
            self.cards,
            "INCIDENTES",
            "0"
        )

        self.card_riesgos = self._card(
            self.cards,
            "RIESGOS CRÍTICOS",
            "0"
        )

        info = tk.Frame(
            self.dashboard,
            bg="#FFFFFF"
        )
        info.pack(
            fill="both",
            expand=True,
            padx=30,
            pady=(5, 25)
        )

        tk.Label(
            info,
            text="Sistema híbrido de decisión",
            bg="#FFFFFF",
            fg="#075B66",
            font=("Segoe UI", 15, "bold")
        ).pack(
            anchor="w",
            padx=20,
            pady=(20, 5)
        )

        tk.Label(
            info,
            text=(
                "LogiSmart combina reglas de lógica proposicional, "
                "MongoDB y un modelo LLM para apoyar la gestión "
                "de operaciones logísticas."
            ),
            bg="#FFFFFF",
            fg="#6B7C80",
            font=("Segoe UI", 10),
            wraplength=850,
            justify="left"
        ).pack(
            anchor="w",
            padx=20
        )

        ttk.Button(
            info,
            text="Actualizar información",
            command=self.refresh_dashboard
        ).pack(
            anchor="w",
            padx=20,
            pady=20
        )

    def _card(self, parent, title, value):

        card = tk.Frame(
            parent,
            bg="#FFFFFF",
            highlightbackground="#DCE9E7",
            highlightthickness=1
        )

        card.pack(
            side="left",
            fill="both",
            expand=True,
            padx=7
        )

        tk.Label(
            card,
            text=title,
            bg="#FFFFFF",
            fg="#6B7C80",
            font=("Segoe UI", 9, "bold")
        ).pack(
            anchor="w",
            padx=18,
            pady=(15, 3)
        )

        label = tk.Label(
            card,
            text=value,
            bg="#FFFFFF",
            fg="#075B66",
            font=("Segoe UI", 27, "bold")
        )

        label.pack(
            anchor="w",
            padx=18,
            pady=(0, 15)
        )

        return label

    def refresh_dashboard(self):

        try:
            camiones = len(
                self.repo.list("camiones")
            )

            accesos = len(
                self.repo.list("accesos")
            )

            incidentes = len([
                x for x in self.repo.list("incidentes")
                if x.get("estado") != "cerrado"
            ])

            riesgos = 0

            for x in self.repo.list("riesgos_eticos"):
                valor = x.get(
                    "riesgo_residual",
                    x.get("puntaje_residual", 0)
                )

                try:
                    if float(valor) >= 12:
                        riesgos += 1
                except Exception:
                    pass

            self.card_camiones.config(
                text=str(camiones)
            )

            self.card_accesos.config(
                text=str(accesos)
            )

            self.card_incidentes.config(
                text=str(incidentes)
            )

            self.card_riesgos.config(
                text=str(riesgos)
            )

        except Exception as e:

            self.status.set(
                f"Error actualizando dashboard: {e}"
            )

    # =========================================================
    # CONTROL DE ACCESO
    # =========================================================

    def _access(self):

        frame = self._tab(
            "Control de acceso"
        )

        tk.Label(
            frame,
            text="Control de acceso",
            bg="#FFF8EC",
            fg="#075B66",
            font=("Segoe UI", 20, "bold")
        ).pack(
            anchor="w",
            padx=25,
            pady=(20, 5)
        )

        tk.Label(
            frame,
            text="Evalúa las condiciones de seguridad del vehículo.",
            bg="#FFF8EC",
            fg="#6B7C80",
            font=("Segoe UI", 10)
        ).pack(
            anchor="w",
            padx=25
        )

        body = tk.Frame(
            frame,
            bg="#FFF8EC"
        )
        body.pack(
            fill="both",
            expand=True,
            padx=25,
            pady=20
        )

        left = tk.Frame(
            body,
            bg="#FFFFFF",
            width=350
        )
        left.pack(
            side="left",
            fill="y",
            padx=(0, 15)
        )

        left.pack_propagate(False)

        tk.Label(
            left,
            text="Condiciones",
            bg="#FFFFFF",
            fg="#075B66",
            font=("Segoe UI", 14, "bold")
        ).pack(
            anchor="w",
            padx=20,
            pady=(20, 10)
        )

        self.vars = {
            key: tk.BooleanVar()
            for key in "PQRS"
        }

        labels = {
            "P": "Autorización",
            "Q": "Peso excedido",
            "R": "Material peligroso",
            "S": "Certificación vigente"
        }

        for key in "PQRS":

            ttk.Checkbutton(
                left,
                text=f"{key} - {labels[key]}",
                variable=self.vars[key]
            ).pack(
                anchor="w",
                padx=20,
                pady=6
            )

        self.cert = tk.BooleanVar(
            value=True
        )

        self.hor = tk.BooleanVar(
            value=True
        )

        ttk.Checkbutton(
            left,
            text="V - Certificación vigente",
            variable=self.cert
        ).pack(
            anchor="w",
            padx=20,
            pady=6
        )

        ttk.Checkbutton(
            left,
            text="H - Horario seguro",
            variable=self.hor
        ).pack(
            anchor="w",
            padx=20,
            pady=6
        )

        ttk.Button(
            left,
            text="Evaluar acceso",
            command=self.evaluate_access
        ).pack(
            padx=20,
            pady=20,
            fill="x"
        )

        right = tk.Frame(
            body,
            bg="#FFFFFF"
        )
        right.pack(
            side="left",
            fill="both",
            expand=True
        )

        tk.Label(
            right,
            text="Resultado",
            bg="#FFFFFF",
            fg="#075B66",
            font=("Segoe UI", 14, "bold")
        ).pack(
            anchor="w",
            padx=20,
            pady=(20, 10)
        )

        self.access_out = tk.Text(
            right,
            bg="#F7FBFA",
            fg="#174A52",
            font=("Consolas", 10),
            relief="flat",
            padx=15,
            pady=15
        )

        self.access_out.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=(0, 20)
        )

    def evaluate_access(self):

        datos = evaluar_camion(
            *(self.vars[k].get() for k in "PQRS"),
            self.cert.get(),
            self.hor.get()
        )

        self.access_out.delete(
            "1.0",
            "end"
        )

        self.access_out.insert(
            "end",
            json.dumps(
                datos,
                ensure_ascii=False,
                indent=2
            )
        )

        try:
            registro = dict(datos)
            registro["marca_tiempo"] = datetime.now()
            registro["operador"] = "GUI"

            self.db.create(
                "accesos",
                registro
            )

            self.refresh_dashboard()

        except Exception:
            pass

    # =========================================================
    # TABLA DE VERDAD
    # =========================================================

    def _truth(self):

        frame = self._tab(
            "Tablas de verdad"
        )

        tk.Label(
            frame,
            text="Tablas de verdad",
            bg="#FFF8EC",
            fg="#075B66",
            font=("Segoe UI", 20, "bold")
        ).pack(
            anchor="w",
            padx=25,
            pady=(20, 15)
        )

        self.truth = ttk.Treeview(
            frame,
            columns=[
                "P",
                "Q",
                "R",
                "S",
                "V",
                "H",
                "A",
                "E",
                "ACCESO"
            ],
            show="headings"
        )

        for column in self.truth["columns"]:

            self.truth.heading(
                column,
                text=column
            )

            self.truth.column(
                column,
                width=80,
                anchor="center"
            )

        self.truth.pack(
            fill="both",
            expand=True,
            padx=25,
            pady=(0, 25)
        )

        self.refresh_truth()

    def refresh_truth(self):

        for item in self.truth.get_children():
            self.truth.delete(item)

        for row in tabla_verdad():

            self.truth.insert(
                "",
                "end",
                values=[
                    int(row[key])
                    for key in self.truth["columns"]
                ]
            )

    # =========================================================
    # INCIDENTES
    # =========================================================

    def _incidents(self):

        frame = self._tab(
            "Incidentes"
        )

        tk.Label(
            frame,
            text="Clasificación de incidentes",
            bg="#FFF8EC",
            fg="#075B66",
            font=("Segoe UI", 20, "bold")
        ).pack(
            anchor="w",
            padx=25,
            pady=(20, 5)
        )

        tk.Label(
            frame,
            text="Combina reglas y LLM para clasificar un correo.",
            bg="#FFF8EC",
            fg="#6B7C80",
            font=("Segoe UI", 10)
        ).pack(
            anchor="w",
            padx=25
        )

        self.mail = tk.Text(
            frame,
            height=8,
            font=("Segoe UI", 10),
            relief="flat",
            bg="#FFFFFF"
        )

        self.mail.pack(
            fill="x",
            padx=25,
            pady=20
        )

        bar = tk.Frame(
            frame,
            bg="#FFF8EC"
        )

        bar.pack(
            fill="x",
            padx=25
        )

        ttk.Button(
            bar,
            text="Clasificar híbrido",
            command=self.classify_incident
        ).pack(
            side="left"
        )

        ttk.Button(
            bar,
            text="Limpiar",
            command=lambda: self.mail.delete("1.0", "end")
        ).pack(
            side="left",
            padx=8
        )

        self.inc_out = tk.Text(
            frame,
            height=12,
            font=("Consolas", 10),
            bg="#FFFFFF",
            relief="flat"
        )

        self.inc_out.pack(
            fill="both",
            expand=True,
            padx=25,
            pady=20
        )

    def classify_incident(self):

        correo = self.mail.get(
            "1.0",
            "end"
        ).strip()

        if not correo:
            messagebox.showwarning(
                "Incidente",
                "Escribe primero el correo o incidente."
            )
            return

        try:

            resultado = hybrid_classify(
                correo,
                self.db,
                self.llm
            )

            self.inc_out.delete(
                "1.0",
                "end"
            )

            self.inc_out.insert(
                "end",
                json.dumps(
                    resultado,
                    ensure_ascii=False,
                    indent=2,
                    default=str
                )
            )

            self.refresh_dashboard()

        except Exception as e:

            self.inc_out.delete(
                "1.0",
                "end"
            )

            self.inc_out.insert(
                "end",
                f"Error: {e}"
            )

    # =========================================================
    # ASISTENTE
    # =========================================================

    def _assistant(self):

        frame = self._tab(
            "Asistente"
        )

        tk.Label(
            frame,
            text="Asistente LogiSmart",
            bg="#FFF8EC",
            fg="#075B66",
            font=("Segoe UI", 20, "bold")
        ).pack(
            anchor="w",
            padx=25,
            pady=(20, 3)
        )

        tk.Label(
            frame,
            text="Consulta información disponible en MongoDB.",
            bg="#FFF8EC",
            fg="#6B7C80",
            font=("Segoe UI", 10)
        ).pack(
            anchor="w",
            padx=25
        )

        self.chat = tk.Text(
            frame,
            bg="#FFFFFF",
            fg="#174A52",
            font=("Segoe UI", 10),
            relief="flat",
            padx=20,
            pady=20
        )

        self.chat.pack(
            fill="both",
            expand=True,
            padx=25,
            pady=15
        )

        bottom = tk.Frame(
            frame,
            bg="#FFF8EC"
        )

        bottom.pack(
            fill="x",
            padx=25,
            pady=(0, 20)
        )

        self.q = tk.Entry(
            bottom,
            font=("Segoe UI", 11),
            relief="flat"
        )

        self.q.pack(
            side="left",
            fill="x",
            expand=True,
            ipady=9
        )

        self.q.bind(
            "<Return>",
            lambda event: self.ask()
        )

        ttk.Button(
            bottom,
            text="Preguntar",
            command=self.ask
        ).pack(
            side="left",
            padx=(8, 0)
        )

        self.chat.insert(
            "end",
            "Asistente: Hola. ¿En qué puedo ayudarte?\n\n"
        )

    def ask(self):

        question = self.q.get().strip()

        self.q.delete(
            0,
            "end"
        )

        if not question:
            return

        self.chat.insert(
            "end",
            f"Tú: {question}\n"
        )

        self.chat.insert(
            "end",
            "Asistente: consultando MongoDB...\n"
        )

        self.update_idletasks()

        try:

            terms = question.upper().split()
            context = []

            for term in terms:

                if term.startswith("CAM") or term.startswith("TRK"):

                    context += self.db.find(
                        "accesos",
                        {"placa": term},
                        10
                    )

            if not context:

                palabras_acceso = [
                    "acceso",
                    "accesos",
                    "inspeccion",
                    "inspección",
                    "camion",
                    "camiones"
                ]

                if any(
                    palabra in question.lower()
                    for palabra in palabras_acceso
                ):

                    context = self.db.find(
                        "accesos",
                        {},
                        10
                    )

            answer = self.llm.explain(
                question,
                context
            )

            self.chat.insert(
                "end",
                f"Asistente: {answer}\n\n"
            )

        except Exception as e:

            self.chat.insert(
                "end",
                f"Asistente: Error: {e}\n\n"
            )

        self.chat.see("end")

    # =========================================================
    # RIESGOS
    # =========================================================

    def _risks(self):

        frame = self._tab(
            "Riesgos éticos"
        )

        tk.Label(
            frame,
            text="Riesgos éticos",
            bg="#FFF8EC",
            fg="#075B66",
            font=("Segoe UI", 20, "bold")
        ).pack(
            anchor="w",
            padx=25,
            pady=(20, 5)
        )

        tk.Label(
            frame,
            text="Supervisión de riesgos residuales del sistema.",
            bg="#FFF8EC",
            fg="#6B7C80",
            font=("Segoe UI", 10)
        ).pack(
            anchor="w",
            padx=25,
            pady=(0, 15)
        )

        self.risks = ttk.Treeview(
            frame,
            columns=[
                "id",
                "riesgo",
                "probabilidad",
                "impacto",
                "residual"
            ],
            show="headings"
        )

        headings = {
            "id": "ID",
            "riesgo": "Riesgo",
            "probabilidad": "Probabilidad",
            "impacto": "Impacto",
            "residual": "Riesgo residual"
        }

        for column in self.risks["columns"]:

            self.risks.heading(
                column,
                text=headings[column]
            )

            self.risks.column(
                column,
                width=150
            )

        self.risks.pack(
            fill="both",
            expand=True,
            padx=25,
            pady=(0, 20)
        )

        ttk.Button(
            frame,
            text="Actualizar riesgos",
            command=self.refresh_risks
        ).pack(
            anchor="w",
            padx=25,
            pady=(0, 20)
        )

        self.refresh_risks()

    def refresh_risks(self):

        if not hasattr(self, "risks"):
            return

        for item in self.risks.get_children():
            self.risks.delete(item)

        try:

            data = self.repo.list(
                "riesgos_eticos"
            )

            for index, item in enumerate(data, 1):

                self.risks.insert(
                    "",
                    "end",
                    values=[
                        item.get("_id", index),
                        item.get(
                            "riesgo",
                            item.get("descripcion", "")
                        ),
                        item.get(
                            "probabilidad",
                            ""
                        ),
                        item.get(
                            "impacto",
                            ""
                        ),
                        item.get(
                            "riesgo_residual",
                            item.get(
                                "puntaje_residual",
                                ""
                            )
                        )
                    ]
                )

        except Exception:
            pass

    # =========================================================
    # BASE DE DATOS / CRUD
    # =========================================================

    def _crud(self):

        frame = self._tab(
            "Base de datos"
        )

        tk.Label(
            frame,
            text="Base de datos",
            bg="#FFF8EC",
            fg="#075B66",
            font=("Segoe UI", 20, "bold")
        ).pack(
            anchor="w",
            padx=25,
            pady=(20, 15)
        )

        top = tk.Frame(
            frame,
            bg="#FFF8EC"
        )

        top.pack(
            fill="x",
            padx=25,
            pady=(0, 10)
        )

        self.collection = tk.StringVar(
            value="camiones"
        )

        ttk.Combobox(
            top,
            textvariable=self.collection,
            values=COLLECTIONS,
            state="readonly",
            width=25
        ).pack(
            side="left"
        )

        ttk.Button(
            top,
            text="Cargar",
            command=self.load_crud
        ).pack(
            side="left",
            padx=8
        )

        ttk.Button(
            top,
            text="Nuevo",
            command=self.new_doc
        ).pack(
            side="left"
        )

        self.crud = ttk.Treeview(
            frame,
            columns=("json",),
            show="headings"
        )

        self.crud.heading(
            "json",
            text="Documento"
        )

        self.crud.column(
            "json",
            width=900
        )

        self.crud.pack(
            fill="both",
            expand=True,
            padx=25,
            pady=(0, 20)
        )

        self.load_crud()

    def load_crud(self):

        for item in self.crud.get_children():
            self.crud.delete(item)

        try:

            docs = self.repo.list(
                self.collection.get()
            )

            for doc in docs:

                self.crud.insert(
                    "",
                    "end",
                    values=[
                        json.dumps(
                            doc,
                            ensure_ascii=False,
                            default=str
                        )
                    ]
                )

        except Exception as e:

            self.crud.insert(
                "",
                "end",
                values=[
                    f"Error: {e}"
                ]
            )

    def new_doc(self):

        messagebox.showinfo(
            "Base de datos",
            "Para crear un documento utiliza el formulario del proyecto."
        )

    # =========================================================
    # REPORTES
    # =========================================================

    def _reports(self):

        frame = self._tab(
            "Reportes"
        )

        tk.Label(
            frame,
            text="Reportes",
            bg="#FFF8EC",
            fg="#075B66",
            font=("Segoe UI", 20, "bold")
        ).pack(
            anchor="w",
            padx=25,
            pady=(20, 5)
        )

        tk.Label(
            frame,
            text="Genera reportes de la información almacenada.",
            bg="#FFF8EC",
            fg="#6B7C80",
            font=("Segoe UI", 10)
        ).pack(
            anchor="w",
            padx=25,
            pady=(0, 20)
        )

        box = tk.Frame(
            frame,
            bg="#FFFFFF"
        )

        box.pack(
            fill="x",
            padx=25,
            pady=10
        )

        ttk.Button(
            box,
            text="Exportar JSON",
            command=self.report_json
        ).pack(
            side="left",
            padx=10,
            pady=20
        )

        ttk.Button(
            box,
            text="Exportar CSV",
            command=self.report_csv
        ).pack(
            side="left",
            padx=10,
            pady=20
        )

        ttk.Button(
            box,
            text="Exportar PDF",
            command=self.report_pdf
        ).pack(
            side="left",
            padx=10,
            pady=20
        )

    def report_json(self):

        try:

            docs = self.repo.list(
                self.collection.get()
                if hasattr(self, "collection")
                else "camiones"
            )

            path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[
                    ("JSON", "*.json")
                ]
            )

            if path:
                export_json(
                    docs,
                    path
                )
                messagebox.showinfo(
                    "Reporte",
                    "Reporte JSON generado."
                )

        except Exception as e:

            messagebox.showerror(
                "Reporte",
                str(e)
            )

    def report_csv(self):

        try:

            docs = self.repo.list(
                self.collection.get()
                if hasattr(self, "collection")
                else "camiones"
            )

            path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[
                    ("CSV", "*.csv")
                ]
            )

            if path:
                export_csv(
                    docs,
                    path
                )
                messagebox.showinfo(
                    "Reporte",
                    "Reporte CSV generado."
                )

        except Exception as e:

            messagebox.showerror(
                "Reporte",
                str(e)
            )

    def report_pdf(self):

        try:

            docs = self.repo.list(
                self.collection.get()
                if hasattr(self, "collection")
                else "camiones"
            )

            path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[
                    ("PDF", "*.pdf")
                ]
            )

            if path:
                export_pdf(
                    docs,
                    path
                )
                messagebox.showinfo(
                    "Reporte",
                    "Reporte PDF generado."
                )

        except Exception as e:

            messagebox.showerror(
                "Reporte",
                str(e)
            )

    # =========================================================
    # CONFIGURACIÓN
    # =========================================================

    def _config(self):

        frame = self._tab(
            "Configuración"
        )

        tk.Label(
            frame,
            text="Configuración",
            bg="#FFF8EC",
            fg="#075B66",
            font=("Segoe UI", 20, "bold")
        ).pack(
            anchor="w",
            padx=25,
            pady=(20, 20)
        )

        datos = [
            ("MongoDB", settings.mongodb_uri),
            ("Base de datos", settings.database),
            ("Ollama", settings.ollama_host),
            ("Modelo", settings.ollama_model),
            ("Timeout", str(settings.llm_timeout)),
            ("Modo simulación", str(settings.simulation_mode))
        ]

        box = tk.Frame(
            frame,
            bg="#FFFFFF"
        )

        box.pack(
            fill="x",
            padx=25
        )

        for nombre, valor in datos:

            row = tk.Frame(
                box,
                bg="#FFFFFF"
            )

            row.pack(
                fill="x",
                padx=20,
                pady=10
            )

            tk.Label(
                row,
                text=nombre,
                bg="#FFFFFF",
                fg="#6B7C80",
                font=("Segoe UI", 10, "bold"),
                width=20,
                anchor="w"
            ).pack(
                side="left"
            )

            tk.Label(
                row,
                text=str(valor),
                bg="#FFFFFF",
                fg="#174A52",
                font=("Segoe UI", 10),
                anchor="w"
            ).pack(
                side="left"
            )

    # =========================================================
    # ACTUALIZACIÓN GENERAL
    # =========================================================

    def refresh_all(self):

        try:
            self.refresh_dashboard()
        except Exception:
            pass

        try:
            self.refresh_truth()
        except Exception:
            pass

        try:
            self.refresh_risks()
        except Exception:
            pass


if __name__ == "__main__":
    app = LogiSmartGUI()
    app.mainloop()