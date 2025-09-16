# login_dialog.py
from PyQt5.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QGridLayout, QMessageBox
from PyQt5.QtCore import QDateTime, Qt, QTimer

LAB_TITLE = "Laboratorio P.S. Iñapari - 002789"

class LoginDialog(QDialog):
    def __init__(self, labdb):
        super().__init__()
        self.labdb = labdb
        self.setWindowTitle(LAB_TITLE)
        self.setModal(True)
        self.showFullScreen()        # pantalla completa
        layout = QVBoxLayout()
        # Formulario usuario/contraseña
        form_layout = QGridLayout()
        label_user = QLabel("Usuario:")
        self.input_user = QLineEdit()
        label_pass = QLabel("Contraseña:")
        self.input_pass = QLineEdit(); self.input_pass.setEchoMode(QLineEdit.Password)
        form_layout.addWidget(label_user, 0, 0); form_layout.addWidget(self.input_user, 0, 1)
        form_layout.addWidget(label_pass, 1, 0); form_layout.addWidget(self.input_pass, 1, 1)
        layout.addLayout(form_layout)

        # Botón login
        btn_login = QPushButton("Ingresar")
        layout.addWidget(btn_login)

        # Reloj en vivo
        self.lbl_time = QLabel("", self)
        self.lbl_time.setAlignment(Qt.AlignCenter)
        self.lbl_time.setStyleSheet("font-size:18px;color:#0a84ff;")
        layout.addWidget(self.lbl_time)
        self.setLayout(layout)

        # timer para reloj
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(1000)
        self._tick()

        btn_login.clicked.connect(self.check_login)
        self.user_data = None

    def _tick(self):
        self.lbl_time.setText(QDateTime.currentDateTime().toString("dd/MM/yyyy HH:mm:ss"))

    def check_login(self):
        username = self.input_user.text().strip(); password = self.input_pass.text().strip()
        if not username or not password:
            QMessageBox.warning(self, "Campos vacíos", "Por favor ingrese nombre de usuario y contraseña.")
            return
        user = self.labdb.authenticate_user(username, password)
        if user:
            self.user_data = user
            self.accept()
        else:
            QMessageBox.warning(self, "Credenciales inválidas", "Usuario o contraseña incorrectos. Inténtelo de nuevo.")

