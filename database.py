# database.py
import sqlite3
class LabDB:
    def __init__(self, db_path="lab_db.sqlite"):
        self.db_path = db_path
        self.conn = None
        self.cur = None
        self.test_map = {}
    def connect(self):
        self.conn = sqlite3.connect(self.db_path)
        self.cur = self.conn.cursor()
        self.cur.execute("PRAGMA foreign_keys = ON")
        self.conn.commit()
    def init_db(self):
        # Crear tablas
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                role TEXT
            )
        """)
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_type TEXT,
                doc_number TEXT,
                first_name TEXT,
                last_name TEXT,
                birth_date TEXT,
                sex TEXT,
                origin TEXT,
                hcl TEXT,
                height REAL,
                weight REAL,
                blood_pressure TEXT,
                UNIQUE(doc_type, doc_number)
            )
        """)
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                category TEXT
            )
        """)
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER,
                date TEXT,
                created_by INTEGER,
                observations TEXT,
                requested_by TEXT,
                diagnosis TEXT,
                age_years INTEGER,
                completed INTEGER DEFAULT 0,
                FOREIGN KEY(patient_id) REFERENCES patients(id),
                FOREIGN KEY(created_by) REFERENCES users(id)
            )
        """)
        # Asegurarse de que columnas nuevas existan para bases de datos creadas anteriormente
        self._ensure_column_exists("orders", "diagnosis", "TEXT", default_value="")
        self._ensure_column_exists("orders", "age_years", "INTEGER")
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS order_tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                test_id INTEGER,
                result TEXT,
                FOREIGN KEY(order_id) REFERENCES orders(id),
                FOREIGN KEY(test_id) REFERENCES tests(id)
            )
        """)
        self.conn.commit()
        # Datos iniciales por defecto
        self.cur.execute("SELECT COUNT(*) FROM users")
        if self.cur.fetchone()[0] == 0:
            # Crear usuario admin por defecto
            self.cur.execute("INSERT INTO users(username, password, role) VALUES (?,?,?)",
                             ("admin", "admin", "super"))
            self.conn.commit()
        self.cur.execute("SELECT COUNT(*) FROM tests")
        if self.cur.fetchone()[0] == 0:
            tests_by_category = {
                "HEMATOLOGÍA": [
                    "Lámina periférica", "Hemograma manual", "Hemograma automatizado",
                    "Hemoglobina", "Hematocrito", "Recuento de leucocitos", "Recuento de hematíes",
                    "Recuento de plaquetas", "Constantes corpusculares", "Células LE",
                    "Tiempo de coagulación", "Tiempo de sangría", "Velocidad de sedimentación globular (VSG)"
                ],
                "BIOQUÍMICA": [
                    "Glucosa", "Glucosa postprandial", "Tolerancia a la glucosa",
                    "Colesterol Total", "Triglicéridos", "Colesterol HDL", "Colesterol LDL",
                    "Transaminasa Glutámico Oxalacética (TGO)", "Transaminasa Glutámico Pirúvico (TGP)",
                    "Bilirrubina Total", "Bilirrubina Directa", "Úrea", "Creatinina",
                    "Proteína de 24 horas", "Fosfatasa alcalina", "Ácido úrico",
                    "Proteínas Totales", "Albúmina", "Amilasa", "Lipasa",
                    "Gamma Glutamil transferasa (GGT)", "Globulina", "Ferritina",
                    "Hemoglobina glicosilada", "Gases arteriales"
                ],
                "INMUNOLOGÍA": [
                    "Grupo sanguíneo y Factor Rh", "Factor reumatoideo", "Reacción de Widal",
                    "Reagina plasmática rápida (RPR)", "Proteína C reactiva (PCR) - Látex",
                    "PCR cuantitativo", "ASO", "Antígeno de superficie Hepatitis B (HBsAg)",
                    "PSA (ELISA)"
                ],
                "PRUEBAS RÁPIDAS": [
                    "HCG (Prueba de embarazo en orina)", "VIH (Prueba rápida)", "Sífilis (Prueba rápida)",
                    "VIH/Sífilis (Prueba combinada)", "Hepatitis A (Prueba rápida)", "Hepatitis B (Prueba rápida)",
                    "PSA (Prueba rápida)", "Sangre oculta en heces (Prueba rápida)", "Helicobacter pylori (Prueba rápida)",
                    "Covid-19 (Prueba antigénica)", "Covid-19 (Prueba serológica)", "Dengue NS1/IgM/IgG (Prueba rápida)"
                ],
                "PARASITOLOGÍA": [
                    "Gota gruesa", "Frotis para Leishmaniasis", "Examen coprológico (concentración)",
                    "Examen coprológico (directo)", "Test de Graham"
                ],
                "MICROBIOLOGÍA": [
                    "Baciloscopía", "Coloración de Gram", "Examen directo (hongos/KOH)",
                    "Urocultivo", "Coprocultivo", "Cultivo de Neisseria gonorrhoeae",
                    "Cultivo de Campylobacter spp.", "Cultivo de otras secreciones",
                    "Identificación bioquímica", "Antibiograma", "Frotis para Bartonella"
                ],
                "MICROSCOPÍA": [
                    "Reacción inflamatoria", "Test de Helecho", "Examen completo de orina", "Sedimento urinario"
                ],
                "OTROS": [
                    "Ácido sulfasalicílico al 3%", "Test de aminas", "Contenido gástrico (en RN)"
                ],
                "TOMA DE MUESTRA": [
                    "Leishmaniasis (toma de muestra)", "Dengue (toma de muestra)", "Leptospirosis (toma de muestra)",
                    "Covid-19 (hisopado nasofaríngeo)", "Carga viral de VIH / Recuento de CD4",
                    "CLIA (PSA, Perfil tiroideo, etc.)", "Sangre venosa/arterial (examen de proceso)"
                ]
            }
            for cat, tests in tests_by_category.items():
                for test in tests:
                    self.cur.execute("INSERT INTO tests(name, category) VALUES (?,?)", (test, cat))
            self.conn.commit()
        # Cargar mapa de pruebas (nombre -> id)
        self.cur.execute("SELECT id, name FROM tests")
        for tid, name in self.cur.fetchall():
            self.test_map[name] = tid
    def authenticate_user(self, username, password):
        self.cur.execute("SELECT id, username, role FROM users WHERE username=? AND password=?", (username, password))
        row = self.cur.fetchone()
        if row:
            uid, user, role = row
            return {"id": uid, "username": user, "role": role}
        else:
            return None
    def create_user(self, username, password, role):
        try:
            self.cur.execute("INSERT INTO users(username, password, role) VALUES (?,?,?)", (username, password, role))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    def find_patient(self, doc_type, doc_number):
        self.cur.execute("SELECT * FROM patients WHERE doc_type=? AND doc_number=?", (doc_type, doc_number))
        return self.cur.fetchone()
    def add_or_update_patient(self, doc_type, doc_number, first_name, last_name, birth_date, sex, origin, hcl, height, weight, blood_pressure):
        existing = self.find_patient(doc_type, doc_number)
        if existing:
            pid = existing[0]
            self.cur.execute("""
                UPDATE patients SET first_name=?, last_name=?, birth_date=?, sex=?, origin=?, hcl=?, height=?, weight=?, blood_pressure=?
                WHERE id=?
            """, (first_name, last_name, birth_date, sex, origin, hcl, height, weight, blood_pressure, pid))
            self.conn.commit()
            return pid
        else:
            self.cur.execute("""
                INSERT INTO patients(doc_type, doc_number, first_name, last_name, birth_date, sex, origin, hcl, height, weight, blood_pressure)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """, (doc_type, doc_number, first_name, last_name, birth_date, sex, origin, hcl, height, weight, blood_pressure))
            self.conn.commit()
            return self.cur.lastrowid
    def add_order_with_tests(self, patient_id, test_names, user_id, observations="", requested_by="", diagnosis="", age_years=None):
        import datetime
        date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        age_value = None
        if age_years is not None:
            try:
                age_value = int(age_years)
            except (TypeError, ValueError):
                age_value = None
        self.cur.execute("""
            INSERT INTO orders(patient_id, date, created_by, observations, requested_by, diagnosis, age_years, completed)
            VALUES (?,?,?,?,?,?,?,?)
        """, (patient_id, date_str, user_id, observations, requested_by, diagnosis, age_value, 0))
        order_id = self.cur.lastrowid
        for name in test_names:
            if name in self.test_map:
                test_id = self.test_map[name]
                self.cur.execute("INSERT INTO order_tests(order_id, test_id, result) VALUES (?,?,?)",
                                 (order_id, test_id, ""))
        self.conn.commit()
        return order_id
    def get_pending_orders(self):
        self.cur.execute("""
            SELECT o.id, p.first_name, p.last_name, o.date
            FROM orders o
            JOIN patients p ON o.patient_id=p.id
            WHERE o.completed=0
            ORDER BY o.date DESC, o.id DESC
        """)
        return self.cur.fetchall()
    def get_completed_orders(self):
        self.cur.execute("""
            SELECT o.id, p.first_name, p.last_name, o.date
            FROM orders o
            JOIN patients p ON o.patient_id=p.id
            WHERE o.completed=1
            ORDER BY o.date DESC, o.id DESC
        """)
        return self.cur.fetchall()
    def get_order_details(self, order_id):
        self.cur.execute("""
            SELECT p.first_name, p.last_name, p.doc_type, p.doc_number, p.birth_date, p.sex, p.origin, p.hcl,
                   o.date, o.observations, o.requested_by, o.diagnosis, o.age_years,
                   t.name, ot.result
            FROM orders o
            JOIN patients p ON o.patient_id = p.id
            JOIN order_tests ot ON ot.order_id = o.id
            JOIN tests t ON ot.test_id = t.id
            WHERE o.id = ?
        """, (order_id,))
        rows = self.cur.fetchall()
        if not rows:
            return None
        first_name, last_name, doc_type, doc_number, birth_date, sex, origin, hcl, date, obs, req_by, diag, age_years, _, _ = rows[0]
        patient_info = {
            "name": f"{first_name} {last_name}",
            "doc_type": doc_type,
            "doc_number": doc_number,
            "birth_date": birth_date,
            "sex": sex,
            "origin": origin,
            "hcl": hcl
        }
        order_info = {"date": date, "observations": obs, "requested_by": req_by, "diagnosis": diag, "age_years": age_years}
        results = [(row[12], row[13]) for row in rows]
        return {"patient": patient_info, "order": order_info, "results": results}
    def save_results(self, order_id, results_dict):
        for name, result in results_dict.items():
            if name in self.test_map:
                tid = self.test_map[name]
                self.cur.execute("UPDATE order_tests SET result=? WHERE order_id=? AND test_id=?", (result, order_id, tid))
        # Verificar si quedan resultados vacíos
        self.cur.execute("SELECT COUNT(*) FROM order_tests WHERE order_id=? AND (result IS NULL OR result='')", (order_id,))
        remaining = self.cur.fetchone()[0]
        completed_flag = 1 if remaining == 0 else 0
        self.cur.execute("UPDATE orders SET completed=? WHERE id=?", (completed_flag, order_id))
        self.conn.commit()
        return completed_flag
    def get_statistics(self):
        stats = {}
        self.cur.execute("SELECT COUNT(*) FROM patients"); stats["total_patients"] = self.cur.fetchone()[0]
        self.cur.execute("SELECT COUNT(*) FROM orders"); stats["total_orders"] = self.cur.fetchone()[0]
        self.cur.execute("SELECT COUNT(*) FROM order_tests"); stats["total_tests_conducted"] = self.cur.fetchone()[0]
        self.cur.execute("""
            SELECT t.category, COUNT(*) FROM order_tests ot JOIN tests t ON ot.test_id = t.id GROUP BY t.category
        """)
        stats["by_category"] = self.cur.fetchall()
        return stats
    def get_distinct_requesters(self):
        self.cur.execute("SELECT DISTINCT requested_by FROM orders WHERE requested_by IS NOT NULL AND requested_by<>'' ORDER BY requested_by")
        return [row[0] for row in self.cur.fetchall() if row[0]]
    def _ensure_column_exists(self, table_name, column_name, column_type, default_value=None):
        self.cur.execute(f"PRAGMA table_info({table_name})")
        columns = [info[1] for info in self.cur.fetchall()]
        if column_name not in columns:
            alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
            if default_value is not None:
                alter_sql += f" DEFAULT '{default_value}'"
            self.cur.execute(alter_sql)
            self.conn.commit()
