# main_window.py
import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
                             QStackedWidget, QFormLayout, QScrollArea, QGroupBox, QComboBox,
                             QLineEdit, QTextEdit, QTableWidget, QTableWidgetItem, QFileDialog, QMessageBox, QCheckBox,
                             QDateEdit, QRadioButton, QButtonGroup)
from PyQt5.QtCore import QDate, QDateTime, Qt, QTimer
from fpdf import FPDF  # Asegúrese de tener fpdf instalado (pip install fpdf)

LAB_TITLE = "Laboratorio P.S. Iñapari - 002789"
class MainWindow(QMainWindow):
    def __init__(self, labdb, user):
        super().__init__()
        self.labdb = labdb
        self.user = user
        self.setWindowTitle(LAB_TITLE)
        # Configuración de ventana principal y menú lateral
        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        side_menu_layout = QVBoxLayout()
        side_menu_widget = QWidget()
        side_menu_widget.setLayout(side_menu_layout)
        side_menu_widget.setFixedWidth(200)
        side_menu_widget.setStyleSheet("background-color: #2c3e50;")
        title_label = QLabel(LAB_TITLE)
        title_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setWordWrap(True)
        side_menu_layout.addWidget(title_label)
        side_menu_layout.addSpacing(10)
        # Secciones/Páginas
        self.stack = QStackedWidget()
        # Contenedor principal con cabecera y reloj
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        header_layout = QHBoxLayout()
        header_title = QLabel(LAB_TITLE)
        header_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        header_title.setWordWrap(True)
        self.clock_label = QLabel()
        self.clock_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.clock_label.setStyleSheet("font-size: 16px; color: #0a84ff;")
        header_layout.addWidget(header_title)
        header_layout.addStretch()
        header_layout.addWidget(self.clock_label)
        content_layout.addLayout(header_layout)
        content_layout.addWidget(self.stack)
        # 1. Página de Registro de Pacientes
        self.page_registro = QWidget(); self.init_registro_page()
        self.stack.addWidget(self.page_registro)
        btn_reg = QPushButton("Registro"); btn_reg.setStyleSheet("background-color: #4CAF50; color: white; font-size: 14px;")
        btn_reg.clicked.connect(lambda: self.stack.setCurrentWidget(self.page_registro))
        side_menu_layout.addWidget(btn_reg)
        # 2. Página de Ingreso de Resultados
        self.page_resultados = QWidget(); self.init_resultados_page()
        self.stack.addWidget(self.page_resultados)
        btn_res = QPushButton("Anotar Resultados"); btn_res.setStyleSheet("background-color: #4CAF50; color: white; font-size: 14px;")
        btn_res.clicked.connect(lambda: self.stack.setCurrentWidget(self.page_resultados))
        side_menu_layout.addWidget(btn_res)
        # 3. Página de Emisión de Resultados
        self.page_emitir = QWidget(); self.init_emitir_page()
        self.stack.addWidget(self.page_emitir)
        btn_emit = QPushButton("Emitir Resultados"); btn_emit.setStyleSheet("background-color: #4CAF50; color: white; font-size: 14px;")
        btn_emit.clicked.connect(lambda: self.stack.setCurrentWidget(self.page_emitir))
        side_menu_layout.addWidget(btn_emit)
        # 4. Página de Análisis de Datos
        self.page_analisis = QWidget(); self.init_analisis_page()
        self.stack.addWidget(self.page_analisis)
        btn_an = QPushButton("Análisis de Datos"); btn_an.setStyleSheet("background-color: #4CAF50; color: white; font-size: 14px;")
        btn_an.clicked.connect(lambda: self.stack.setCurrentWidget(self.page_analisis))
        side_menu_layout.addWidget(btn_an)
        # 5. Página de Configuración (solo visible para superusuario)
        if self.user['role'] == 'super':
            self.page_config = QWidget(); self.init_config_page()
            self.stack.addWidget(self.page_config)
            btn_conf = QPushButton("Configuración"); btn_conf.setStyleSheet("background-color: #4CAF50; color: white; font-size: 14px;")
            btn_conf.clicked.connect(lambda: self.stack.setCurrentWidget(self.page_config))
            side_menu_layout.addWidget(btn_conf)
        side_menu_layout.addStretch()
        main_layout.addWidget(side_menu_widget)
        main_layout.addWidget(content_widget)
        self.setCentralWidget(central_widget)
        self.stack.setCurrentWidget(self.page_registro)  # Mostrar la sección de registro al inicio
        # Actualizar datos dinámicos al cambiar de página
        self.stack.currentChanged.connect(self.on_page_changed)
        # Variables auxiliares
        self.order_fields = {}        # Campos de resultado dinámicos (nombre_prueba -> QLineEdit)
        self.selected_order_id = None # Orden seleccionada actualmente en resultados
        self.last_order_registered = None  # Última orden registrada (para enlace rápido a resultados)
        # Reloj en tiempo real para la ventana principal
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start(1000)
        self._update_clock()
    def on_page_changed(self, index):
        current_widget = self.stack.widget(index)
        if current_widget == self.page_resultados:
            self.populate_pending_orders()
        elif current_widget == self.page_emitir:
            self.populate_completed_orders()
        elif current_widget == self.page_analisis:
            self.refresh_statistics()
    def _update_clock(self):
        self.clock_label.setText(QDateTime.currentDateTime().toString("dd/MM/yyyy HH:mm:ss"))
    def init_registro_page(self):
        layout = QVBoxLayout(self.page_registro)
        top_layout = QHBoxLayout()
        # Formulario de datos del paciente
        form_layout = QFormLayout()
        self.input_doc_type = QComboBox(); self.input_doc_type.addItems(["DNI", "Carnet Ext.", "Pasaporte"])
        self.input_doc_number = QLineEdit()
        btn_search = QPushButton("Buscar"); btn_search.setFixedWidth(60)
        btn_search.clicked.connect(self.autofill_patient)
        doc_hlayout = QHBoxLayout()
        doc_hlayout.addWidget(self.input_doc_type); doc_hlayout.addWidget(self.input_doc_number); doc_hlayout.addWidget(btn_search)
        form_layout.addRow("Documento:", doc_hlayout)
        self.input_first_name = QLineEdit(); form_layout.addRow("Nombre:", self.input_first_name)
        self.input_last_name = QLineEdit(); form_layout.addRow("Apellidos:", self.input_last_name)
        # Fecha de nacimiento y edad calculada automáticamente (editable)
        self.input_birth_date = QDateEdit()
        self.input_birth_date.setDisplayFormat("dd-MM-yyyy")
        self.input_birth_date.setCalendarPopup(True)
        self.input_birth_date.setDate(QDate.currentDate())
        self.input_birth_date.dateChanged.connect(self.update_age_from_birth_date)
        form_layout.addRow("F. Nacimiento:", self.input_birth_date)
        self.input_age = QLineEdit()
        self.input_age.setPlaceholderText("Edad estimada")
        form_layout.addRow("Edad:", self.input_age)
        # Sexo como botones exclusivos
        self.sex_male_radio = QRadioButton("Masculino")
        self.sex_female_radio = QRadioButton("Femenino")
        self.sex_group = QButtonGroup(self.page_registro)
        self.sex_group.addButton(self.sex_male_radio)
        self.sex_group.addButton(self.sex_female_radio)
        self.sex_male_radio.setChecked(True)
        sex_layout = QHBoxLayout()
        sex_layout.addWidget(self.sex_male_radio)
        sex_layout.addWidget(self.sex_female_radio)
        sex_layout.addStretch()
        form_layout.addRow("Sexo:", sex_layout)
        # Procedencia con opción rápida P.S Iñapari u otros
        self.origin_combo = QComboBox()
        self.origin_combo.addItems(["P.S Iñapari", "Otros"])
        self.origin_combo.currentIndexChanged.connect(self.on_origin_changed)
        self.input_origin_other = QLineEdit()
        self.input_origin_other.setPlaceholderText("Especifique procedencia")
        self.input_origin_other.setEnabled(False)
        origin_layout = QHBoxLayout()
        origin_layout.addWidget(self.origin_combo)
        origin_layout.addWidget(self.input_origin_other)
        form_layout.addRow("Procedencia:", origin_layout)
        self.input_hcl = QLineEdit(); form_layout.addRow("HCL:", self.input_hcl)
        self.input_height = QLineEdit(); self.input_height.setPlaceholderText("cm")
        form_layout.addRow("Talla (cm):", self.input_height)
        self.input_weight = QLineEdit(); self.input_weight.setPlaceholderText("kg")
        form_layout.addRow("Peso (kg):", self.input_weight)
        self.input_blood_pressure = QLineEdit(); self.input_blood_pressure.setPlaceholderText("ej. 120/80")
        form_layout.addRow("Presión Art.:", self.input_blood_pressure)
        self.input_diagnosis = QLineEdit(); self.input_diagnosis.setPlaceholderText("Ej. Síndrome febril")
        form_layout.addRow("Diagnóstico presuntivo:", self.input_diagnosis)
        self.input_observations = QLineEdit()
        self.input_observations.setPlaceholderText("Observaciones (laboratorio)")
        self.input_observations.setText("N/A")
        obs_layout = QHBoxLayout()
        obs_layout.addWidget(self.input_observations)
        btn_obs_na = QPushButton("Sin obs.")
        btn_obs_na.setFixedWidth(90)
        btn_obs_na.clicked.connect(lambda: self.input_observations.setText("N/A"))
        obs_layout.addWidget(btn_obs_na)
        form_layout.addRow("Observaciones:", obs_layout)
        self.input_requested_by = QComboBox()
        self.input_requested_by.setEditable(True)
        self.input_requested_by.setInsertPolicy(QComboBox.NoInsert)
        self.input_requested_by.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        form_layout.addRow("Solicitante:", self.input_requested_by)
        # Placeholder después de crear el combo editable
        if self.input_requested_by.lineEdit():
            self.input_requested_by.lineEdit().setPlaceholderText("Seleccione o escriba el médico solicitante")
        self.populate_requesters()
        top_layout.addLayout(form_layout)
        # Listado de pruebas por categoría (con scroll)
        tests_scroll = QScrollArea(); tests_scroll.setWidgetResizable(True)
        tests_container = QWidget(); tests_layout = QVBoxLayout(tests_container)
        # Obtener pruebas agrupadas por categoría de la BD
        categories = {}
        self.labdb.cur.execute("SELECT category, name FROM tests")
        for cat, name in self.labdb.cur.fetchall():
            categories.setdefault(cat, []).append(name)
        for cat, tests in categories.items():
            group_box = QGroupBox(cat)
            group_layout = QVBoxLayout()
            for test_name in tests:
                cb = QCheckBox(test_name)
                group_layout.addWidget(cb)
            group_box.setLayout(group_layout)
            tests_layout.addWidget(group_box)
        tests_layout.addStretch()
        tests_scroll.setWidget(tests_container)
        top_layout.addWidget(tests_scroll)
        layout.addLayout(top_layout)
        # Botones de acción
        btn_register = QPushButton("Registrar paciente y pruebas")
        btn_new = QPushButton("Registrar nuevo paciente")
        btn_to_results = QPushButton("Anotar resultado de este paciente")
        btn_to_results.setEnabled(False)
        btn_register.clicked.connect(lambda: self.register_patient(btn_to_results))
        btn_new.clicked.connect(self.clear_registration_form)
        btn_to_results.clicked.connect(self.go_to_results)
        btns_layout = QHBoxLayout()
        btns_layout.addWidget(btn_register); btns_layout.addWidget(btn_new); btns_layout.addWidget(btn_to_results)
        layout.addLayout(btns_layout)
    def populate_requesters(self, keep_current=False):
        current_text = self.input_requested_by.currentText().strip() if keep_current else ""
        items_lower = set()
        self.input_requested_by.blockSignals(True)
        self.input_requested_by.clear()
        self.input_requested_by.addItem("N/A")
        for requester in self.labdb.get_distinct_requesters():
            clean = requester.strip()
            if clean and clean.lower() not in ("n/a", "na"):
                self.input_requested_by.addItem(clean)
                items_lower.add(clean.lower())
        self.input_requested_by.blockSignals(False)
        if keep_current and current_text:
            idx = self.input_requested_by.findText(current_text)
            if idx == -1 and current_text.lower() not in items_lower:
                self.input_requested_by.addItem(current_text)
                idx = self.input_requested_by.count() - 1
            if idx >= 0:
                self.input_requested_by.setCurrentIndex(idx)
        else:
            self.input_requested_by.setCurrentIndex(0)
        if self.input_requested_by.lineEdit():
            if self.input_requested_by.currentIndex() <= 0:
                self.input_requested_by.lineEdit().clear()
            else:
                self.input_requested_by.lineEdit().setText(self.input_requested_by.currentText())
            self.input_requested_by.lineEdit().setPlaceholderText("Seleccione o escriba el médico solicitante")
    def update_age_from_birth_date(self, qdate=None):
        if qdate is None:
            qdate = self.input_birth_date.date()
        if isinstance(qdate, QDate) and qdate.isValid():
            years = max(0, qdate.daysTo(QDate.currentDate()) // 365)
            self.input_age.setText(str(years))
        else:
            self.input_age.clear()
    def on_origin_changed(self, index):
        use_other = self.origin_combo.currentText() == "Otros"
        self.input_origin_other.setEnabled(use_other)
        if not use_other:
            self.input_origin_other.clear()
    def get_current_origin(self):
        if self.origin_combo.currentText() == "Otros":
            other = self.input_origin_other.text().strip()
            return other if other else "Otros"
        return "P.S Iñapari"
    def set_origin_value(self, value):
        if value and value.strip().lower() not in ("p.s iñapari", "ps iñapari", "p.s. iñapari"):
            self.origin_combo.setCurrentIndex(1)
            self.input_origin_other.setEnabled(True)
            self.input_origin_other.setText(value)
        else:
            self.origin_combo.setCurrentIndex(0)
            self.input_origin_other.setEnabled(False)
            self.input_origin_other.clear()
    def _format_number(self, value):
        if value in (None, ""):
            return ""
        if isinstance(value, float):
            if value.is_integer():
                return str(int(value))
            return f"{value:.2f}".rstrip('0').rstrip('.')
        return str(value)
    def autofill_patient(self):
        doc_type = self.input_doc_type.currentText()
        doc_number = self.input_doc_number.text().strip()
        if doc_number == "":
            return
        patient = self.labdb.find_patient(doc_type, doc_number)
        if patient:
            # Rellenar campos con datos existentes
            _, _, _, first_name, last_name, birth_date, sex, origin, hcl, height, weight, blood_pressure = patient
            self.input_first_name.setText(first_name); self.input_last_name.setText(last_name)
            if birth_date:
                bd = QDate.fromString(birth_date, "yyyy-MM-dd")
                if bd.isValid():
                    self.input_birth_date.setDate(bd)
                else:
                    self.input_birth_date.setDate(QDate.currentDate())
                    self.input_age.clear()
            else:
                self.input_birth_date.setDate(QDate.currentDate())
                self.input_age.clear()
            if sex == "Femenino":
                self.sex_female_radio.setChecked(True)
            else:
                self.sex_male_radio.setChecked(True)
            self.set_origin_value(origin or "")
            self.input_hcl.setText(hcl or "")
            self.input_height.setText(self._format_number(height))
            self.input_weight.setText(self._format_number(weight))
            self.input_blood_pressure.setText(blood_pressure or "")
            QMessageBox.information(self, "Paciente encontrado", "Datos del paciente cargados.")
    def register_patient(self, btn_to_results):
        doc_type = self.input_doc_type.currentText()
        doc_number = self.input_doc_number.text().strip()
        if doc_number == "" or self.input_first_name.text().strip() == "" or self.input_last_name.text().strip() == "":
            QMessageBox.warning(self, "Datos incompletos", "Ingrese al menos Documento, Nombre y Apellidos.")
            return
        # Validar formato de documento
        if doc_type == "DNI":
            if len(doc_number) != 8 or not doc_number.isdigit():
                QMessageBox.warning(self, "Documento inválido", "El DNI debe tener 8 dígitos.")
                return
        else:
            if len(doc_number) > 20:
                QMessageBox.warning(self, "Documento inválido", f"El {doc_type} no debe exceder 20 caracteres.")
                return
        # Obtener datos del formulario
        first_name = self.input_first_name.text().strip()
        last_name = self.input_last_name.text().strip()
        birth_date = self.input_birth_date.date().toString("yyyy-MM-dd")
        sex = "Femenino" if self.sex_female_radio.isChecked() else "Masculino"
        origin = self.get_current_origin()
        if self.origin_combo.currentText() == "Otros" and (not self.input_origin_other.text().strip()):
            QMessageBox.warning(self, "Procedencia requerida", "Indique la procedencia del paciente cuando seleccione 'Otros'.")
            return
        hcl = self.input_hcl.text().strip()
        height = self.input_height.text().strip()
        weight = self.input_weight.text().strip()
        bp = self.input_blood_pressure.text().strip()
        diagnosis = self.input_diagnosis.text().strip()
        observations = self.input_observations.text().strip() or "N/A"
        requested_by_text = self.input_requested_by.currentText().strip() if self.input_requested_by.count() else ""
        if requested_by_text == "":
            requested_by_text = "N/A"
        if diagnosis == "":
            diagnosis = "N/A"
        age_text = self.input_age.text().strip()
        if age_text:
            try:
                age_years = int(age_text)
            except ValueError:
                QMessageBox.warning(self, "Edad inválida", "Ingrese la edad en años utilizando solo números enteros.")
                return
        else:
            age_years = None
        try:
            height_val = float(height) if height else None
        except:
            height_val = None
        try:
            weight_val = float(weight) if weight else None
        except:
            weight_val = None
        # Insertar o actualizar paciente en BD
        patient_id = self.labdb.add_or_update_patient(doc_type, doc_number, first_name, last_name, birth_date, sex, origin, hcl, height_val, weight_val, bp)
        # Obtener lista de pruebas seleccionadas
        selected_tests = []
        for cb in self.page_registro.findChildren(QCheckBox):
            if cb.isChecked():
                selected_tests.append(cb.text())
        if not selected_tests:
            QMessageBox.warning(self, "Sin pruebas", "Seleccione al menos una prueba.")
            return
        # Crear orden en BD con las pruebas seleccionadas
        order_id = self.labdb.add_order_with_tests(
            patient_id,
            selected_tests,
            self.user['id'],
            observations=observations,
            requested_by=requested_by_text,
            diagnosis=diagnosis,
            age_years=age_years
        )
        QMessageBox.information(self, "Registro exitoso", f"Paciente y pruebas registrados (Orden #{order_id}).")
        # Habilitar botón para ir a anotar resultados de esta orden
        btn_to_results.setEnabled(True)
        self.last_order_registered = order_id
        # Actualizar historial de solicitantes para próximas atenciones
        self.populate_requesters(keep_current=True)
    def clear_registration_form(self):
        # Limpiar todos los campos del formulario de registro
        self.input_doc_number.clear(); self.input_first_name.clear(); self.input_last_name.clear()
        self.input_birth_date.blockSignals(True)
        self.input_birth_date.setDate(QDate.currentDate())
        self.input_birth_date.blockSignals(False)
        self.input_age.clear()
        self.sex_male_radio.setChecked(True)
        self.set_origin_value("P.S Iñapari")
        self.input_hcl.clear()
        self.input_height.clear(); self.input_weight.clear(); self.input_blood_pressure.clear()
        self.input_diagnosis.clear()
        self.input_observations.setText("N/A")
        if self.input_requested_by.count():
            self.input_requested_by.setCurrentIndex(0)
        if self.input_requested_by.lineEdit():
            self.input_requested_by.lineEdit().clear()
        for cb in self.page_registro.findChildren(QCheckBox):
            cb.setChecked(False)
    def go_to_results(self):
        # Navegar a la página de resultados para la última orden registrada
        if self.last_order_registered:
            self.stack.setCurrentWidget(self.page_resultados)
            self.populate_pending_orders()
            # Seleccionar automáticamente la orden recién creada en el combo
            for i in range(self.combo_orders.count()):
                if self.combo_orders.itemData(i) == self.last_order_registered:
                    self.combo_orders.setCurrentIndex(i); break
            self.load_order_fields()
    def init_resultados_page(self):
        layout = QVBoxLayout(self.page_resultados)
        top_layout = QHBoxLayout()
        lbl = QLabel("Orden pendiente:")
        self.combo_orders = QComboBox()
        btn_load = QPushButton("Cargar")
        top_layout.addWidget(lbl); top_layout.addWidget(self.combo_orders); top_layout.addWidget(btn_load)
        layout.addLayout(top_layout)
        # Área scrollable para campos de resultados
        self.results_area = QScrollArea(); self.results_area.setWidgetResizable(True)
        self.results_container = QWidget(); self.results_layout = QFormLayout(self.results_container)
        self.results_area.setWidget(self.results_container)
        layout.addWidget(self.results_area)
        btn_save = QPushButton("Guardar Resultados")
        layout.addWidget(btn_save)
        btn_load.clicked.connect(self.load_order_fields)
        btn_save.clicked.connect(self.save_results)
    def populate_pending_orders(self):
        # Llenar combo de órdenes pendientes (no completadas)
        self.combo_orders.clear()
        pending = self.labdb.get_pending_orders()
        for (oid, first, last, date) in pending:
            self.combo_orders.addItem(f"{first} {last} - {date}", oid)
        if not pending:
            self.combo_orders.addItem("(No hay órdenes pendientes)", None)
    def load_order_fields(self):
        # Cargar campos de resultado para la orden seleccionada
        while self.results_layout.rowCount():
            self.results_layout.removeRow(0)  # eliminar filas anteriores
        self.order_fields.clear()
        data = self.combo_orders.currentData()
        if data is None:
            return
        order_id = int(data); self.selected_order_id = order_id
        # Consultar pruebas de esa orden
        self.labdb.cur.execute("""
            SELECT t.name, ot.result FROM order_tests ot JOIN tests t ON ot.test_id = t.id WHERE ot.order_id=?
        """, (order_id,))
        for name, result in self.labdb.cur.fetchall():
            lbl = QLabel(name + ":"); edit = QLineEdit()
            edit.setText(result if result else "")
            self.results_layout.addRow(lbl, edit)
            self.order_fields[name] = edit
    def save_results(self):
        # Guardar los resultados ingresados para la orden seleccionada
        if not self.selected_order_id:
            return
        results_dict = {name: edit.text().strip() for name, edit in self.order_fields.items()}
        # Si hay campos vacíos, confirmar si desea guardar incompleto
        if any(val == "" for val in results_dict.values()):
            reply = QMessageBox.question(self, "Confirmar", "Hay pruebas sin resultado. ¿Guardar de todos modos?", QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.No:
                return
        completed = self.labdb.save_results(self.selected_order_id, results_dict)
        if completed:
            QMessageBox.information(self, "Completado", "Resultados guardados. Orden marcada como completada.")
            # Actualizar lista de pendientes (esta orden se removerá)
            self.populate_pending_orders()
        else:
            QMessageBox.information(self, "Guardado", "Resultados guardados (orden aún incompleta).")
    def init_emitir_page(self):
        layout = QVBoxLayout(self.page_emitir)
        top_layout = QHBoxLayout()
        lbl = QLabel("Orden completada:")
        self.combo_completed = QComboBox()
        btn_view = QPushButton("Ver")
        top_layout.addWidget(lbl); top_layout.addWidget(self.combo_completed); top_layout.addWidget(btn_view)
        layout.addLayout(top_layout)
        self.output_text = QTextEdit(); self.output_text.setReadOnly(True)
        layout.addWidget(self.output_text)
        btn_pdf = QPushButton("Exportar a PDF"); btn_excel = QPushButton("Exportar a Excel")
        btns_layout = QHBoxLayout(); btns_layout.addWidget(btn_pdf); btns_layout.addWidget(btn_excel)
        layout.addLayout(btns_layout)
        btn_view.clicked.connect(self.display_selected_result)
        btn_pdf.clicked.connect(self.export_pdf)
        btn_excel.clicked.connect(self.export_excel)
    def populate_completed_orders(self):
        # Llenar combo de órdenes completadas
        self.combo_completed.clear()
        completed = self.labdb.get_completed_orders()
        for (oid, first, last, date) in completed:
            self.combo_completed.addItem(f"{first} {last} - {date}", oid)
        if not completed:
            self.combo_completed.addItem("(No hay resultados)", None)
    def display_selected_result(self):
        # Mostrar los resultados de la orden seleccionada en el cuadro de texto
        data = self.combo_completed.currentData()
        if data is None:
            return
        order_id = int(data)
        info = self.labdb.get_order_details(order_id)
        if not info:
            return
        pat = info["patient"]; ord_inf = info["order"]; results = info["results"]
        text = (f"Paciente: {pat['name']} (Doc: {pat['doc_type']} {pat['doc_number']})\n")
        age_value = ord_inf.get('age_years')
        if age_value is None and pat['birth_date']:
            bd = QDate.fromString(pat['birth_date'], "yyyy-MM-dd")
            if bd.isValid():
                age_value = bd.daysTo(QDate.currentDate()) // 365
        if age_value is not None:
            text += f"Edad: {age_value} años\n"
        text += (f"Sexo: {pat['sex']}\nProcedencia: {pat['origin']}\nHCL: {pat['hcl']}\n"
                 f"Fecha: {ord_inf['date']}\nSolicitante: {ord_inf['requested_by']}\n")
        if ord_inf.get("diagnosis") and ord_inf["diagnosis"].strip():
            text += f"Diagnóstico presuntivo: {ord_inf['diagnosis']}\n"
        text += "Resultados:\n"
        for test_name, result in results:
            text += f"  - {test_name}: {result}\n"
        if ord_inf["observations"]:
            text += f"Observaciones: {ord_inf['observations']}\n"
        self.output_text.setPlainText(text)
    def export_pdf(self):
        # Exportar el resultado seleccionado a un archivo PDF
        data = self.combo_completed.currentData()
        if data is None:
            return
        order_id = int(data)
        info = self.labdb.get_order_details(order_id)
        if not info:
            return
        # Seleccionar ruta de guardado
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "Guardar PDF", "", "Archivos PDF (*.pdf)", options=options)
        if not file_path:
            return
        if not file_path.lower().endswith(".pdf"):
            file_path += ".pdf"
        pat = info["patient"]; ord_inf = info["order"]; results = info["results"]
        pdf = FPDF()
        pdf.set_auto_page_break(True, margin=15)
        pdf.add_page()
        # Encabezado con logotipos opcionales
        try:
            if os.path.exists("logo_left.png"):
                pdf.image("logo_left.png", x=10, y=8, w=25)
            elif os.path.exists("logo.png"):
                pdf.image("logo.png", x=10, y=8, w=25)
            if os.path.exists("logo_right.png"):
                pdf.image("logo_right.png", x=pdf.w - 35, y=8, w=25)
        except Exception:
            pass
        pdf.set_font("Arial", 'B', 15)
        pdf.cell(0, 10, LAB_TITLE, ln=1, align='C')
        pdf.set_font("Arial", '', 11)
        pdf.cell(0, 6, "Informe de resultados de laboratorio", ln=1, align='C')
        pdf.ln(4)
        pdf.set_draw_color(10, 132, 255)
        pdf.set_line_width(0.4)
        current_y = pdf.get_y()
        pdf.line(10, current_y, pdf.w - 10, current_y)
        pdf.ln(4)
        # Datos del paciente
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(0, 6, "Datos del paciente", ln=1)
        pdf.set_font("Arial", '', 10)
        pdf.cell(95, 6, f"Paciente: {pat['name']}", ln=0)
        pdf.cell(0, 6, f"Documento: {pat['doc_type']} {pat['doc_number']}", ln=1)
        age_value = ord_inf.get('age_years')
        if age_value is None and pat['birth_date']:
            bd = QDate.fromString(pat['birth_date'], "yyyy-MM-dd")
            if bd.isValid():
                age_value = bd.daysTo(QDate.currentDate()) // 365
        age_text = f"{age_value} años" if age_value is not None else "-"
        pdf.cell(95, 6, f"Edad: {age_text}", ln=0)
        pdf.cell(0, 6, f"Sexo: {pat['sex']}", ln=1)
        pdf.cell(95, 6, f"Procedencia: {pat['origin']}", ln=0)
        pdf.cell(0, 6, f"HCL: {pat['hcl']}", ln=1)
        pdf.cell(95, 6, f"Fecha y hora: {ord_inf['date']}", ln=0)
        pdf.cell(0, 6, f"Solicitante: {ord_inf['requested_by']}", ln=1)
        if ord_inf.get('diagnosis') and ord_inf['diagnosis'].strip():
            pdf.multi_cell(0, 6, f"Diagnóstico presuntivo: {ord_inf['diagnosis']}")
        pdf.ln(2)
        # Resultados
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(0, 6, "Resultados", ln=1)
        pdf.set_font("Arial", '', 10)
        for test_name, result in results:
            pdf.multi_cell(0, 6, f"{test_name}: {result}", border=0)
        if ord_inf['observations']:
            pdf.ln(2)
            pdf.set_font("Arial", 'I', 9)
            pdf.multi_cell(0, 6, f"Observaciones: {ord_inf['observations']}")
        pdf.ln(4)
        pdf.set_font("Arial", 'I', 8)
        pdf.multi_cell(0, 5, "Este documento es generado automáticamente por el sistema del laboratorio."
                                 " Para validar la autenticidad, confirme con el laboratorio responsable.")
        try:
            pdf.output(file_path)
            QMessageBox.information(self, "PDF guardado", f"Reporte guardado en:\n{file_path}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo guardar el PDF:\n{e}")
    def export_excel(self):
        # Exportar todos los resultados a un archivo CSV (Excel puede abrirlo)
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "Exportar datos", "", "Archivo CSV (*.csv)", options=options)
        if not file_path:
            return
        if not file_path.lower().endswith(".csv"):
            file_path += ".csv"
        self.labdb.cur.execute("""
            SELECT p.first_name, p.last_name, p.doc_type, p.doc_number, t.name, ot.result, o.date, o.requested_by, o.diagnosis, o.age_years
            FROM order_tests ot
            JOIN orders o ON ot.order_id = o.id
            JOIN patients p ON o.patient_id = p.id
            JOIN tests t ON ot.test_id = t.id
        """)
        rows = self.labdb.cur.fetchall()
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("Nombre,Apellidos,Documento,Prueba,Resultado,Fecha,Solicitante,Diagnostico presuntivo,Edad (años)\n")
                for first, last, doc_type, doc_num, test_name, result, date, requester, diagnosis, age_years in rows:
                    name = first; surn = last; doc = f"{doc_type} {doc_num}"
                    res = result; dt = date
                    req = requester or ""
                    diag = diagnosis or ""
                    age_txt = str(age_years) if age_years is not None else ""
                    line = f"{name},{surn},{doc},{test_name},{res},{dt},{req},{diag},{age_txt}\n"
                    f.write(line)
            QMessageBox.information(self, "Exportado", f"Datos exportados a:\n{file_path}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo exportar:\n{e}")
    def init_analisis_page(self):
        layout = QVBoxLayout(self.page_analisis)
        self.stats_label = QLabel()
        layout.addWidget(self.stats_label)
        self.stats_table = QTableWidget(0, 2)
        self.stats_table.setHorizontalHeaderLabels(["Categoría", "Cantidad"])
        layout.addWidget(self.stats_table)
    def refresh_statistics(self):
        stats = self.labdb.get_statistics()
        text = (f"Pacientes registrados: {stats['total_patients']}\n"
                f"Órdenes realizadas: {stats['total_orders']}\n"
                f"Pruebas realizadas: {stats['total_tests_conducted']}")
        self.stats_label.setText(text)
        # Llenar tabla de categorías
        self.stats_table.setRowCount(0)
        for (cat, count) in stats['by_category']:
            row = self.stats_table.rowCount()
            self.stats_table.insertRow(row)
            self.stats_table.setItem(row, 0, QTableWidgetItem(cat))
            self.stats_table.setItem(row, 1, QTableWidgetItem(str(count)))
    def init_config_page(self):
        layout = QVBoxLayout(self.page_config)
        info_label = QLabel("Crear nuevo usuario:")
        layout.addWidget(info_label)
        form_layout = QFormLayout()
        self.new_user_input = QLineEdit(); form_layout.addRow("Usuario:", self.new_user_input)
        self.new_pass_input = QLineEdit(); self.new_pass_input.setEchoMode(QLineEdit.Password)
        form_layout.addRow("Contraseña:", self.new_pass_input)
        self.role_input = QComboBox(); self.role_input.addItems(["Administrador", "Superusuario"])
        form_layout.addRow("Rol:", self.role_input)
        layout.addLayout(form_layout)
        btn_create = QPushButton("Crear Usuario")
        layout.addWidget(btn_create)
        btn_create.clicked.connect(self.create_user)
    def create_user(self):
        username = self.new_user_input.text().strip()
        password = self.new_pass_input.text().strip()
        role_text = self.role_input.currentText()
        role = "admin" if role_text == "Administrador" else "super"
        if username == "" or password == "":
            QMessageBox.warning(self, "Campos vacíos", "Ingrese nombre de usuario y contraseña.")
            return
        success = self.labdb.create_user(username, password, role)
        if success:
            QMessageBox.information(self, "Usuario creado", f"Usuario '{username}' creado exitosamente.")
            self.new_user_input.clear(); self.new_pass_input.clear()
        else:
            QMessageBox.warning(self, "Error", "No se pudo crear el usuario. ¿Nombre ya existe?")
