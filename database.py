# database.py
import json
import sqlite3
from collections import OrderedDict
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
        self._ensure_column_exists("users", "full_name", "TEXT")
        self._ensure_column_exists("users", "profession", "TEXT")
        self._ensure_column_exists("users", "license", "TEXT")
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
                is_pregnant INTEGER DEFAULT 0,
                gestational_age_weeks INTEGER,
                expected_delivery_date TEXT,
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
                sample_date TEXT,
                created_by INTEGER,
                observations TEXT,
                requested_by TEXT,
                diagnosis TEXT,
                insurance_type TEXT DEFAULT 'SIS',
                fua_number TEXT,
                age_years INTEGER,
                completed INTEGER DEFAULT 0,
                FOREIGN KEY(patient_id) REFERENCES patients(id),
                FOREIGN KEY(created_by) REFERENCES users(id)
            )
        """)
        # Asegurarse de que columnas nuevas existan para bases de datos creadas anteriormente
        self._ensure_column_exists("orders", "diagnosis", "TEXT", default_value="")
        self._ensure_column_exists("orders", "insurance_type", "TEXT", default_value="SIS")
        self._ensure_column_exists("orders", "fua_number", "TEXT")
        self._ensure_column_exists("orders", "age_years", "INTEGER")
        self._ensure_column_exists("orders", "sample_date", "TEXT")
        self._ensure_column_exists("orders", "emitted", "INTEGER", default_value="0")
        self._ensure_column_exists("orders", "emitted_at", "TEXT")
        self._ensure_column_exists("orders", "deleted", "INTEGER", default_value="0")
        self._ensure_column_exists("orders", "deleted_reason", "TEXT")
        self._ensure_column_exists("orders", "deleted_by", "INTEGER")
        self._ensure_column_exists("orders", "deleted_at", "TEXT")
        self._ensure_column_exists("patients", "is_pregnant", "INTEGER", default_value="0")
        self._ensure_column_exists("patients", "gestational_age_weeks", "INTEGER")
        self._ensure_column_exists("patients", "expected_delivery_date", "TEXT")
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS order_tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                test_id INTEGER,
                result TEXT,
                sample_status TEXT DEFAULT 'recibida',
                sample_issue TEXT,
                observation TEXT,
                deleted INTEGER DEFAULT 0,
                deleted_reason TEXT,
                deleted_by INTEGER,
                deleted_at TEXT,
                FOREIGN KEY(order_id) REFERENCES orders(id),
                FOREIGN KEY(test_id) REFERENCES tests(id)
            )
        """)
        self.conn.commit()
        # Datos iniciales por defecto
        self.cur.execute("SELECT COUNT(*) FROM users")
        if self.cur.fetchone()[0] == 0:
            # Crear usuario admin por defecto
            self.cur.execute(
                "INSERT INTO users(username, password, role, full_name, profession, license) VALUES (?,?,?,?,?,?)",
                ("admin", "admin", "super", "Kewin Otazu Mamani", "Biólogo", "C.B.P. 18165")
            )
            self.conn.commit()
        else:
            self.cur.execute("SELECT full_name, profession, license FROM users WHERE username='admin'")
            row = self.cur.fetchone()
            if row:
                full_name, profession, license_code = row
                if not full_name or not profession or not license_code:
                    self.cur.execute(
                        "UPDATE users SET full_name=?, profession=?, license=? WHERE username='admin'",
                        (
                            full_name or "Kewin Otazu Mamani",
                            profession or "Biólogo",
                            license_code or "C.B.P. 18165"
                        )
                    )
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
                    "BHCG (Prueba de embarazo en sangre)", "VIH (Prueba rápida)", "Sífilis (Prueba rápida)",
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
                    "Cultivo de Campylobacter spp.", "Secreción (otros sitios)", "Secreción vaginal",
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
        # Ajustes posteriores para bases de datos existentes
        self._ensure_test_renamed(
            "HCG (Prueba de embarazo en orina)",
            "BHCG (Prueba de embarazo en sangre)"
        )
        self._ensure_test_renamed(
            "Cultivo de secreción vaginal",
            "Secreción vaginal"
        )
        self._ensure_test_renamed(
            "Cultivo de otras secreciones",
            "Secreción (otros sitios)"
        )
        self._ensure_test_exists("Secreción vaginal", "MICROBIOLOGÍA")
        self._ensure_test_exists("Secreción (otros sitios)", "MICROBIOLOGÍA")
        self._ensure_test_exists("Hemoglobina - Hematocrito", "HEMATOLOGÍA")
        self._ensure_test_exists("Parasitológico seriado", "PARASITOLOGÍA")
        # Cargar mapa de pruebas (nombre -> id)
        self.cur.execute("SELECT id, name FROM tests")
        for tid, name in self.cur.fetchall():
            self.test_map[name] = tid
        # Ajustar columnas agregadas posteriormente
        self._ensure_column_exists("order_tests", "sample_status", "TEXT", default_value="recibida")
        self._ensure_column_exists("order_tests", "sample_issue", "TEXT")
        self._ensure_column_exists("order_tests", "observation", "TEXT")
        self._ensure_column_exists("order_tests", "deleted", "INTEGER", default_value="0")
        self._ensure_column_exists("order_tests", "deleted_reason", "TEXT")
        self._ensure_column_exists("order_tests", "deleted_by", "INTEGER")
        self._ensure_column_exists("order_tests", "deleted_at", "TEXT")
    def authenticate_user(self, username, password):
        self.cur.execute(
            "SELECT id, username, role, full_name, profession, license FROM users WHERE username=? AND password=?",
            (username, password)
        )
        row = self.cur.fetchone()
        if row:
            uid, user, role, full_name, profession, license = row
            return {
                "id": uid,
                "username": user,
                "role": role,
                "full_name": full_name or "",
                "profession": profession or "",
                "license": license or ""
            }
        else:
            return None
    def create_user(self, username, password, role, full_name="", profession="", license=""):
        try:
            self.cur.execute(
                """
                INSERT INTO users(username, password, role, full_name, profession, license)
                VALUES (?,?,?,?,?,?)
                """,
                (username, password, role, full_name or None, profession or None, license or None)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def update_user_profile(self, user_id, full_name, profession, license):
        if not user_id:
            return False
        self.cur.execute(
            """
            UPDATE users
            SET full_name=?, profession=?, license=?
            WHERE id=?
            """,
            (full_name or None, profession or None, license or None, user_id)
        )
        self.conn.commit()
        return self.cur.rowcount > 0
    def find_patient(self, doc_type, doc_number):
        self.cur.execute("SELECT * FROM patients WHERE doc_type=? AND doc_number=?", (doc_type, doc_number))
        return self.cur.fetchone()
    def add_or_update_patient(
        self,
        doc_type,
        doc_number,
        first_name,
        last_name,
        birth_date,
        sex,
        origin,
        hcl,
        height,
        weight,
        blood_pressure,
        is_pregnant=False,
        gestational_age_weeks=None,
        expected_delivery_date=None
    ):
        first_name = first_name.upper() if first_name else first_name
        last_name = last_name.upper() if last_name else last_name
        existing = self.find_patient(doc_type, doc_number)
        preg_flag = 1 if is_pregnant else 0
        gest_age = None
        if gestational_age_weeks is not None:
            try:
                gest_age = int(gestational_age_weeks)
            except (TypeError, ValueError):
                gest_age = None
        delivery_date = expected_delivery_date if expected_delivery_date else None
        if existing:
            pid = existing[0]
            self.cur.execute("""
                UPDATE patients
                SET first_name=?, last_name=?, birth_date=?, sex=?, origin=?, hcl=?, height=?, weight=?, blood_pressure=?,
                    is_pregnant=?, gestational_age_weeks=?, expected_delivery_date=?
                WHERE id=?
            """, (
                first_name,
                last_name,
                birth_date,
                sex,
                origin,
                hcl,
                height,
                weight,
                blood_pressure,
                preg_flag,
                gest_age,
                delivery_date,
                pid
            ))
            self.conn.commit()
            return pid
        else:
            self.cur.execute("""
                INSERT INTO patients(
                    doc_type,
                    doc_number,
                    first_name,
                    last_name,
                    birth_date,
                    sex,
                    origin,
                    hcl,
                    height,
                    weight,
                    blood_pressure,
                    is_pregnant,
                    gestational_age_weeks,
                    expected_delivery_date
                )
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                doc_type,
                doc_number,
                first_name,
                last_name,
                birth_date,
                sex,
                origin,
                hcl,
                height,
                weight,
                blood_pressure,
                preg_flag,
                gest_age,
                delivery_date
            ))
            self.conn.commit()
            return self.cur.lastrowid

    def add_order_with_tests(
        self,
        patient_id,
        test_names,
        user_id,
        observations="",
        requested_by="",
        diagnosis="",
        insurance_type="SIS",
        fua_number=None,
        age_years=None,
        sample_date=None
    ):
        import datetime
        date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sample_date_str = None
        if sample_date:
            sample_date_str = str(sample_date)
        age_value = None
        if age_years is not None:
            try:
                age_value = int(age_years)
            except (TypeError, ValueError):
                age_value = None
        insurance_value = (insurance_type or "SIS").strip() or "SIS"
        fua_value = fua_number.strip() if isinstance(fua_number, str) else fua_number
        if isinstance(fua_value, str) and fua_value == "":
            fua_value = None
        self.cur.execute("""
            INSERT INTO orders(patient_id, date, sample_date, created_by, observations, requested_by, diagnosis, insurance_type, fua_number, age_years, completed)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (patient_id, date_str, sample_date_str, user_id, observations, requested_by, diagnosis, insurance_value, fua_value, age_value, 0))
        order_id = self.cur.lastrowid
        for name in test_names:
            if name in self.test_map:
                test_id = self.test_map[name]
                self.cur.execute("INSERT INTO order_tests(order_id, test_id, result) VALUES (?,?,?)",
                                 (order_id, test_id, ""))
        self.conn.commit()
        return order_id
    def find_recent_duplicate_order(self, patient_id, test_names, within_minutes=10):
        if not patient_id or not test_names:
            return None
        normalized_target = sorted(name.strip().lower() for name in test_names if name)
        if not normalized_target:
            return None
        import datetime
        threshold = datetime.datetime.now() - datetime.timedelta(minutes=within_minutes)
        self.cur.execute(
            """
            SELECT id FROM orders
            WHERE patient_id=?
              AND datetime(date) >= datetime(?)
              AND (deleted IS NULL OR deleted=0)
            ORDER BY datetime(date) DESC, id DESC
            """,
            (patient_id, threshold.strftime("%Y-%m-%d %H:%M:%S"))
        )
        candidate_ids = [row[0] for row in self.cur.fetchall()]
        for oid in candidate_ids:
            self.cur.execute(
                """
                SELECT t.name
                FROM order_tests ot
                JOIN tests t ON ot.test_id = t.id
                WHERE ot.order_id=? AND (ot.deleted IS NULL OR ot.deleted=0)
                ORDER BY t.name
                """,
                (oid,)
            )
            names = [row[0].strip().lower() for row in self.cur.fetchall() if row and row[0]]
            if names == normalized_target:
                return oid
        return None

    def mark_order_deleted(self, order_id, reason, user_id=None):
        if not order_id:
            return False
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cur.execute(
            """
            UPDATE orders
            SET deleted=1,
                deleted_reason=?,
                deleted_by=?,
                deleted_at=?,
                completed=0,
                emitted=0
            WHERE id=?
            """,
            (reason or "", user_id, timestamp, order_id)
        )
        order_updated = self.cur.rowcount
        self.cur.execute(
            """
            UPDATE order_tests
            SET deleted=1,
                deleted_reason=?,
                deleted_by=?,
                deleted_at=?
            WHERE order_id=?
            """,
            (reason or "", user_id, timestamp, order_id)
        )
        tests_updated = self.cur.rowcount
        self.conn.commit()
        return (order_updated > 0) or (tests_updated > 0)

    def delete_order_test(self, order_test_id, reason, user_id=None):
        if not order_test_id:
            return False
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cur.execute(
            """
            UPDATE order_tests
            SET deleted=1,
                deleted_reason=?,
                deleted_by=?,
                deleted_at=?
            WHERE id=?
            """,
            (reason or "", user_id, timestamp, order_test_id)
        )
        if not self.cur.rowcount:
            return False
        self.conn.commit()
        self.cur.execute("SELECT order_id FROM order_tests WHERE id=?", (order_test_id,))
        row = self.cur.fetchone()
        if row:
            self._update_order_completion(row[0])
        return True

    def get_pending_orders(self):
        self.cur.execute("""
            SELECT o.id, p.first_name, p.last_name, o.date, o.sample_date, p.doc_type, p.doc_number
            FROM orders o
            JOIN patients p ON o.patient_id=p.id
            WHERE o.completed=0 AND (o.deleted IS NULL OR o.deleted=0)
            ORDER BY o.date ASC, o.id ASC
        """)
        return self.cur.fetchall()

    def get_completed_orders(self, include_emitted=False):
        if include_emitted:
            self.cur.execute("""
                SELECT o.id, p.first_name, p.last_name, o.date, o.sample_date, p.doc_type, p.doc_number, o.emitted, o.emitted_at
                FROM orders o
                JOIN patients p ON o.patient_id=p.id
                WHERE o.completed=1 AND (o.deleted IS NULL OR o.deleted=0)
                ORDER BY o.date ASC, o.id ASC
            """)
        else:
            self.cur.execute("""
                SELECT o.id, p.first_name, p.last_name, o.date, o.sample_date, p.doc_type, p.doc_number, o.emitted, o.emitted_at
                FROM orders o
                JOIN patients p ON o.patient_id=p.id
                WHERE o.completed=1 AND (o.emitted IS NULL OR o.emitted=0)
                  AND (o.deleted IS NULL OR o.deleted=0)
                ORDER BY o.date ASC, o.id ASC
            """)
        return self.cur.fetchall()
    def get_order_details(self, order_id):
        self.cur.execute("""
            SELECT p.first_name, p.last_name, p.doc_type, p.doc_number, p.birth_date, p.sex, p.origin, p.hcl,
                   p.is_pregnant, p.gestational_age_weeks, p.expected_delivery_date,
                   o.date, o.sample_date, o.observations, o.requested_by, o.diagnosis, o.insurance_type, o.fua_number, o.age_years, o.emitted, o.emitted_at
            FROM orders o
            JOIN patients p ON o.patient_id = p.id
            WHERE o.id = ?
        """, (order_id,))
        header = self.cur.fetchone()
        if not header:
            return None
        (first_name, last_name, doc_type, doc_number, birth_date, sex, origin, hcl,
         is_pregnant, gest_age_weeks, expected_delivery,
         date, sample_date, obs, req_by, diag, insurance_type, fua_number, age_years, emitted, emitted_at) = header
        patient_info = {
            "name": f"{(first_name or '').upper()} {(last_name or '').upper()}".strip(),
            "doc_type": doc_type,
            "doc_number": doc_number,
            "birth_date": birth_date,
            "sex": sex,
            "origin": origin,
            "hcl": hcl,
            "is_pregnant": bool(is_pregnant) if is_pregnant not in (None, "") else False,
            "gestational_age_weeks": gest_age_weeks,
            "expected_delivery_date": expected_delivery
        }
        order_info = {
            "date": date,
            "sample_date": sample_date,
            "observations": obs,
            "requested_by": req_by,
            "diagnosis": diag,
            "insurance_type": insurance_type,
            "fua_number": fua_number,
            "age_years": age_years,
            "emitted": emitted,
            "emitted_at": emitted_at,
        }
        self.cur.execute("""
            SELECT t.name, ot.result, t.category, ot.sample_status, ot.sample_issue, ot.observation, ot.id
            FROM order_tests ot
            JOIN tests t ON ot.test_id = t.id
            WHERE ot.order_id = ?
              AND (ot.deleted IS NULL OR ot.deleted=0)
            ORDER BY ot.id ASC
        """, (order_id,))
        results = self.cur.fetchall()
        return {"patient": patient_info, "order": order_info, "results": results}
    def save_results(self, order_id, results_dict):
        for name, payload in results_dict.items():
            if name not in self.test_map:
                continue
            tid = self.test_map[name]
            result_value = payload
            sample_status = None
            sample_issue = None
            observation = None
            if isinstance(payload, dict) and "result" in payload:
                result_value = payload.get("result")
                sample_status = payload.get("sample_status")
                sample_issue = payload.get("sample_issue")
                observation = payload.get("observation")
            if isinstance(result_value, dict):
                stored = json.dumps(result_value, ensure_ascii=False)
            else:
                stored = result_value
            if sample_status is None:
                sample_status = "recibida"
            if sample_issue is None:
                sample_issue = ""
            if observation is None:
                observation = ""
            self.cur.execute(
                """
                UPDATE order_tests
                SET result=?,
                    sample_status=?,
                    sample_issue=?,
                    observation=?
                WHERE order_id=? AND test_id=?
                """,
                (stored, sample_status, sample_issue, observation, order_id, tid)
            )
        return self._update_order_completion(order_id)

    def ensure_followup_order_for_pending(self, source_order_id, pending_tests, user_id):
        if not source_order_id or not pending_tests or not user_id:
            return None
        self.cur.execute(
            """
            SELECT patient_id, requested_by, diagnosis, insurance_type, fua_number, age_years
            FROM orders
            WHERE id=? AND (deleted IS NULL OR deleted=0)
            """,
            (source_order_id,)
        )
        row = self.cur.fetchone()
        if not row:
            return None
        patient_id, requested_by, diagnosis, insurance_type, fua_number, age_years = row
        normalized_tests = []
        for name in pending_tests:
            if not name:
                continue
            if name not in self.test_map:
                self.cur.execute("SELECT id FROM tests WHERE name=?", (name,))
                fetched = self.cur.fetchone()
                if fetched:
                    self.test_map[name] = fetched[0]
            if name in self.test_map:
                normalized_tests.append(name)
        if not normalized_tests:
            return None
        tests_to_add = []
        for test_name in normalized_tests:
            if not self._pending_test_has_followup(patient_id, source_order_id, test_name):
                tests_to_add.append(test_name)
        if not tests_to_add:
            return None
        base_note = f"Pendiente de orden #{source_order_id}"
        detail_note = ", ".join(tests_to_add)
        observations = base_note if not detail_note else f"{base_note} - {detail_note}"
        new_order_id = self.add_order_with_tests(
            patient_id,
            tests_to_add,
            user_id,
            observations=observations,
            requested_by=requested_by or "",
            diagnosis=diagnosis or "",
            insurance_type=insurance_type or "SIS",
            fua_number=fua_number,
            age_years=age_years,
            sample_date=None
        )
        return new_order_id

    def remove_test_from_order(self, order_id, test_name):
        if not test_name:
            return False
        if test_name not in self.test_map:
            self.cur.execute("SELECT id FROM tests WHERE name=?", (test_name,))
            row = self.cur.fetchone()
            if row:
                self.test_map[test_name] = row[0]
        tid = self.test_map.get(test_name)
        if not tid:
            return False
        self.cur.execute("DELETE FROM order_tests WHERE order_id=? AND test_id=?", (order_id, tid))
        if self.cur.rowcount:
            self._update_order_completion(order_id)
            return True
        self.conn.commit()
        return False

    def _update_order_completion(self, order_id):
        self.cur.execute(
            """
            SELECT result, sample_status
            FROM order_tests
            WHERE order_id=? AND (deleted IS NULL OR deleted=0)
            """,
            (order_id,)
        )
        rows = self.cur.fetchall()
        if not rows:
            completed_flag = 1
        else:
            pending = 0
            for result, sample_status in rows:
                status = (sample_status or "recibida").strip().lower()
                if status == "pendiente":
                    pending += 1
                    continue
                if status == "rechazada":
                    continue
                if result in (None, ""):
                    pending += 1
            completed_flag = 0 if pending else 1
        self.cur.execute("UPDATE orders SET completed=? WHERE id=?", (completed_flag, order_id))
        self.conn.commit()
        return completed_flag

    def _pending_test_has_followup(self, patient_id, source_order_id, test_name):
        if not patient_id or not source_order_id or not test_name:
            return False
        pattern = f"%Pendiente de orden #{source_order_id}%"
        self.cur.execute(
            """
            SELECT COUNT(*)
            FROM order_tests ot
            JOIN orders o ON ot.order_id = o.id
            JOIN tests t ON ot.test_id = t.id
            WHERE o.patient_id=?
              AND (o.deleted IS NULL OR o.deleted=0)
              AND (ot.deleted IS NULL OR ot.deleted=0)
              AND o.observations LIKE ?
              AND t.name=?
            """,
            (patient_id, pattern, test_name)
        )
        row = self.cur.fetchone()
        return bool(row and row[0])

    def mark_order_emitted(self, order_id, emitted_at):
        self.cur.execute(
            """
            UPDATE orders
            SET emitted=1,
                emitted_at=COALESCE(emitted_at, ?)
            WHERE id=?
            """,
            (emitted_at, order_id)
        )
        self.conn.commit()
    def get_statistics(self, start_datetime=None, end_datetime=None):
        stats = {}
        order_where = "WHERE (o.deleted IS NULL OR o.deleted=0)"
        order_params = []
        tests_where = (
            "FROM order_tests ot "
            "JOIN orders o ON ot.order_id = o.id "
            "WHERE (ot.deleted IS NULL OR ot.deleted=0) "
            "AND (o.deleted IS NULL OR o.deleted=0)"
        )
        tests_params = []
        if start_datetime and end_datetime:
            order_where += " AND datetime(o.date) BETWEEN datetime(?) AND datetime(?)"
            order_params = [start_datetime, end_datetime]
            tests_where += " AND datetime(o.date) BETWEEN datetime(?) AND datetime(?)"
            tests_params = [start_datetime, end_datetime]
        self.cur.execute(f"SELECT COUNT(DISTINCT o.patient_id) FROM orders o {order_where}", order_params)
        row = self.cur.fetchone()
        stats["total_patients"] = row[0] if row and row[0] is not None else 0
        self.cur.execute(f"SELECT COUNT(*) FROM orders o {order_where}", order_params)
        stats["total_orders"] = self.cur.fetchone()[0]
        self.cur.execute(f"SELECT COUNT(*) {tests_where}", tests_params)
        stats["total_tests_conducted"] = self.cur.fetchone()[0]
        self.cur.execute(
            """
            SELECT t.category, COUNT(*)
            FROM order_tests ot
            JOIN tests t ON ot.test_id = t.id
            JOIN orders o ON ot.order_id = o.id
            WHERE (ot.deleted IS NULL OR ot.deleted=0)
              AND (o.deleted IS NULL OR o.deleted=0)
        """
            + (" AND datetime(o.date) BETWEEN datetime(?) AND datetime(?)" if tests_params else "") +
            " GROUP BY t.category",
            tests_params
        )
        stats["by_category"] = self.cur.fetchall()
        self.cur.execute(
            """
            SELECT t.category, t.name, COUNT(*)
            FROM order_tests ot
            JOIN tests t ON ot.test_id = t.id
            JOIN orders o ON ot.order_id = o.id
            WHERE (ot.deleted IS NULL OR ot.deleted=0)
              AND (o.deleted IS NULL OR o.deleted=0)
        """
            + (" AND datetime(o.date) BETWEEN datetime(?) AND datetime(?)" if tests_params else "") +
            " GROUP BY t.category, t.name ORDER BY t.category, t.name",
            tests_params
        )
        detail_rows = self.cur.fetchall()
        detail = OrderedDict()
        for category, test_name, count in detail_rows:
            if category not in detail:
                detail[category] = {"total": 0, "tests": []}
            detail[category]["tests"].append((test_name, count))
            detail[category]["total"] += count
        stats["by_category_detail"] = detail
        return stats
    def get_results_in_range(self, start_datetime, end_datetime):
        self.cur.execute(
            """
            SELECT ot.id, o.id, o.date, o.sample_date, p.first_name, p.last_name, p.doc_type, p.doc_number,
                   p.sex, p.birth_date, p.hcl, p.origin, p.is_pregnant, p.gestational_age_weeks, p.expected_delivery_date,
                   o.age_years, o.observations, o.insurance_type, o.fua_number,
                   t.name, t.category, ot.result, ot.sample_status, ot.sample_issue, ot.observation
            FROM order_tests ot
            JOIN orders o ON ot.order_id = o.id
            JOIN patients p ON o.patient_id = p.id
            JOIN tests t ON ot.test_id = t.id
            WHERE datetime(o.date) BETWEEN datetime(?) AND datetime(?)
              AND (o.deleted IS NULL OR o.deleted=0)
              AND (ot.deleted IS NULL OR ot.deleted=0)
            ORDER BY datetime(o.date) ASC, o.id ASC, ot.id ASC
            """,
            (start_datetime, end_datetime)
        )
        return self.cur.fetchall()
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

    def get_all_tests(self):
        self.cur.execute("SELECT name, category FROM tests ORDER BY category, name")
        return self.cur.fetchall()

    def get_tests_for_order(self, order_id):
        self.cur.execute("""
            SELECT t.name FROM order_tests ot
            JOIN tests t ON ot.test_id = t.id
            WHERE ot.order_id=?
        """, (order_id,))
        return [row[0] for row in self.cur.fetchall()]

    def add_tests_to_order(self, order_id, test_names):
        if not test_names:
            return []
        self.cur.execute("""
            SELECT t.name FROM order_tests ot
            JOIN tests t ON ot.test_id = t.id
            WHERE ot.order_id=?
        """, (order_id,))
        existing = {row[0] for row in self.cur.fetchall()}
        added = []
        for name in test_names:
            if name not in self.test_map:
                self.cur.execute("SELECT id FROM tests WHERE name=?", (name,))
                row = self.cur.fetchone()
                if row:
                    self.test_map[name] = row[0]
            if name in self.test_map and name not in existing:
                test_id = self.test_map[name]
                self.cur.execute(
                    "INSERT INTO order_tests(order_id, test_id, result) VALUES (?,?,?)",
                    (order_id, test_id, "")
                )
                added.append(name)
        if added:
            self.cur.execute("UPDATE orders SET completed=0 WHERE id=?", (order_id,))
        self.conn.commit()
        return added

    def update_order_fua(self, order_id, fua_number):
        if not order_id:
            return False
        value = fua_number.strip() if isinstance(fua_number, str) else fua_number
        if isinstance(value, str) and value == "":
            value = None
        self.cur.execute("SELECT id FROM orders WHERE id=?", (order_id,))
        if not self.cur.fetchone():
            return False
        self.cur.execute(
            "UPDATE orders SET fua_number=? WHERE id=?",
            (value, order_id)
        )
        self.conn.commit()
        return True

    def get_patient_history_by_document(self, doc_number, doc_type=None):
        if not doc_number:
            return []
        params = [doc_number]
        query = """
            SELECT o.id, o.date, o.sample_date, t.name, ot.result, t.category,
                   p.first_name, p.last_name, p.doc_type, p.doc_number,
                   p.sex, p.birth_date, p.hcl, p.origin, o.age_years, o.observations, o.insurance_type, o.fua_number, o.emitted, o.emitted_at,
                   ot.sample_status, ot.sample_issue, ot.observation, ot.id
            FROM orders o
            JOIN patients p ON o.patient_id = p.id
            JOIN order_tests ot ON ot.order_id = o.id
            JOIN tests t ON ot.test_id = t.id
            WHERE p.doc_number = ? AND (o.deleted IS NULL OR o.deleted=0) AND (ot.deleted IS NULL OR ot.deleted=0)
        """
        if doc_type:
            query += " AND p.doc_type = ?"
            params.append(doc_type)
        query += " ORDER BY datetime(o.date) DESC, o.id DESC, t.name ASC"
        self.cur.execute(query, params)
        return self.cur.fetchall()

    def _ensure_test_renamed(self, old_name, new_name):
        if old_name == new_name:
            return
        self.cur.execute("UPDATE tests SET name=? WHERE name=?", (new_name, old_name))
        self.conn.commit()

    def _ensure_test_exists(self, name, category):
        self.cur.execute("SELECT id FROM tests WHERE name=?", (name,))
        row = self.cur.fetchone()
        if row:
            if name not in self.test_map:
                self.test_map[name] = row[0]
            return
        self.cur.execute("INSERT INTO tests(name, category) VALUES (?,?)", (name, category))
        self.conn.commit()
        if name not in self.test_map:
            self.cur.execute("SELECT id FROM tests WHERE name=?", (name,))
            new_row = self.cur.fetchone()
            if new_row:
                self.test_map[name] = new_row[0]
