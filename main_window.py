# main_window.py
import copy
import datetime
import json
import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
                             QStackedWidget, QFormLayout, QScrollArea, QGroupBox, QComboBox,
                             QLineEdit, QTextEdit, QTableWidget, QTableWidgetItem, QFileDialog, QMessageBox, QCheckBox,
                             QDateEdit, QRadioButton, QButtonGroup, QDialog, QDialogButtonBox, QListWidget, QListWidgetItem)
from PyQt5.QtCore import QDate, QDateTime, Qt, QTimer
from fpdf import FPDF  # Asegúrese de tener fpdf instalado (pip install fpdf)

LAB_TITLE = "Laboratorio P.S. Iñapari - 002789"

# Definiciones de plantillas de resultados estructurados por examen
HEMOGRAM_BASE_FIELDS = [
    {
        "key": "hematocrito",
        "label": "Hematocrito (Hto)",
        "unit": "%",
        "reference": (
            "RN: 44-65 %\n"
            "Niños 1-10 a: 35-45 %\n"
            "Hombres adultos: 40-54 %\n"
            "Mujeres adultas: 36-47 %\n"
            "Gestantes (2°-3° trim): 33-43 %"
        ),
        "placeholder": "Ej. 42.5"
    },
    {
        "key": "hemoglobina",
        "label": "Hemoglobina (Hb)",
        "unit": "g/dL",
        "reference": (
            "RN: 14.0-24.0 g/dL\n"
            "1-12 meses: 10.0-12.5 g/dL\n"
            "Niños 1-12 años: 11.5-15.5 g/dL\n"
            "Mujeres adultas: 12.0-16.0 g/dL\n"
            "Hombres adultos: 13.5-17.5 g/dL\n"
            "Gestantes (2°-3° trim): ≥11.0 g/dL"
        ),
        "placeholder": "Ej. 14.1"
    },
    {
        "key": "leucocitos",
        "label": "Leucocitos",
        "unit": "/µL",
        "reference": (
            "RN: 9 000-30 000 /µL\n"
            "1-12 meses: 6 000-17 500 /µL\n"
            "Niños 1-6 años: 5 000-15 500 /µL\n"
            "Niños 6-18 años: 4 500-13 500 /µL\n"
            "Adultos: 4 500-11 000 /µL"
        ),
        "placeholder": "Ej. 7 500"
    },
    {
        "key": "eritrocitos",
        "label": "Recuento de hematíes (RBC)",
        "unit": "millones/µL",
        "reference": (
            "RN: 4.1-6.1 millones/µL\n"
            "Niños 1-10 años: 3.9-5.3 millones/µL\n"
            "Hombres adultos: 4.5-6.0 millones/µL\n"
            "Mujeres adultas: 4.0-5.4 millones/µL"
        ),
        "placeholder": "Ej. 4.8"
    },
    {
        "key": "plaquetas",
        "label": "Plaquetas",
        "unit": "/µL",
        "reference": (
            "RN: 150 000-450 000 /µL\n"
            "Niños: 150 000-450 000 /µL\n"
            "Adultos: 150 000-400 000 /µL"
        ),
        "placeholder": "Ej. 250 000"
    },
    {
        "key": "segmentados",
        "label": "Segmentados",
        "unit": "%",
        "reference": (
            "Adultos: 40-75 %\n"
            "Niños 1-6 años: 30-60 %"
        )
    },
    {
        "key": "abastonados",
        "label": "Abastonados",
        "unit": "%",
        "reference": "0-6 %",
        "optional": True
    },
    {
        "key": "linfocitos",
        "label": "Linfocitos",
        "unit": "%",
        "reference": (
            "RN: 22-35 %\n"
            "Niños 1-6 años: 40-65 %\n"
            "Adultos: 20-45 %"
        )
    },
    {
        "key": "monocitos",
        "label": "Monocitos",
        "unit": "%",
        "reference": "2-10 %"
    },
    {
        "key": "eosinofilos",
        "label": "Eosinófilos",
        "unit": "%",
        "reference": "0-6 %"
    },
    {
        "key": "basofilos",
        "label": "Basófilos",
        "unit": "%",
        "reference": "0-2 %",
        "optional": True
    },
    {
        "key": "mielocitos",
        "label": "Mielocitos",
        "unit": "%",
        "optional": True
    },
    {
        "key": "metamielocitos",
        "label": "Metamielocitos",
        "unit": "%",
        "optional": True
    },
    {
        "key": "otras_celulas",
        "label": "Otras anormalidades",
        "optional": True,
        "placeholder": "Ej. Células en banda"
    },
    {
        "key": "observaciones",
        "label": "Observaciones microscópicas",
        "type": "text_area",
        "optional": True,
        "placeholder": "Describe hallazgos morfológicos"
    }
]

URINE_BASE_FIELDS = [
    {"type": "section", "label": "Examen físico"},
    {"key": "color", "label": "Color", "reference": "Amarillo pajizo; RN: incoloro a amarillo claro"},
    {"key": "aspecto", "label": "Aspecto", "reference": "Transparente; leve turbidez fisiológica en gestantes"},
    {"key": "olor", "label": "Olor", "reference": "Aromático suave", "optional": True},
    {"type": "section", "label": "Examen químico"},
    {"key": "densidad", "label": "Densidad", "reference": "RN: 1.002-1.012 | Niños: 1.005-1.015 | Adultos: 1.005-1.030"},
    {"key": "ph", "label": "pH", "reference": "RN: 5.0-7.0 | Niños/Adultos: 5.0-7.5"},
    {"key": "urobilinogeno", "label": "Urobilinógeno", "reference": "0.1-1.0 mg/dL"},
    {"key": "bilirrubina", "label": "Bilirrubina", "reference": "Negativo"},
    {"key": "proteinas", "label": "Proteínas", "reference": "Negativo (<15 mg/dL)"},
    {"key": "nitritos", "label": "Nitritos", "reference": "Negativo"},
    {"key": "glucosa", "label": "Glucosa", "reference": "Negativo"},
    {"key": "cetonas", "label": "Cetonas", "reference": "Negativo"},
    {"key": "leucocitos_quimico", "label": "Leucocitos", "reference": "Negativo"},
    {"key": "acido_ascorbico", "label": "Ácido ascórbico", "reference": "Negativo", "optional": True},
    {"key": "sangre", "label": "Sangre", "reference": "Negativo"},
    {"type": "section", "label": "Sedimento urinario"},
    {"key": "celulas_epiteliales", "label": "Células epiteliales/c", "reference": "0-5 /campo"},
    {"key": "leucocitos_campo", "label": "Leucocitos/c", "reference": "0-5 /campo (mujeres hasta 10)"},
    {"key": "hematies_campo", "label": "Hematíes/c", "reference": "0-2 /campo"},
    {"key": "cristales", "label": "Cristales/c", "reference": "No se observan", "optional": True},
    {"key": "cilindros", "label": "Cilindros/c", "reference": "0-2 cilindros hialinos/campo"},
    {"key": "otros_hallazgos", "label": "Otros hallazgos", "type": "text_area", "optional": True}
]

COPRO_DIRECT_FIELDS = [
    {"type": "section", "label": "Evaluación macroscópica"},
    {"key": "consistencia", "label": "Consistencia", "reference": "Formada; lactantes semiformada"},
    {"key": "color", "label": "Color", "reference": "Pardo amarillento", "optional": True},
    {"key": "moco", "label": "Moco", "type": "choice", "choices": ["Ausente", "Escaso", "Moderado", "Abundante"], "reference": "Ausente o escaso"},
    {"type": "section", "label": "Evaluación microscópica"},
    {"key": "leucocitos", "label": "Leucocitos/c", "reference": "0-2 /campo"},
    {"key": "hematies", "label": "Hematíes/c", "reference": "0-1 /campo"},
    {"key": "parasitos", "label": "Parásitos observados", "type": "text_area", "reference": "No se observan", "optional": True},
    {"key": "levaduras", "label": "Levaduras", "reference": "Ausentes o escasas", "optional": True},
    {"key": "grasas", "label": "Grasas", "reference": "Ausentes", "optional": True},
    {"key": "reaccion_inflamatoria", "label": "Reacción inflamatoria", "optional": True, "helper": "Describa tinción Wright / diferenciación PMN-MMN"},
    {"key": "metodo", "label": "Método", "type": "choice", "choices": ["Directo", "Concentrado", "Serial"], "reference": "Registrar técnica aplicada"},
    {"key": "observaciones", "label": "Observaciones", "type": "text_area", "optional": True}
]

COPRO_CONCENT_FIELDS = [
    {"type": "section", "label": "Procedimiento"},
    {"key": "metodo", "label": "Método", "type": "choice", "choices": ["Concentración", "Flotación", "Sedimentación"], "reference": "Indique técnica aplicada"},
    {"type": "section", "label": "Hallazgos"},
    {"key": "parasitos", "label": "Parásitos observados", "type": "text_area", "reference": "No se observan", "optional": True},
    {"key": "quistes", "label": "Quistes / huevos", "reference": "No se observan", "optional": True},
    {"key": "observaciones", "label": "Observaciones", "type": "text_area", "optional": True}
]

GRAM_FIELDS = [
    {"type": "section", "label": "Examen directo"},
    {"key": "directo_celulas", "label": "Células/c", "reference": "Escasas células epiteliales", "optional": True},
    {"key": "directo_leucocitos", "label": "Leucocitos/c", "reference": "0-10 /campo"},
    {"key": "directo_hematies", "label": "Hematíes/c", "reference": "0-1 /campo", "optional": True},
    {"key": "directo_germenes", "label": "Gérmenes", "reference": "Flora bacteriana escasa", "optional": True},
    {"type": "section", "label": "Coloración de Gram"},
    {"key": "gram_celulas", "label": "Células/c", "reference": "Escasas células epiteliales", "optional": True},
    {"key": "gram_leucocitos", "label": "Leucocitos/c", "reference": "0-10 /campo"},
    {"key": "gram_bacilos_doderlein", "label": "Bacilos de Döderlein", "reference": "Abundantes"},
    {"key": "gram_bacterias", "label": "Bacterias", "reference": "Flora mixta escasa", "optional": True},
    {"key": "gram_celulas_clue", "label": "Células clue", "reference": "Ausentes", "optional": True},
    {"key": "observaciones", "label": "Observaciones", "type": "text_area", "optional": True}
]

REACTION_FIELDS = [
    {"key": "leucocitos_pmn", "label": "Leucocitos PMN/c", "reference": "0-1 /campo"},
    {"key": "leucocitos_mmn", "label": "Leucocitos MMN/c", "reference": "0-1 /campo"},
    {"key": "moco", "label": "Moco", "type": "choice", "choices": ["Ausente", "Escaso", "Moderado", "Abundante"], "reference": "Ausente o escaso", "optional": True},
    {"key": "observaciones", "label": "Observaciones", "type": "text_area", "optional": True}
]

SEDIMENTO_FIELDS = [
    {"key": "celulas_epiteliales", "label": "Células epiteliales/c", "reference": "0-5 /campo"},
    {"key": "leucocitos_campo", "label": "Leucocitos/c", "reference": "0-5 /campo"},
    {"key": "hematies_campo", "label": "Hematíes/c", "reference": "0-2 /campo"},
    {"key": "bacterias", "label": "Bacterias", "reference": "Ausentes o escasas", "optional": True},
    {"key": "cristales", "label": "Cristales", "reference": "No se observan", "optional": True},
    {"key": "cilindros", "label": "Cilindros", "reference": "0-2 hialinos/campo", "optional": True},
    {"key": "otros_hallazgos", "label": "Otros hallazgos", "type": "text_area", "optional": True}
]

def build_bool_observation_template(positive_text="Positivo", negative_text="Negativo", reference_text="Negativo"):
    return {
        "fields": [
            {
                "key": "resultado",
                "label": "Resultado",
                "type": "bool",
                "positive_text": positive_text,
                "negative_text": negative_text,
                "reference": reference_text
            },
            {
                "key": "observaciones",
                "label": "Observaciones",
                "type": "text_area",
                "optional": True,
                "placeholder": "Observaciones (opcional)"
            }
        ]
    }

def build_single_value_template(key, label, unit=None, reference=None, placeholder=None, helper=None, optional=False, field_type="line", choices=None):
    field = {
        "key": key,
        "label": label
    }
    if unit:
        field["unit"] = unit
    if reference:
        field["reference"] = reference
    if placeholder:
        field["placeholder"] = placeholder
    if helper:
        field["helper"] = helper
    if optional:
        field["optional"] = True
    if field_type != "line":
        field["type"] = field_type
    if choices:
        field["choices"] = choices
    return {"fields": [field]}

SECRECION_VAGINAL_FIELDS = [
    {"type": "section", "label": "Evaluación clínica"},
    {"key": "ph", "label": "pH vaginal", "reference": "Mujer fértil: 3.8-4.5 | Postmenopáusica: hasta 5.0", "placeholder": "Ej. 4.2"},
    {"key": "aspecto", "label": "Aspecto", "reference": "Homogéneo, blanco lechoso", "optional": True},
    {"key": "olor", "label": "Olor", "reference": "Sin olor fétido", "optional": True},
    {"type": "section", "label": "Montaje fresco"},
    {"key": "leucocitos", "label": "Leucocitos/campo", "reference": "<10/campo de gran aumento"},
    {"key": "lactobacilos", "label": "Lactobacilos", "reference": "Abundantes"},
    {"key": "celulas_clue", "label": "Células clue", "reference": "Ausentes"},
    {"key": "trichomonas", "label": "Trichomonas vaginalis", "reference": "No se observan", "optional": True},
    {"key": "levaduras", "label": "Levaduras/blastosporas", "reference": "No se observan", "optional": True},
    {"type": "section", "label": "Coloración de Gram"},
    {"key": "puntaje_nugent", "label": "Puntaje de Nugent", "reference": "0-3 flora normal | 4-6 flora intermedia | 7-10 vaginosis"},
    {"key": "bacilos_doderlein", "label": "Bacilos de Döderlein", "reference": "Abundantes"},
    {"key": "cocos_gram", "label": "Cocos/Gram variables", "optional": True},
    {"type": "section", "label": "Pruebas complementarias"},
    {"key": "test_aminas", "label": "Test de aminas", "type": "bool", "positive_text": "Positivo", "negative_text": "Negativo", "reference": "Negativo"},
    {"key": "observaciones", "label": "Observaciones", "type": "text_area", "optional": True, "placeholder": "Hallazgos adicionales relevantes"}
]

SECRECION_GENERAL_FIELDS = [
    {"type": "section", "label": "Datos de la muestra"},
    {"key": "tipo_secrecion", "label": "Tipo de secreción", "type": "choice", "choices": ["Cervical", "Uretral", "Ocular", "Nasofaríngea", "Otorrinolaringológica", "Rectal", "Cutánea", "Otra"], "reference": "Seleccione sitio anatómico"},
    {"key": "aspecto", "label": "Aspecto", "reference": "Transparente o mucoso", "optional": True},
    {"key": "olor", "label": "Olor", "reference": "Sin olor fétido", "optional": True},
    {"type": "section", "label": "Examen directo"},
    {"key": "celulas", "label": "Células epiteliales/campo", "reference": "Escasas", "optional": True},
    {"key": "leucocitos", "label": "Leucocitos/campo", "reference": "<5/campo en secreciones no purulentas"},
    {"key": "eritrocitos", "label": "Hematíes/campo", "reference": "0-1 /campo", "optional": True},
    {"key": "flora", "label": "Flora bacteriana", "reference": "Flora mixta escasa", "optional": True},
    {"key": "levaduras", "label": "Levaduras", "reference": "No se observan", "optional": True},
    {"key": "parasitos", "label": "Parásitos", "reference": "No se observan", "optional": True},
    {"type": "section", "label": "Gram (si aplica)"},
    {"key": "gram_leucocitos", "label": "Leucocitos/campo", "reference": "0-5/campo", "optional": True},
    {"key": "gram_microorganismos", "label": "Microorganismos observados", "optional": True},
    {"key": "observaciones", "label": "Observaciones", "type": "text_area", "optional": True}
]

CONST_CORPUSCULAR_FIELDS = [
    {"key": "vcm", "label": "VCM", "unit": "fL", "reference": "RN: 95-120 | Niños: 70-86 | Adultos: 80-96", "placeholder": "Ej. 88"},
    {"key": "hcm", "label": "HCM", "unit": "pg", "reference": "RN: 31-37 | Niños: 24-32 | Adultos: 27-33", "placeholder": "Ej. 29"},
    {"key": "chcm", "label": "CHCM", "unit": "g/dL", "reference": "Niños y adultos: 32-36 g/dL", "placeholder": "Ej. 33"},
    {"key": "rdw", "label": "RDW", "unit": "%", "reference": "11.5-14.5 %", "placeholder": "Ej. 13.2"}
]

TOLERANCIA_GLUCO_FIELDS = [
    {"key": "glucosa_ayunas", "label": "Glucosa en ayunas", "unit": "mg/dL", "reference": "Normal <100 mg/dL | Gestante <95 mg/dL", "placeholder": "Ej. 92"},
    {"key": "glucosa_60", "label": "Glucosa 60 min", "unit": "mg/dL", "reference": "Normal <180 mg/dL", "placeholder": "Ej. 155"},
    {"key": "glucosa_120", "label": "Glucosa 120 min", "unit": "mg/dL", "reference": "Normal <140 mg/dL | Gestante <153 mg/dL", "placeholder": "Ej. 132"},
    {"key": "glucosa_180", "label": "Glucosa 180 min", "unit": "mg/dL", "reference": "<140 mg/dL", "optional": True, "placeholder": "Ej. 124"}
]

GASES_ARTERIALES_FIELDS = [
    {"key": "ph", "label": "pH", "reference": "RN: 7.30-7.40 | Adultos: 7.35-7.45", "placeholder": "Ej. 7.39"},
    {"key": "pco2", "label": "pCO₂", "unit": "mmHg", "reference": "RN: 27-40 | Adultos: 35-45", "placeholder": "Ej. 40"},
    {"key": "po2", "label": "pO₂", "unit": "mmHg", "reference": "RN: 50-70 | Adultos: 80-100", "placeholder": "Ej. 92"},
    {"key": "hco3", "label": "HCO₃⁻", "unit": "mmol/L", "reference": "RN: 20-26 | Adultos: 22-26", "placeholder": "Ej. 24"},
    {"key": "exceso_base", "label": "Exceso de bases", "unit": "mmol/L", "reference": "-2 a +2", "placeholder": "Ej. -1"},
    {"key": "saturacion", "label": "SatO₂", "unit": "%", "reference": "RN: 90-95 % | Adultos: 95-100 %", "placeholder": "Ej. 97"},
    {"key": "lactato", "label": "Lactato", "unit": "mmol/L", "reference": "0.5-1.6 mmol/L", "optional": True, "placeholder": "Ej. 1.1"}
]

UROCULTIVO_FIELDS = [
    {"key": "recuento", "label": "Recuento bacteriano", "unit": "UFC/mL", "reference": "<10^5 UFC/mL: sin significancia clínica"},
    {"key": "microorganismo", "label": "Microorganismo aislado", "reference": "Sin desarrollo significativo", "optional": True},
    {"key": "interpretacion", "label": "Interpretación", "type": "text_area", "optional": True, "placeholder": "Sensibilidad recomendada"}
]

COPROCULTIVO_FIELDS = [
    {"key": "microorganismos", "label": "Microorganismos aislados", "reference": "No se aíslan patógenos entéricos", "optional": True},
    {"key": "resultado", "label": "Resultado", "reference": "Flora intestinal normal", "optional": True},
    {"key": "observaciones", "label": "Observaciones", "type": "text_area", "optional": True}
]

EXAMEN_HONGOS_FIELDS = [
    {"type": "section", "label": "Examen directo con KOH"},
    {"key": "hifas", "label": "Hifas", "reference": "No se observan", "optional": True},
    {"key": "levaduras", "label": "Levaduras / blastosporas", "reference": "No se observan", "optional": True},
    {"key": "artroconidios", "label": "Artroconidios", "optional": True},
    {"key": "observaciones", "label": "Observaciones", "type": "text_area", "optional": True}
]

CONTENIDO_GASTRICO_FIELDS = [
    {"key": "volumen", "label": "Volumen residual", "unit": "mL", "reference": "<20 mL", "placeholder": "Ej. 12"},
    {"key": "ph", "label": "pH", "reference": "1.0-4.0", "placeholder": "Ej. 2.5"},
    {"key": "aspecto", "label": "Aspecto", "reference": "Translúcido o ligeramente verdoso", "optional": True},
    {"key": "observaciones", "label": "Observaciones", "type": "text_area", "optional": True}
]

GRUPO_RH_FIELDS = [
    {"key": "grupo_abo", "label": "Grupo ABO", "type": "choice", "choices": ["O", "A", "B", "AB"], "reference": "Reportar fenotipo ABO"},
    {"key": "factor_rh", "label": "Factor Rh", "type": "choice", "choices": ["Positivo", "Negativo"], "reference": "Factor Rh(D)"},
    {"key": "observaciones", "label": "Observaciones", "type": "text_area", "optional": True}
]

WIDAL_FIELDS = [
    {"key": "antigeno_o", "label": "Antígeno O", "reference": "Negativo: <1:80"},
    {"key": "antigeno_h", "label": "Antígeno H", "reference": "Negativo: <1:160"},
    {"key": "antigeno_ah", "label": "Antígeno AH", "reference": "Negativo: <1:80", "optional": True},
    {"key": "antigeno_bh", "label": "Antígeno BH", "reference": "Negativo: <1:80", "optional": True},
    {"key": "observaciones", "label": "Observaciones", "type": "text_area", "optional": True}
]

def build_sample_tracking_template(reference_note):
    return {
        "fields": [
            {"key": "hora_toma", "label": "Hora de toma/envío", "placeholder": "HH:MM", "reference": "Registrar hora oficial de la toma"},
            {"key": "destino", "label": "Destino / referencia", "optional": True, "placeholder": "Ej. Laboratorio de referencia"},
            {"key": "observaciones", "label": "Observaciones", "type": "text_area", "optional": True, "reference": reference_note}
        ]
    }

TEST_TEMPLATES = {
    "Hemograma manual": {
        "fields": copy.deepcopy(HEMOGRAM_BASE_FIELDS),
        "auto_calculations": [
            {
                "source": "hematocrito",
                "target": "hemoglobina",
                "operation": "divide",
                "operand": 3.03,
                "decimals": 2,
                "description": "Hb = Hto / 3.03 (cálculo automático)",
            }
        ]
    },
    "Hemograma automatizado": {
        "fields": copy.deepcopy(HEMOGRAM_BASE_FIELDS),
        "auto_calculations": [
            {
                "source": "hematocrito",
                "target": "hemoglobina",
                "operation": "divide",
                "operand": 3.03,
                "decimals": 2,
                "description": "Hb = Hto / 3.03 (cálculo automático)",
            }
        ]
    },
    "Examen completo de orina": {"fields": copy.deepcopy(URINE_BASE_FIELDS)},
    "Sedimento urinario": {"fields": copy.deepcopy(SEDIMENTO_FIELDS)},
    "Examen coprológico (directo)": {"fields": copy.deepcopy(COPRO_DIRECT_FIELDS)},
    "Examen coprológico (concentración)": {"fields": copy.deepcopy(COPRO_CONCENT_FIELDS)},
    "Coloración de Gram": {"fields": copy.deepcopy(GRAM_FIELDS)},
    "Reacción inflamatoria": {"fields": copy.deepcopy(REACTION_FIELDS)},
    "Test de aminas": {
        "fields": [
            {"key": "resultado", "label": "Resultado", "type": "bool", "positive_text": "Positivo", "negative_text": "Negativo", "reference": "Negativo"},
            {"key": "olor_caracteristico", "label": "Olor característico", "optional": True},
            {"key": "observaciones", "label": "Observaciones", "type": "text_area", "optional": True}
        ]
    },
    "Test de Helecho": {
        "fields": [
            {"key": "resultado", "label": "Resultado", "type": "bool", "positive_text": "Positivo", "negative_text": "Negativo", "reference": "Patrón negativo"},
            {"key": "observaciones", "label": "Observaciones", "type": "text_area", "optional": True}
        ]
    },
    "Secreción vaginal": {"fields": copy.deepcopy(SECRECION_VAGINAL_FIELDS)},
    "Secreción (otros sitios)": {"fields": copy.deepcopy(SECRECION_GENERAL_FIELDS)},
    "Constantes corpusculares": {"fields": copy.deepcopy(CONST_CORPUSCULAR_FIELDS)},
    "Tolerancia a la glucosa": {"fields": copy.deepcopy(TOLERANCIA_GLUCO_FIELDS)},
    "Gases arteriales": {"fields": copy.deepcopy(GASES_ARTERIALES_FIELDS)},
    "Urocultivo": {"fields": copy.deepcopy(UROCULTIVO_FIELDS)},
    "Coprocultivo": {"fields": copy.deepcopy(COPROCULTIVO_FIELDS)},
    "Examen directo (hongos/KOH)": {"fields": copy.deepcopy(EXAMEN_HONGOS_FIELDS)},
    "Contenido gástrico (en RN)": {"fields": copy.deepcopy(CONTENIDO_GASTRICO_FIELDS)},
    "Grupo sanguíneo y Factor Rh": {"fields": copy.deepcopy(GRUPO_RH_FIELDS)},
    "Reacción de Widal": {"fields": copy.deepcopy(WIDAL_FIELDS)}
}

SIMPLE_NUMERIC_TESTS = {
    "Hemoglobina": {
        "key": "hemoglobina",
        "label": "Hemoglobina",
        "unit": "g/dL",
        "reference": (
            "RN: 14.0-24.0 g/dL\n"
            "1-12 meses: 10.0-12.5 g/dL\n"
            "Niños 1-12 años: 11.5-15.5 g/dL\n"
            "Mujeres adultas: 12.0-16.0 g/dL\n"
            "Hombres adultos: 13.5-17.5 g/dL\n"
            "Gestantes (2°-3° trim): ≥11.0 g/dL"
        ),
        "placeholder": "Ej. 13.8"
    },
    "Recuento de leucocitos": {
        "key": "leucocitos_totales",
        "label": "Leucocitos",
        "unit": "/µL",
        "reference": (
            "RN: 9 000-30 000 /µL\n"
            "Niños 1-6 años: 5 000-15 500 /µL\n"
            "Adultos: 4 500-11 000 /µL"
        ),
        "placeholder": "Ej. 8 200"
    },
    "Recuento de hematíes": {
        "key": "eritrocitos_totales",
        "label": "Recuento de hematíes",
        "unit": "millones/µL",
        "reference": (
            "RN: 4.1-6.1 millones/µL\n"
            "Niños 1-10 años: 3.9-5.3 millones/µL\n"
            "Hombres adultos: 4.5-6.0 millones/µL\n"
            "Mujeres adultas: 4.0-5.4 millones/µL"
        ),
        "placeholder": "Ej. 4.7"
    },
    "Recuento de plaquetas": {
        "key": "plaquetas_totales",
        "label": "Plaquetas",
        "unit": "/µL",
        "reference": "RN y niños: 150 000-450 000 /µL | Adultos: 150 000-400 000 /µL",
        "placeholder": "Ej. 210 000"
    },
    "Tiempo de coagulación": {
        "key": "tiempo_coagulacion",
        "label": "Tiempo de coagulación",
        "unit": "min",
        "reference": "Adultos: 8-12 min (Lee-White) | Niños: 6-11 min",
        "placeholder": "Ej. 9"
    },
    "Tiempo de sangría": {
        "key": "tiempo_sangria",
        "label": "Tiempo de sangría",
        "unit": "min",
        "reference": "Mujeres: 2-7 min | Hombres: 2-6 min",
        "placeholder": "Ej. 3"
    },
    "Velocidad de sedimentación globular (VSG)": {
        "key": "vsg",
        "label": "VSG",
        "unit": "mm/h",
        "reference": (
            "Hombres <50 a: 0-15 mm/h | Hombres ≥50 a: 0-20 mm/h\n"
            "Mujeres <50 a: 0-20 mm/h | Mujeres ≥50 a: 0-30 mm/h\n"
            "Niños: 0-10 mm/h"
        ),
        "placeholder": "Ej. 12"
    },
    "Glucosa": {
        "key": "glucosa",
        "label": "Glucosa en ayunas",
        "unit": "mg/dL",
        "reference": "Niños y adultos: 70-99 mg/dL | Gestantes: <95 mg/dL",
        "placeholder": "Ej. 88"
    },
    "Glucosa postprandial": {
        "key": "glucosa_postprandial",
        "label": "Glucosa 2 h postprandial",
        "unit": "mg/dL",
        "reference": "Niños y adultos: <140 mg/dL | Gestantes: <120 mg/dL",
        "placeholder": "Ej. 128"
    },
    "Colesterol Total": {
        "key": "colesterol_total",
        "label": "Colesterol total",
        "unit": "mg/dL",
        "reference": "Adultos: <200 mg/dL (deseable) | Niños: <170 mg/dL",
        "placeholder": "Ej. 185"
    },
    "Triglicéridos": {
        "key": "trigliceridos",
        "label": "Triglicéridos",
        "unit": "mg/dL",
        "reference": "Niños <9 a: <100 mg/dL | 10-19 a: <130 mg/dL | Adultos: <150 mg/dL",
        "placeholder": "Ej. 135"
    },
    "Colesterol HDL": {
        "key": "hdl",
        "label": "Colesterol HDL",
        "unit": "mg/dL",
        "reference": "Varones: ≥40 mg/dL | Mujeres: ≥50 mg/dL | Niños: ≥45 mg/dL",
        "placeholder": "Ej. 52"
    },
    "Colesterol LDL": {
        "key": "ldl",
        "label": "Colesterol LDL",
        "unit": "mg/dL",
        "reference": "Niños: <110 mg/dL | Adultos: <100 mg/dL (óptimo)",
        "placeholder": "Ej. 98"
    },
    "Transaminasa Glutámico Oxalacética (TGO)": {
        "key": "tgo",
        "label": "TGO (AST)",
        "unit": "U/L",
        "reference": "RN: <75 U/L | Niños: <50 U/L | Adultos: 10-40 U/L",
        "placeholder": "Ej. 28"
    },
    "Transaminasa Glutámico Pirúvico (TGP)": {
        "key": "tgp",
        "label": "TGP (ALT)",
        "unit": "U/L",
        "reference": "RN: <60 U/L | Niños: <40 U/L | Adultos: 7-45 U/L",
        "placeholder": "Ej. 32"
    },
    "Bilirrubina Total": {
        "key": "bilirrubina_total",
        "label": "Bilirrubina total",
        "unit": "mg/dL",
        "reference": "Adultos: 0.3-1.2 mg/dL | RN 24 h: <6 mg/dL | RN 48 h: <10 mg/dL",
        "placeholder": "Ej. 0.8"
    },
    "Bilirrubina Directa": {
        "key": "bilirrubina_directa",
        "label": "Bilirrubina directa",
        "unit": "mg/dL",
        "reference": "Adultos: 0.0-0.3 mg/dL | RN: <0.5 mg/dL",
        "placeholder": "Ej. 0.2"
    },
    "Úrea": {
        "key": "urea",
        "label": "Úrea",
        "unit": "mg/dL",
        "reference": "RN: 3-12 mg/dL | Niños: 5-18 mg/dL | Adultos: 15-40 mg/dL",
        "placeholder": "Ej. 28"
    },
    "Creatinina": {
        "key": "creatinina",
        "label": "Creatinina",
        "unit": "mg/dL",
        "reference": "RN: 0.3-1.0 mg/dL | Niños: 0.2-0.7 mg/dL | Mujeres: 0.5-0.9 mg/dL | Hombres: 0.7-1.3 mg/dL",
        "placeholder": "Ej. 0.9"
    },
    "Proteína de 24 horas": {
        "key": "proteina_24h",
        "label": "Proteína 24 h",
        "unit": "mg/24h",
        "reference": "Adultos: <150 mg/24h | Gestantes: <300 mg/24h",
        "placeholder": "Ej. 120"
    },
    "Fosfatasa alcalina": {
        "key": "fosfatasa_alcalina",
        "label": "Fosfatasa alcalina",
        "unit": "U/L",
        "reference": "Niños: 150-380 U/L | Adultos: 44-147 U/L | Gestantes 3er trim: <240 U/L",
        "placeholder": "Ej. 110"
    },
    "Ácido úrico": {
        "key": "acido_urico",
        "label": "Ácido úrico",
        "unit": "mg/dL",
        "reference": "Niños: 2.0-5.5 mg/dL | Mujeres: 2.4-6.0 mg/dL | Hombres: 3.4-7.0 mg/dL",
        "placeholder": "Ej. 4.8"
    },
    "Proteínas Totales": {
        "key": "proteinas_totales",
        "label": "Proteínas totales",
        "unit": "g/dL",
        "reference": "RN: 4.6-7.4 g/dL | Niños: 6.0-8.0 g/dL | Adultos: 6.4-8.3 g/dL",
        "placeholder": "Ej. 7.1"
    },
    "Albúmina": {
        "key": "albumina",
        "label": "Albúmina",
        "unit": "g/dL",
        "reference": "RN: 2.8-4.4 g/dL | Niños: 3.5-5.5 g/dL | Adultos: 3.5-5.2 g/dL | Gestantes: 2.8-4.5 g/dL",
        "placeholder": "Ej. 4.0"
    },
    "Amilasa": {
        "key": "amilasa",
        "label": "Amilasa",
        "unit": "U/L",
        "reference": "RN: 6-65 U/L | Niños: 30-90 U/L | Adultos: 28-100 U/L",
        "placeholder": "Ej. 62"
    },
    "Lipasa": {
        "key": "lipasa",
        "label": "Lipasa",
        "unit": "U/L",
        "reference": "RN: 6-51 U/L | Niños: 10-140 U/L | Adultos: 13-60 U/L",
        "placeholder": "Ej. 45"
    },
    "Gamma Glutamil transferasa (GGT)": {
        "key": "ggt",
        "label": "GGT",
        "unit": "U/L",
        "reference": "RN: 12-73 U/L | Niños: 12-43 U/L | Mujeres: 7-32 U/L | Hombres: 10-50 U/L",
        "placeholder": "Ej. 24"
    },
    "Globulina": {
        "key": "globulina",
        "label": "Globulina",
        "unit": "g/dL",
        "reference": "Niños: 2.0-3.5 g/dL | Adultos: 2.3-3.5 g/dL",
        "placeholder": "Ej. 2.7"
    },
    "Ferritina": {
        "key": "ferritina",
        "label": "Ferritina",
        "unit": "ng/mL",
        "reference": (
            "RN: 25-200 ng/mL\n"
            "Niños 1-5 a: 10-60 ng/mL | Niños 6-15 a: 7-140 ng/mL\n"
            "Hombres adultos: 30-400 ng/mL\n"
            "Mujeres adultas: 15-150 ng/mL\n"
            "Gestantes: 1T 10-150 | 2T 6-74 | 3T 2-40 ng/mL"
        ),
        "placeholder": "Ej. 55"
    },
    "Hemoglobina glicosilada": {
        "key": "hba1c",
        "label": "HbA1c",
        "unit": "%",
        "reference": "Normal <5.7 % | Prediabetes 5.7-6.4 % | Diabetes ≥6.5 % | Gestantes con diabetes: meta <6.0 %",
        "placeholder": "Ej. 5.6"
    },
    "Factor reumatoideo": {
        "key": "factor_reumatoideo",
        "label": "Factor reumatoideo",
        "unit": "UI/mL",
        "reference": "Adultos: <14 UI/mL | Niños: <10 UI/mL",
        "placeholder": "Ej. 8"
    },
    "PCR cuantitativo": {
        "key": "proteina_c",
        "label": "Proteína C reactiva",
        "unit": "mg/L",
        "reference": "Adultos: <5 mg/L | RN: <10 mg/L",
        "placeholder": "Ej. 3.2"
    },
    "ASO": {
        "key": "aso",
        "label": "Antiestreptolisinas (ASO)",
        "unit": "UI/mL",
        "reference": "Adultos: <200 UI/mL | Niños: <250 UI/mL",
        "placeholder": "Ej. 120"
    },
    "PSA (ELISA)": {
        "key": "psa",
        "label": "PSA total",
        "unit": "ng/mL",
        "reference": "40-49 a: <2.5 | 50-59 a: <3.5 | 60-69 a: <4.5 | ≥70 a: <6.5 ng/mL",
        "placeholder": "Ej. 2.1"
    }
}

SIMPLE_TEXTAREA_TESTS = {
    "Lámina periférica": {
        "key": "descripcion",
        "label": "Descripción morfológica",
        "reference": "Eritrocitos normocíticos normocrómicos, leucocitos sin alteraciones, plaquetas adecuadas",
        "placeholder": "Describa morfología observada"
    },
    "Identificación bioquímica": {
        "key": "panel_bioquimico",
        "label": "Perfil bioquímico",
        "reference": "Describa pruebas realizadas según manual CLSI vigente",
        "placeholder": "Ej. Enterobacter cloacae, panel API 20E"
    },
    "Antibiograma": {
        "key": "antibiograma",
        "label": "Antibiograma",
        "reference": "Interpretar según guías CLSI/EUCAST",
        "placeholder": "Antibiótico - Interpretación (S/I/R)"
    }
}

BOOL_TESTS = {
    "Células LE": {"positive_text": "Positivo", "negative_text": "Negativo", "reference": "Negativo"},
    "Baciloscopía": {"positive_text": "BAAR positivo", "negative_text": "BAAR negativo", "reference": "No se observan bacilos ácido-alcohol resistentes"},
    "Gota gruesa": {"positive_text": "Hemoparásitos", "negative_text": "No se observan", "reference": "No se observan Plasmodium spp."},
    "Frotis para Leishmaniasis": {"positive_text": "Leishmania sp.", "negative_text": "No se observan", "reference": "No se observan amastigotes"},
    "Cultivo de Neisseria gonorrhoeae": {"positive_text": "Aislamiento positivo", "negative_text": "Sin aislamiento", "reference": "No se aisla N. gonorrhoeae"},
    "Cultivo de Campylobacter spp.": {"positive_text": "Aislamiento positivo", "negative_text": "Sin aislamiento", "reference": "No se aisla Campylobacter spp."},
    "Frotis para Bartonella": {"positive_text": "Cuerpos de Bartonella", "negative_text": "No se observan", "reference": "Negativo"},
    "Test de Graham": {"positive_text": "Huevos presentes", "negative_text": "No se observan", "reference": "Sin huevos de Enterobius vermicularis"},
    "Ácido sulfasalicílico al 3%": {"positive_text": "Positivo", "negative_text": "Negativo", "reference": "Negativo (proteínas ≤30 mg/dL)"},
    "Antígeno de superficie Hepatitis B (HBsAg)": {
        "positive_text": "Reactivo",
        "negative_text": "No reactivo",
        "reference": "No reactivo"
    },
    "Reagina plasmática rápida (RPR)": {
        "positive_text": "Reactivo",
        "negative_text": "No reactivo",
        "reference": "No reactivo"
    },
    "Proteína C reactiva (PCR) - Látex": {"positive_text": "Reactivo", "negative_text": "No reactivo", "reference": "No reactivo"},
    "BHCG (Prueba de embarazo en sangre)": {"positive_text": "Positivo", "negative_text": "Negativo", "reference": "Negativo (<5 mUI/mL)"}
}

SAMPLE_TEMPLATES = {
    "Leishmaniasis (toma de muestra)": build_sample_tracking_template("Registro de remisión según NTS para vigilancia de leishmaniasis"),
    "Dengue (toma de muestra)": build_sample_tracking_template("Mantener cadena de frío 2-8 °C"),
    "Leptospirosis (toma de muestra)": build_sample_tracking_template("Documentar envío a laboratorio de referencia"),
    "Covid-19 (hisopado nasofaríngeo)": build_sample_tracking_template("Remitir en medio viral a 4 °C"),
    "Carga viral de VIH / Recuento de CD4": build_sample_tracking_template("Registrar código de envío y hora"),
    "CLIA (PSA, Perfil tiroideo, etc.)": build_sample_tracking_template("Sin valores de referencia: registro de muestra derivada"),
    "Sangre venosa/arterial (examen de proceso)": build_sample_tracking_template("Control de cadena de custodia (sin valores analíticos)"),
    "Covid-19 (Prueba antigénica)": build_bool_observation_template("Positivo", "Negativo", "Negativo"),
    "Covid-19 (Prueba serológica)": build_bool_observation_template("Positivo", "Negativo", "Negativo"),
    "Dengue NS1/IgM/IgG (Prueba rápida)": build_bool_observation_template("Positivo", "Negativo", "Negativo"),
    "Hepatitis A (Prueba rápida)": build_bool_observation_template("Positivo", "Negativo", "Negativo"),
    "Hepatitis B (Prueba rápida)": build_bool_observation_template("Positivo", "Negativo", "Negativo"),
    "PSA (Prueba rápida)": build_bool_observation_template("Positivo", "Negativo", "Negativo"),
    "Sangre oculta en heces (Prueba rápida)": build_bool_observation_template("Positivo", "Negativo", "Negativo"),
    "Helicobacter pylori (Prueba rápida)": build_bool_observation_template("Positivo", "Negativo", "Negativo"),
    "VIH (Prueba rápida)": build_bool_observation_template("Reactivo", "No reactivo", "No reactivo"),
    "Sífilis (Prueba rápida)": build_bool_observation_template("Reactivo", "No reactivo", "No reactivo"),
    "VIH/Sífilis (Prueba combinada)": build_bool_observation_template("Reactivo", "No reactivo", "No reactivo"),
    "BHCG (Prueba de embarazo en sangre)": build_bool_observation_template("Positivo", "Negativo", "Negativo (<5 mUI/mL)")
}

for test_name, info in SIMPLE_NUMERIC_TESTS.items():
    TEST_TEMPLATES[test_name] = build_single_value_template(
        info["key"],
        info.get("label", test_name),
        unit=info.get("unit"),
        reference=info.get("reference"),
        placeholder=info.get("placeholder"),
        helper=info.get("helper")
    )

for test_name, info in SIMPLE_TEXTAREA_TESTS.items():
    TEST_TEMPLATES[test_name] = build_single_value_template(
        info["key"],
        info.get("label", test_name),
        reference=info.get("reference"),
        placeholder=info.get("placeholder"),
        field_type="text_area"
    )

for test_name, params in BOOL_TESTS.items():
    TEST_TEMPLATES[test_name] = build_bool_observation_template(
        params.get("positive_text", "Positivo"),
        params.get("negative_text", "Negativo"),
        params.get("reference", "Negativo")
    )

for test_name, template in SAMPLE_TEMPLATES.items():
    TEST_TEMPLATES[test_name] = copy.deepcopy(template)

# Plantilla base para Hematocrito sin cálculo automático
HEMATOCRIT_BASE_TEMPLATE = build_single_value_template(
    "hematocrito",
    "Hematocrito",
    unit="%",
    reference=(
        "RN: 44-65 %\n"
        "Niños 1-10 a: 35-45 %\n"
        "Hombres adultos: 40-54 %\n"
        "Mujeres adultas: 36-47 %\n"
        "Gestantes (2°-3° trim): 33-43 %"
    ),
    placeholder="Ej. 43"
)
TEST_TEMPLATES["Hematocrito"] = copy.deepcopy(HEMATOCRIT_BASE_TEMPLATE)


def build_hematocrit_template(include_auto_hemoglobin=False):
    template = copy.deepcopy(HEMATOCRIT_BASE_TEMPLATE)
    fields = copy.deepcopy(HEMATOCRIT_BASE_TEMPLATE.get("fields", []))
    if include_auto_hemoglobin:
        hb_reference = SIMPLE_NUMERIC_TESTS.get("Hemoglobina", {}).get("reference")
        fields.append(
            {
                "key": "hemoglobina",
                "label": "Hemoglobina (estimada)",
                "unit": "g/dL",
                "reference": hb_reference,
                "placeholder": "Calculada automáticamente"
            }
        )
        template["auto_calculations"] = [
            {
                "source": "hematocrito",
                "target": "hemoglobina",
                "operation": "divide",
                "operand": 3.03,
                "decimals": 2,
                "description": "Hb estimada = Hto / 3.03 (solo cuando se solicita Hematocrito)",
                "clear_on_invalid": True
            }
        ]
    template["fields"] = fields
    return template

RAPID_TEST_NAMES = [
    "BHCG (Prueba de embarazo en sangre)",
    "VIH (Prueba rápida)",
    "Sífilis (Prueba rápida)",
    "VIH/Sífilis (Prueba combinada)",
    "Hepatitis A (Prueba rápida)",
    "Hepatitis B (Prueba rápida)",
    "PSA (Prueba rápida)",
    "Sangre oculta en heces (Prueba rápida)",
    "Helicobacter pylori (Prueba rápida)",
    "Covid-19 (Prueba antigénica)",
    "Covid-19 (Prueba serológica)",
    "Dengue NS1/IgM/IgG (Prueba rápida)"
]

for rapid_test in RAPID_TEST_NAMES:
    if rapid_test not in TEST_TEMPLATES:
        TEST_TEMPLATES[rapid_test] = build_bool_observation_template()



class AddTestsDialog(QDialog):
    def __init__(self, tests, disabled_tests=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Agregar pruebas a la orden")
        self.setMinimumSize(420, 480)
        layout = QVBoxLayout(self)
        description = QLabel("Seleccione las pruebas adicionales que desea agregar a la orden actual.")
        description.setWordWrap(True)
        layout.addWidget(description)
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.MultiSelection)
        disabled_set = set(disabled_tests or [])
        for name, category in tests:
            display_text = f"{name} ({category})" if category else name
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, name)
            if name in disabled_set:
                item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
                item.setText(f"{display_text} — ya incluido")
            self.list_widget.addItem(item)
        layout.addWidget(self.list_widget)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_selected_tests(self):
        return [item.data(Qt.UserRole) for item in self.list_widget.selectedItems() if item.flags() & Qt.ItemIsEnabled]


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
        self.order_fields = {}        # Campos de resultado dinámicos por examen
        self.selected_order_id = None # Orden seleccionada actualmente en resultados
        self.last_order_registered = None  # Última orden registrada (para enlace rápido a resultados)
        self.pending_orders_cache = []    # Lista cacheada de órdenes pendientes para facilitar filtros
        self.completed_orders_cache = []  # Lista cacheada de órdenes completadas
        self._activity_cache = {"data": [], "description": "", "start": None, "end": None}
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
            self.input_first_name.setText((first_name or "").upper()); self.input_last_name.setText((last_name or "").upper())
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
        first_name = self.input_first_name.text().strip().upper()
        last_name = self.input_last_name.text().strip().upper()
        self.input_first_name.setText(first_name)
        self.input_last_name.setText(last_name)
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
            self._select_order_in_combo(self.combo_orders, self.last_order_registered)
            self.load_order_fields()
    def init_resultados_page(self):
        layout = QVBoxLayout(self.page_resultados)
        search_layout = QHBoxLayout()
        search_label = QLabel("Buscar:")
        self.order_search_input = QLineEdit()
        self.order_search_input.setPlaceholderText("Nombre, documento o # de orden")
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.order_search_input, 1)
        sort_label = QLabel("Ordenar:")
        self.pending_sort_combo = QComboBox()
        self.pending_sort_combo.addItems([
            "Fecha (recientes primero)",
            "Fecha (antiguas primero)",
            "Número de orden (descendente)",
            "Número de orden (ascendente)"
        ])
        search_layout.addWidget(sort_label)
        search_layout.addWidget(self.pending_sort_combo)
        search_layout.addStretch()
        layout.addLayout(search_layout)
        top_layout = QHBoxLayout()
        lbl = QLabel("Orden pendiente:")
        self.combo_orders = QComboBox()
        self.combo_orders.setMinimumWidth(350)
        btn_load = QPushButton("Cargar")
        top_layout.addWidget(lbl)
        top_layout.addWidget(self.combo_orders)
        top_layout.addWidget(btn_load)
        layout.addLayout(top_layout)
        # Área scrollable para campos de resultados
        self.results_area = QScrollArea()
        self.results_area.setWidgetResizable(True)
        self.results_container = QWidget()
        self.results_layout = QVBoxLayout(self.results_container)
        self.results_layout.setContentsMargins(10, 10, 10, 10)
        self.results_layout.setSpacing(14)
        self.results_area.setWidget(self.results_container)
        layout.addWidget(self.results_area)
        btn_save = QPushButton("Guardar Resultados")
        layout.addWidget(btn_save)
        btn_load.clicked.connect(self.load_order_fields)
        btn_save.clicked.connect(self.save_results)
        self.order_search_input.textChanged.connect(self.filter_pending_orders)
        self.pending_sort_combo.currentIndexChanged.connect(
            lambda: self.filter_pending_orders(self.order_search_input.text(), prefer_order=self.selected_order_id)
        )
    def populate_pending_orders(self):
        # Llenar combo de órdenes pendientes (no completadas)
        pending = self.labdb.get_pending_orders()
        self.pending_orders_cache = []
        for row in pending:
            oid, first, last, date, doc_type, doc_number = row
            self.pending_orders_cache.append({
                "id": oid,
                "first_name": (first or "").upper(),
                "last_name": (last or "").upper(),
                "date": date,
                "doc_type": doc_type or "",
                "doc_number": doc_number or ""
            })
        search_text = self.order_search_input.text() if hasattr(self, 'order_search_input') else ""
        prefer_id = self.selected_order_id or self.last_order_registered
        self.filter_pending_orders(search_text, prefer_order=prefer_id)
    def filter_pending_orders(self, text="", prefer_order=None):
        if not hasattr(self, 'combo_orders'):
            return
        filter_text = (text or "").strip().lower()
        current_data = self.combo_orders.currentData()
        self.combo_orders.blockSignals(True)
        self.combo_orders.clear()
        orders = getattr(self, 'pending_orders_cache', [])
        filtered_orders = []
        for order in orders:
            search_blob = " ".join([
                str(order['id']),
                order['first_name'] or "",
                order['last_name'] or "",
                order['doc_type'] or "",
                order['doc_number'] or "",
                order['date'] or ""
            ]).lower()
            if filter_text in search_blob:
                filtered_orders.append(order)
        sort_mode = self.pending_sort_combo.currentIndex() if hasattr(self, 'pending_sort_combo') else 0
        sorted_orders = self._sort_orders(filtered_orders, sort_mode)
        matching_ids = [order['id'] for order in sorted_orders]
        for order in sorted_orders:
            display = self._format_order_display(order)
            self.combo_orders.addItem(display, order['id'])
        if not matching_ids:
            self.combo_orders.addItem("(No hay órdenes pendientes)", None)
        self.combo_orders.blockSignals(False)
        target_candidates = [
            prefer_order,
            current_data,
            self.selected_order_id,
            self.last_order_registered
        ]
        selected = None
        for candidate in target_candidates:
            if candidate is not None and candidate in matching_ids:
                selected = candidate
                break
        if selected is not None:
            self._select_order_in_combo(self.combo_orders, selected)
        else:
            self.combo_orders.setCurrentIndex(0)
    def _format_order_display(self, order):
        doc_type = order.get('doc_type') or ""
        doc_number = order.get('doc_number') or ""
        doc_text = f" ({doc_type} {doc_number})" if doc_type and doc_number else ""
        first = (order.get('first_name') or "").upper()
        last = (order.get('last_name') or "").upper()
        name_text = (f"{first} {last}").strip()
        status_tag = ""
        if 'emitted' in order:
            status_tag = " [EMITIDO]" if order.get('emitted') else " [POR EMITIR]"
        return f"Orden #{order['id']} | {order['date']} | {name_text}{doc_text}{status_tag}"
    def _select_order_in_combo(self, combo, order_id):
        for idx in range(combo.count()):
            if combo.itemData(idx) == order_id:
                combo.setCurrentIndex(idx)
                return

    def _parse_order_datetime(self, order):
        date_str = order.get('date') if isinstance(order, dict) else None
        if not date_str:
            return datetime.datetime.min
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.datetime.strptime(date_str, fmt)
            except (ValueError, TypeError):
                continue
        return datetime.datetime.min

    def _sort_orders(self, orders, sort_mode):
        if not orders:
            return []
        if sort_mode == 0:  # Fecha descendente (recientes primero)
            return sorted(
                orders,
                key=lambda o: (self._parse_order_datetime(o), o.get('id', 0)),
                reverse=True
            )
        if sort_mode == 1:  # Fecha ascendente (antiguas primero)
            return sorted(
                orders,
                key=lambda o: (self._parse_order_datetime(o), o.get('id', 0))
            )
        if sort_mode == 2:  # Número de orden descendente
            return sorted(orders, key=lambda o: o.get('id', 0), reverse=True)
        # Número de orden ascendente (predeterminado restante)
        return sorted(orders, key=lambda o: o.get('id', 0))

    def _refresh_completed_combo(self, prefer_order=None):
        if not hasattr(self, 'combo_completed'):
            return
        current_data = self.combo_completed.currentData()
        orders = getattr(self, 'completed_orders_cache', [])
        sort_mode = self.completed_sort_combo.currentIndex() if hasattr(self, 'completed_sort_combo') else 0
        sorted_orders = self._sort_orders(orders, sort_mode)
        self.combo_completed.blockSignals(True)
        self.combo_completed.clear()
        if not sorted_orders:
            self.combo_completed.addItem("(No hay resultados)", None)
            self.combo_completed.blockSignals(False)
            self.combo_completed.setCurrentIndex(0)
            return
        for order in sorted_orders:
            self.combo_completed.addItem(self._format_order_display(order), order['id'])
        def normalize_candidate(candidate):
            try:
                return int(candidate)
            except (TypeError, ValueError):
                return None
        normalized_prefer = normalize_candidate(prefer_order)
        normalized_current = normalize_candidate(current_data)
        available_ids = {order['id'] for order in sorted_orders}
        target_candidates = [normalized_prefer, normalized_current]
        selected = None
        for candidate in target_candidates:
            if candidate is not None and candidate in available_ids:
                selected = candidate
                break
        if selected is not None:
            self._select_order_in_combo(self.combo_completed, selected)
        else:
            self.combo_completed.setCurrentIndex(0)
        self.combo_completed.blockSignals(False)
    def load_order_fields(self):
        # Cargar campos de resultado para la orden seleccionada
        self._clear_results_layout()
        self.order_fields.clear()
        data = self.combo_orders.currentData() if hasattr(self, 'combo_orders') else None
        if data is None:
            self.selected_order_id = None
            placeholder = QLabel("Seleccione una orden pendiente para registrar resultados.")
            placeholder.setStyleSheet("color: #555; font-style: italic;")
            placeholder.setWordWrap(True)
            self.results_layout.addWidget(placeholder)
            self.results_layout.addStretch()
            return
        order_id = int(data)
        self.selected_order_id = order_id
        # Consultar pruebas de esa orden
        self.labdb.cur.execute("""
            SELECT t.name, ot.result, t.category
            FROM order_tests ot
            JOIN tests t ON ot.test_id = t.id
            WHERE ot.order_id=?
        """, (order_id,))
        rows = self.labdb.cur.fetchall()
        if not rows:
            empty_label = QLabel("La orden seleccionada no tiene pruebas asociadas.")
            empty_label.setStyleSheet("color: #555; font-style: italic;")
            empty_label.setWordWrap(True)
            self.results_layout.addWidget(empty_label)
            self.results_layout.addStretch()
            return
        order_test_names = [name for name, _, _ in rows]
        for test_name, raw_result, category in rows:
            template = None
            template_name = test_name
            if test_name == "Hematocrito":
                auto_mode = self._should_auto_calculate_hb(order_test_names)
                template = build_hematocrit_template(auto_mode)
                if auto_mode:
                    template_name = "Hematocrito (automático)"
                    TEST_TEMPLATES[template_name] = copy.deepcopy(template)
            else:
                base_template = TEST_TEMPLATES.get(test_name)
                if base_template is not None:
                    template = copy.deepcopy(base_template)
                elif category == "PRUEBAS RÁPIDAS":
                    template = build_bool_observation_template()
                    TEST_TEMPLATES[test_name] = copy.deepcopy(template)
            group_box = QGroupBox(test_name)
            group_box.setStyleSheet("QGroupBox { font-weight: bold; }")
            group_layout = QFormLayout()
            group_layout.setLabelAlignment(Qt.AlignLeft)
            group_box.setLayout(group_layout)
            parsed = self._parse_stored_result(raw_result)
            existing_values = {}
            if parsed.get("type") == "structured":
                existing_values = parsed.get("values", {})
            field_entries = {}
            if template:
                for field_def in template.get("fields", []):
                    if field_def.get("type") == "section":
                        section_label = QLabel(field_def.get("label", ""))
                        section_label.setStyleSheet("font-weight: bold; color: #2c3e50; padding-top:4px;")
                        group_layout.addRow(section_label)
                        continue
                    label_text, field_widget, widget_info = self._create_structured_field(field_def, existing_values)
                    widget_info["definition"] = field_def
                    key = field_def.get("key")
                    if key:
                        field_entries[key] = widget_info
                    group_layout.addRow(f"{label_text}:", field_widget)
                self._apply_auto_calculations(field_entries, template)
                self.order_fields[test_name] = {
                    "template": template,
                    "template_name": template_name,
                    "fields": field_entries
                }
            else:
                default_value = ""
                if parsed.get("type") == "text":
                    default_value = parsed.get("value", "")
                elif parsed.get("type") == "structured":
                    default_value = self._structured_dict_to_text(parsed.get("values", {}))
                edit = QLineEdit()
                edit.setText(default_value)
                group_layout.addRow("Resultado:", edit)
                self.order_fields[test_name] = {
                    "template": None,
                    "fields": {
                        "__value__": {
                            "type": "line",
                            "widget": edit,
                            "definition": {"key": "__value__", "label": "Resultado"}
                        }
                    }
                }
            self.results_layout.addWidget(group_box)
        self.results_layout.addStretch()

    def _should_auto_calculate_hb(self, order_test_names):
        valid_names = [name for name in order_test_names if name]
        return valid_names.count("Hematocrito") == 1 and len(valid_names) == 1
    def save_results(self):
        # Guardar los resultados ingresados para la orden seleccionada
        if not self.selected_order_id:
            return
        results_dict = {}
        has_empty = False
        for test_name, info in self.order_fields.items():
            template = info.get("template")
            if template:
                values = {}
                for key, field_info in info["fields"].items():
                    value = self._get_widget_value(field_info)
                    values[key] = value
                    if value == "" and not field_info["definition"].get("optional", False):
                        has_empty = True
                results_dict[test_name] = {
                    "type": "structured",
                    "template": info.get("template_name", test_name),
                    "values": values
                }
            else:
                field_info = info["fields"].get("__value__")
                value = self._get_widget_value(field_info)
                results_dict[test_name] = value
                if value == "":
                    has_empty = True
        if has_empty:
            reply = QMessageBox.question(
                self,
                "Confirmar",
                "Hay pruebas o campos sin resultado. ¿Guardar de todos modos?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        completed = self.labdb.save_results(self.selected_order_id, results_dict)
        if completed:
            QMessageBox.information(self, "Completado", "Resultados guardados. Orden marcada como completada.")
            self.selected_order_id = None
            self.populate_pending_orders()
            self._clear_results_layout()
            msg = QLabel("Seleccione otra orden pendiente para continuar con la digitación de resultados.")
            msg.setStyleSheet("color: #555; font-style: italic;")
            msg.setWordWrap(True)
            self.results_layout.addWidget(msg)
            self.results_layout.addStretch()
        else:
            QMessageBox.information(self, "Guardado", "Resultados guardados (orden aún incompleta).")
            self.load_order_fields()
    def _clear_results_layout(self):
        if not hasattr(self, 'results_layout'):
            return
        while self.results_layout.count():
            item = self.results_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
    def _create_structured_field(self, field_def, existing_values):
        key = field_def.get("key")
        value = ""
        if key:
            value = existing_values.get(key, "")
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        widget_info = {"key": key, "container": container}
        field_type = field_def.get("type", "text")
        if field_type == "choice":
            combo = QComboBox()
            combo.addItems(field_def.get("choices", []))
            if value:
                idx = combo.findText(value)
                if idx >= 0:
                    combo.setCurrentIndex(idx)
                else:
                    combo.addItem(value)
                    combo.setCurrentIndex(combo.count() - 1)
            else:
                if combo.count():
                    combo.setCurrentIndex(-1)
            layout.addWidget(combo)
            widget_info.update({"type": "combo", "widget": combo})
        elif field_type == "bool":
            pos_text = field_def.get("positive_text", "Positivo")
            neg_text = field_def.get("negative_text", "Negativo")
            pos_radio = QRadioButton(pos_text)
            neg_radio = QRadioButton(neg_text)
            group = QButtonGroup(container)
            group.addButton(pos_radio)
            group.addButton(neg_radio)
            layout.addWidget(pos_radio)
            layout.addWidget(neg_radio)
            widget_info.update({
                "type": "bool",
                "group": group,
                "positive": pos_radio,
                "negative": neg_radio,
                "positive_text": pos_text,
                "negative_text": neg_text
            })
            if value:
                if value.lower() == pos_text.lower() or value.lower() == "positivo":
                    pos_radio.setChecked(True)
                elif value.lower() == neg_text.lower() or value.lower() == "negativo":
                    neg_radio.setChecked(True)
        elif field_type == "text_area":
            text_edit = QTextEdit()
            text_edit.setFixedHeight(field_def.get("height", 70))
            placeholder = field_def.get("placeholder")
            if placeholder:
                text_edit.setPlaceholderText(placeholder)
            if value:
                text_edit.setPlainText(value)
            layout.addWidget(text_edit)
            widget_info.update({"type": "text_area", "widget": text_edit})
        else:
            edit = QLineEdit()
            placeholder = field_def.get("placeholder")
            if placeholder:
                edit.setPlaceholderText(placeholder)
            if value:
                edit.setText(value)
            layout.addWidget(edit)
            widget_info.update({"type": "line", "widget": edit})
        unit = field_def.get("unit")
        if unit and field_type not in ("bool",):
            unit_label = QLabel(unit)
            unit_label.setStyleSheet("color: #555; font-size: 11px;")
            layout.addWidget(unit_label)
        reference = field_def.get("reference")
        if reference:
            ref_label = QLabel(f"Ref: {reference}")
            ref_label.setWordWrap(True)
            ref_label.setStyleSheet("color: #777; font-size: 11px;")
            layout.addWidget(ref_label)
        helper = field_def.get("helper")
        if helper:
            helper_label = QLabel(helper)
            helper_label.setWordWrap(True)
            helper_label.setStyleSheet("color: #0a84ff; font-size: 10px;")
            layout.addWidget(helper_label)
        layout.addStretch()
        widget_info["unit"] = unit
        widget_info["reference"] = reference
        return field_def.get("label", key or ""), container, widget_info
    def _apply_auto_calculations(self, field_entries, template):
        for calc in template.get("auto_calculations", []):
            self._setup_auto_calculation(field_entries, calc)
    def _setup_auto_calculation(self, field_entries, calc):
        source_key = calc.get("source")
        target_key = calc.get("target")
        if not source_key or not target_key:
            return
        source_info = field_entries.get(source_key)
        target_info = field_entries.get(target_key)
        if not source_info or not target_info:
            return
        if source_info.get("type") not in ("line",):
            return
        if target_info.get("type") not in ("line",):
            return
        source_widget = source_info.get("widget")
        target_widget = target_info.get("widget")
        if not source_widget or not target_widget:
            return
        operation = calc.get("operation")
        operand = calc.get("operand")
        decimals = calc.get("decimals", 2)
        only_if_empty = calc.get("only_if_empty", False)
        apply_on_load = calc.get("apply_on_load", True)
        description = calc.get("description")
        if description and not target_info.get("has_auto_helper"):
            container = target_info.get("container")
            if container and container.layout():
                helper_label = QLabel(description)
                helper_label.setWordWrap(True)
                helper_label.setStyleSheet("color: #0a84ff; font-size: 10px;")
                container.layout().addWidget(helper_label)
                target_info["has_auto_helper"] = True
        def on_change(text):
            value = self._to_float(text)
            if value is None:
                if calc.get("clear_on_invalid", False):
                    target_widget.blockSignals(True)
                    target_widget.clear()
                    target_widget.blockSignals(False)
                return
            result = None
            if operation == "divide":
                if operand in (0, None):
                    return
                result = value / operand
            elif operation == "multiply" and operand is not None:
                result = value * operand
            elif operation == "add" and operand is not None:
                result = value + operand
            elif operation == "subtract" and operand is not None:
                result = value - operand
            if result is None:
                return
            if only_if_empty and target_widget.text().strip():
                return
            if target_widget.hasFocus() and not calc.get("update_while_editing", False):
                return
            if decimals is not None:
                formatted = f"{result:.{decimals}f}".rstrip('0').rstrip('.')
            else:
                formatted = str(result)
            target_widget.blockSignals(True)
            target_widget.setText(formatted)
            target_widget.blockSignals(False)
        source_widget.textChanged.connect(on_change)
        if apply_on_load:
            on_change(source_widget.text())
    def _structured_dict_to_text(self, values):
        if not isinstance(values, dict):
            return ""
        parts = []
        for key, val in values.items():
            if val:
                parts.append(f"{key}: {val}")
        return "; ".join(parts)
    def _parse_stored_result(self, raw_result):
        if isinstance(raw_result, dict):
            return raw_result
        if raw_result in (None, ""):
            return {"type": "text", "value": ""}
        try:
            data = json.loads(raw_result)
        except (TypeError, json.JSONDecodeError):
            return {"type": "text", "value": raw_result}
        if isinstance(data, dict) and data.get("type") == "structured":
            return data
        return {"type": "text", "value": raw_result if raw_result is not None else ""}
    def _get_widget_value(self, field_info):
        if not field_info:
            return ""
        field_type = field_info.get("type")
        if field_type == "line":
            widget = field_info.get("widget")
            return widget.text().strip() if widget else ""
        if field_type == "text_area":
            widget = field_info.get("widget")
            return widget.toPlainText().strip() if widget else ""
        if field_type == "combo":
            widget = field_info.get("widget")
            return widget.currentText().strip() if widget else ""
        if field_type == "bool":
            if field_info.get("positive") and field_info["positive"].isChecked():
                return field_info.get("positive_text", "Positivo")
            if field_info.get("negative") and field_info["negative"].isChecked():
                return field_info.get("negative_text", "Negativo")
            return ""
        return ""
    def _to_float(self, text):
        if text in (None, ""):
            return None
        try:
            return float(str(text).replace(',', '.'))
        except ValueError:
            return None
    def _format_result_lines(self, test_name, raw_result):
        parsed = self._parse_stored_result(raw_result)
        template = TEST_TEMPLATES.get(test_name)
        if parsed.get("type") == "structured" and template:
            values = parsed.get("values", {})
            lines = [f"{test_name}:"]
            for field_def in template.get("fields", []):
                if field_def.get("type") == "section":
                    section_label = field_def.get("label", "")
                    if section_label:
                        lines.append(f"  {section_label}:")
                    continue
                key = field_def.get("key")
                if not key:
                    continue
                value = values.get(key, "")
                if isinstance(value, str):
                    display_value = " ".join(value.splitlines()).strip()
                else:
                    display_value = value
                if display_value in (None, ""):
                    display_value = "-"
                unit = field_def.get("unit")
                field_type = field_def.get("type")
                if unit and display_value not in ("-", "") and field_type not in ("bool", "text_area", "choice"):
                    display_text = str(display_value)
                    if not display_text.endswith(unit):
                        display_value = f"{display_text} {unit}"
                reference = field_def.get("reference")
                label = field_def.get("label", key)
                bullet = f"  • {label}: {display_value}"
                if reference:
                    bullet += f" (Ref: {reference})"
                lines.append(bullet)
            return lines
        text_value = parsed.get("value", raw_result or "")
        if isinstance(text_value, str):
            text_value = text_value.strip()
        if text_value == "":
            text_value = "-"
        return [f"{test_name}: {text_value}"]
    def _format_result_for_export(self, test_name, raw_result):
        lines = self._format_result_lines(test_name, raw_result)
        if len(lines) <= 1:
            line = lines[0]
            parts = line.split(": ", 1)
            return parts[1] if len(parts) > 1 else line
        cleaned = []
        for line in lines[1:]:
            stripped = line.strip()
            if stripped.endswith(":") and "•" not in stripped:
                continue
            cleaned.append(stripped.replace("• ", ""))
        return " | ".join(cleaned)
    def _calculate_age_years(self, patient_info, order_info):
        age_value = order_info.get('age_years') if isinstance(order_info, dict) else None
        if age_value is not None:
            try:
                return int(age_value)
            except (TypeError, ValueError):
                age_value = None
        if age_value is None:
            birth_date = patient_info.get('birth_date') if isinstance(patient_info, dict) else None
            if birth_date:
                bd = QDate.fromString(birth_date, "yyyy-MM-dd")
                if bd.isValid():
                    age_value = bd.daysTo(QDate.currentDate()) // 365
        return age_value
    def _format_age_text(self, patient_info, order_info):
        age_value = self._calculate_age_years(patient_info, order_info)
        return f"{age_value} años" if age_value is not None else "-"
    def _extract_result_structure(self, test_name, raw_result):
        parsed = self._parse_stored_result(raw_result)
        template_key = parsed.get("template") if isinstance(parsed, dict) else None
        template = TEST_TEMPLATES.get(template_key) if template_key in TEST_TEMPLATES else TEST_TEMPLATES.get(test_name)
        if parsed.get("type") == "structured" and template:
            values = parsed.get("values", {})
            items = []
            for field_def in template.get("fields", []):
                if field_def.get("type") == "section":
                    label = field_def.get("label", "")
                    if label:
                        items.append({"type": "section", "label": label})
                    continue
                key = field_def.get("key")
                if not key:
                    continue
                value = values.get(key, "")
                if isinstance(value, str):
                    display_value = " ".join(value.split())
                else:
                    display_value = value
                if display_value in (None, ""):
                    display_value = "-"
                unit = field_def.get("unit")
                field_type = field_def.get("type")
                if unit and display_value not in ("-", "") and field_type not in ("bool", "text_area", "choice"):
                    display_value = f"{display_value} {unit}"
                items.append({
                    "type": "value",
                    "label": field_def.get("label", key),
                    "value": display_value,
                    "reference": field_def.get("reference")
                })
            return {"type": "structured", "items": items}
        text_value = parsed.get("value", raw_result or "")
        if isinstance(text_value, str):
            text_value = text_value.strip()
        if text_value == "":
            text_value = "-"
        return {"type": "text", "value": text_value}
    def _find_logo_path(self, position):
        if position not in {"left", "center", "right"}:
            return None
        search_dirs = ["", "assets", "resources", "images", "img", "static"]
        base_names = [
            f"logo_{position}.png",
            f"logo_{position}.jpg",
            f"logo_{position}.jpeg",
            f"{position}_logo.png",
            f"{position}_logo.jpg",
        ]
        if position == "center":
            base_names.extend([
                "logo.png",
                "logo_central.png",
                "logo_central.jpg",
                "logo_centro.png",
            ])
        if position == "right":
            base_names.extend(["logo_secondary.png", "logo_secundario.png"])
        for directory in search_dirs:
            for name in base_names:
                candidate = os.path.join(directory, name) if directory else name
                if os.path.exists(candidate):
                    return candidate
        return None
    def init_emitir_page(self):
        layout = QVBoxLayout(self.page_emitir)
        top_layout = QHBoxLayout()
        lbl = QLabel("Orden completada:")
        self.combo_completed = QComboBox()
        btn_view = QPushButton("Ver")
        btn_add_tests = QPushButton("Agregar pruebas")
        top_layout.addWidget(lbl)
        top_layout.addWidget(self.combo_completed, 1)
        top_layout.addWidget(btn_view)
        top_layout.addWidget(btn_add_tests)
        layout.addLayout(top_layout)
        sort_layout = QHBoxLayout()
        self.include_emitted_checkbox = QCheckBox("Mostrar emitidos")
        sort_layout.addWidget(self.include_emitted_checkbox)
        sort_layout.addStretch()
        sort_label = QLabel("Ordenar:")
        self.completed_sort_combo = QComboBox()
        self.completed_sort_combo.addItems([
            "Fecha (recientes primero)",
            "Fecha (antiguas primero)",
            "Número de orden (descendente)",
            "Número de orden (ascendente)"
        ])
        sort_layout.addWidget(sort_label)
        sort_layout.addWidget(self.completed_sort_combo)
        layout.addLayout(sort_layout)
        self.output_text = QTextEdit(); self.output_text.setReadOnly(True)
        layout.addWidget(self.output_text)
        btn_pdf = QPushButton("Emitir en PDF"); btn_excel = QPushButton("Exportar a Excel")
        btns_layout = QHBoxLayout(); btns_layout.addWidget(btn_pdf); btns_layout.addWidget(btn_excel)
        layout.addLayout(btns_layout)
        btn_view.clicked.connect(self.display_selected_result)
        btn_pdf.clicked.connect(self.export_pdf)
        btn_excel.clicked.connect(self.export_excel)
        btn_add_tests.clicked.connect(self.add_tests_to_selected_order)
        self.include_emitted_checkbox.toggled.connect(self.populate_completed_orders)
        self.completed_sort_combo.currentIndexChanged.connect(lambda: self._refresh_completed_combo())
    def populate_completed_orders(self):
        # Llenar combo de órdenes completadas
        include_emitted = False
        if hasattr(self, 'include_emitted_checkbox'):
            include_emitted = self.include_emitted_checkbox.isChecked()
        completed_rows = self.labdb.get_completed_orders(include_emitted=include_emitted)
        self.completed_orders_cache = []
        for row in completed_rows:
            oid, first, last, date, doc_type, doc_number, emitted, emitted_at = row
            order = {
                "id": oid,
                "first_name": (first or "").upper(),
                "last_name": (last or "").upper(),
                "date": date,
                "doc_type": doc_type or "",
                "doc_number": doc_number or "",
                "emitted": bool(emitted),
                "emitted_at": emitted_at
            }
            self.completed_orders_cache.append(order)
        self._refresh_completed_combo()

    def add_tests_to_selected_order(self):
        data = self.combo_completed.currentData() if hasattr(self, 'combo_completed') else None
        if data is None:
            QMessageBox.information(self, "Sin selección", "Seleccione una orden para agregar pruebas adicionales.")
            return
        order_id = int(data)
        all_tests = self.labdb.get_all_tests()
        existing = self.labdb.get_tests_for_order(order_id)
        dialog = AddTestsDialog(all_tests, existing, self)
        if dialog.exec_() != QDialog.Accepted:
            return
        selected = dialog.get_selected_tests()
        if not selected:
            QMessageBox.information(self, "Sin cambios", "No se seleccionaron nuevas pruebas.")
            return
        added = self.labdb.add_tests_to_order(order_id, selected)
        if not added:
            QMessageBox.information(self, "Sin cambios", "Las pruebas seleccionadas ya estaban asociadas a la orden.")
            return
        QMessageBox.information(
            self,
            "Pruebas agregadas",
            "Se agregaron {0} prueba(s). Registre los resultados antes de emitir nuevamente.".format(len(added))
        )
        self.selected_order_id = order_id
        self.populate_pending_orders()
        self.populate_completed_orders()
        reply = QMessageBox.question(
            self,
            "Registrar resultados",
            "¿Desea ir a la pantalla de resultados para completar las nuevas pruebas?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.stack.setCurrentWidget(self.page_resultados)
            if hasattr(self, 'combo_orders'):
                self._select_order_in_combo(self.combo_orders, order_id)
            self.load_order_fields()
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
        doc_text = " ".join([part for part in (pat.get('doc_type'), pat.get('doc_number')) if part]) or "-"
        lines = [f"PACIENTE: {pat.get('name') or '-'}", f"DOCUMENTO: {doc_text}"]
        age_value = self._calculate_age_years(pat, ord_inf)
        lines.append(f"EDAD: {age_value} AÑOS" if age_value is not None else "EDAD: -")
        lines.append(f"SEXO: {pat.get('sex') or '-'}")
        lines.append(f"HISTORIA CLÍNICA: {pat.get('hcl') or '-'}")
        lines.append(f"PROCEDENCIA: {pat.get('origin') or '-'}")
        lines.append(f"FECHA DE MUESTRA: {ord_inf.get('date') or '-'}")
        lines.append(f"SOLICITANTE: {ord_inf.get('requested_by') or '-'}")
        lines.append(f"DIAGNÓSTICO PRESUNTIVO: {ord_inf.get('diagnosis') or '-'}")
        emission_raw = ord_inf.get('emitted_at')
        if emission_raw:
            try:
                emission_dt = datetime.datetime.strptime(emission_raw, "%Y-%m-%d %H:%M:%S")
                emission_display = emission_dt.strftime("%d/%m/%Y %H:%M")
            except Exception:
                emission_display = emission_raw
        else:
            emission_display = "Pendiente de emisión"
        lines.append(f"FECHA DE EMISIÓN: {emission_display}")
        lines.append("RESULTADOS:")
        for test_name, result, _ in results:
            lines.extend(self._format_result_lines(test_name, result))
        if ord_inf["observations"]:
            lines.append(f"Observaciones: {ord_inf['observations']}")
        self.output_text.setPlainText("\n".join(lines))

    def export_pdf(self):
        # Exportar el resultado seleccionado a un archivo PDF
        data = self.combo_completed.currentData()
        if data is None:
            return
        order_id = int(data)
        info = self.labdb.get_order_details(order_id)
        if not info:
            return
        pat = info["patient"]; ord_inf = info["order"]; results = info["results"]
        suggested_name = f"Orden_{order_id}.pdf"
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "Guardar PDF", suggested_name, "Archivos PDF (*.pdf)", options=options)
        if not file_path:
            return
        if not file_path.lower().endswith(".pdf"):
            file_path += ".pdf"
        existing_emission = ord_inf.get('emitted_at')
        mark_as_emitted = not (ord_inf.get('emitted') and existing_emission)
        if mark_as_emitted:
            emission_time = datetime.datetime.now()
            emission_display = emission_time.strftime("%d/%m/%Y %H:%M")
            emission_timestamp = emission_time.strftime("%Y-%m-%d %H:%M:%S")
        else:
            emission_timestamp = existing_emission
            try:
                parsed = datetime.datetime.strptime(existing_emission, "%Y-%m-%d %H:%M:%S")
                emission_display = parsed.strftime("%d/%m/%Y %H:%M")
            except Exception:
                emission_display = existing_emission or "-"
        doc_text = " ".join([part for part in (pat.get('doc_type'), pat.get('doc_number')) if part]) or "-"
        patient_name = (pat.get('name') or '-').upper()
        age_text = self._format_age_text(pat, ord_inf)
        order_date_text = ord_inf.get('date') or "-"
        sex_text = (pat.get('sex') or '-').upper()
        hcl_text = (pat.get('hcl') or '-').upper()
        origin_text = (pat.get('origin') or '-').upper()
        requester_text = (ord_inf.get('requested_by') or '-').upper()
        diagnosis_text = (ord_inf.get('diagnosis') or '-').upper()
        pdf = FPDF('P', 'mm', 'A4')
        pdf.set_margins(12, 12, 12)
        pdf.set_auto_page_break(True, margin=14)
        pdf.add_page()
        header_image_path = os.path.join("img", "img.png")
        info_pairs = [
            (("Paciente", patient_name), ("Edad", age_text)),
            (("Documento", doc_text.upper() if doc_text else "-"), ("Sexo", sex_text)),
            (("Historia clínica", hcl_text), ("Fecha emisión", emission_display)),
            (("Procedencia", origin_text), ("Fecha muestra", order_date_text)),
            (("Solicitante", requester_text), ("Diagnóstico presuntivo", diagnosis_text)),
        ]

        def draw_patient_info():
            col_width = (pdf.w - pdf.l_margin - pdf.r_margin) / 2

            def render_pair(label, value, x_start, width, start_y):
                pdf.set_xy(x_start, start_y)
                pdf.set_font("Arial", 'B', 7.2)
                pdf.cell(width, 3.4, f"{label.upper()}:", border=0)
                pdf.set_font("Arial", '', 7.2)
                pdf.set_xy(x_start, pdf.get_y())
                safe_value = str(value) if value not in (None, "") else "-"
                pdf.multi_cell(width, 3.6, safe_value, border=0)
                return pdf.get_y()

            pdf.set_font("Arial", 'B', 8.8)
            pdf.set_text_color(30, 30, 30)
            pdf.cell(0, 5, "Datos del paciente", ln=1)
            pdf.set_text_color(0, 0, 0)
            pdf.ln(1)
            for left, right in info_pairs:
                start_y = pdf.get_y()
                left_end = render_pair(left[0], left[1], pdf.l_margin, col_width, start_y)
                right_end = render_pair(right[0], right[1], pdf.l_margin + col_width, col_width, start_y)
                pdf.set_y(max(left_end, right_end) + 1.2)

        def draw_page_header():
            top_y = max(5, pdf.t_margin - 6)
            header_drawn = False
            if os.path.exists(header_image_path):
                try:
                    header_width = pdf.w - pdf.l_margin - pdf.r_margin
                    header_height = 27
                    pdf.image(header_image_path, x=pdf.l_margin, y=top_y, w=header_width, h=header_height)
                    pdf.set_y(top_y + header_height + 2)
                    header_drawn = True
                except Exception:
                    header_drawn = False
            if not header_drawn:
                fallback_logo = self._find_logo_path('center')
                if fallback_logo:
                    try:
                        pdf.image(fallback_logo, x=(pdf.w - 28) / 2, y=top_y, w=28)
                        pdf.set_y(top_y + 30)
                        header_drawn = True
                    except Exception:
                        header_drawn = False
            if not header_drawn:
                pdf.set_y(pdf.t_margin)
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 6, LAB_TITLE, ln=1, align='C')
                pdf.ln(2)
            draw_patient_info()
            pdf.ln(1.5)

        def ensure_space(required_height):
            if pdf.get_y() + required_height > pdf.h - pdf.b_margin:
                pdf.add_page()
                draw_page_header()
                return True
            return False

        def wrap_text(text, max_width):
            if max_width <= 0:
                return [str(text)]
            if text in (None, ""):
                text = "-"
            text = str(text).replace('\r', ' ')
            segments = []
            for part in text.split('\n'):
                stripped = part.strip()
                if stripped:
                    segments.append(stripped)
            if not segments:
                segments = [text.strip() or "-"]
            lines = []
            for segment in segments:
                words = segment.split()
                if not words:
                    lines.append("-")
                    continue
                current = words[0]
                for word in words[1:]:
                    candidate = f"{current} {word}"
                    if pdf.get_string_width(candidate) <= max_width:
                        current = candidate
                    else:
                        lines.append(current)
                        current = word
                lines.append(current)
            return lines or ["-"]

        def render_table_header(widths, on_new_page=None):
            header_height = 6
            if ensure_space(header_height) and on_new_page:
                on_new_page()
                ensure_space(header_height)
            pdf.set_font("Arial", 'B', 7.2)
            pdf.set_text_color(255, 255, 255)
            pdf.set_fill_color(46, 117, 182)
            x_start = pdf.l_margin
            pdf.set_x(x_start)
            headers = ["Parámetro", "Resultado", "Valores de referencia"]
            for idx, title in enumerate(headers):
                pdf.cell(widths[idx], header_height, title, border=1, align='C', fill=True)
            pdf.ln(header_height)
            pdf.set_text_color(0, 0, 0)

        def render_table_row(texts, widths, on_new_page):
            line_height = 3.4
            padding_x = 1.4
            padding_y = 0.9
            pdf.set_font("Arial", '', 6.8)
            lines_by_cell = []
            max_lines = 1
            for idx, text in enumerate(texts):
                available = max(widths[idx] - 2 * padding_x, 1)
                lines = wrap_text(text, available)
                lines_by_cell.append(lines)
                if len(lines) > max_lines:
                    max_lines = len(lines)
            row_height = max_lines * line_height + 2 * padding_y
            if ensure_space(row_height):
                on_new_page()
                render_table_header(widths)
            x_start = pdf.l_margin
            y_start = pdf.get_y()
            pdf.set_draw_color(210, 215, 226)
            pdf.set_line_width(0.2)
            for idx, lines in enumerate(lines_by_cell):
                cell_width = widths[idx]
                x_pos = x_start + sum(widths[:idx])
                pdf.set_fill_color(255, 255, 255)
                pdf.rect(x_pos, y_start, cell_width, row_height)
                text_y = y_start + padding_y
                for line in lines:
                    pdf.set_xy(x_pos + padding_x, text_y)
                    pdf.cell(cell_width - 2 * padding_x, line_height, line, border=0)
                    text_y += line_height
            pdf.set_xy(pdf.l_margin, y_start + row_height)

        def render_section_row(label, total_width, widths, on_new_page):
            section_height = 4.2
            if ensure_space(section_height + 1):
                on_new_page()
                render_table_header(widths)
            pdf.set_font("Arial", 'B', 6.8)
            pdf.set_fill_color(242, 246, 253)
            pdf.set_text_color(47, 84, 150)
            pdf.cell(total_width, section_height, label, border=1, ln=1, align='L', fill=True)
            pdf.set_text_color(0, 0, 0)

        draw_page_header()

        table_total_width = pdf.w - pdf.l_margin - pdf.r_margin
        column_widths = [table_total_width * 0.38, table_total_width * 0.27, table_total_width * 0.35]

        def draw_test_header(title):
            ensure_space(9)
            pdf.set_font("Arial", 'B', 8.6)
            pdf.set_text_color(255, 255, 255)
            pdf.set_fill_color(46, 117, 182)
            pdf.cell(0, 6, title.upper(), ln=1, fill=True)
            pdf.set_text_color(0, 0, 0)
            pdf.ln(1.2)

        for test_name, raw_result, _ in results:
            structure = self._extract_result_structure(test_name, raw_result)
            draw_test_header(test_name)
            def on_new_page():
                draw_test_header(test_name)
            if structure.get("type") == "structured":
                render_table_header(column_widths, on_new_page)
                for item in structure.get("items", []):
                    if item.get("type") == "section":
                        render_section_row(item.get("label", ""), sum(column_widths), column_widths, on_new_page)
                        continue
                    row_texts = [
                        item.get('label', ''),
                        item.get('value', '-'),
                        item.get('reference') or '-'
                    ]
                    render_table_row(row_texts, column_widths, on_new_page)
            else:
                value_text = structure.get("value", "-")
                ensure_space(6)
                pdf.set_font("Arial", '', 7)
                pdf.multi_cell(0, 4, str(value_text))
            pdf.ln(2)

        if ord_inf.get('observations'):
            ensure_space(8)
            pdf.set_font("Arial", 'B', 7.4)
            pdf.cell(0, 4.2, "Observaciones", ln=1)
            pdf.set_font("Arial", '', 6.9)
            pdf.multi_cell(0, 3.6, ord_inf['observations'])
            pdf.ln(1.5)

        try:
            pdf.output(file_path)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo guardar el PDF:\n{e}")
            return
        if mark_as_emitted:
            self.labdb.mark_order_emitted(order_id, emission_timestamp)
        QMessageBox.information(self, "Informe emitido", f"Reporte guardado en:\n{file_path}")
        self.populate_completed_orders()
        self.output_text.clear()


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
                    name = (first or "").upper(); surn = (last or "").upper(); doc = f"{doc_type} {doc_num}".strip()
                    res = self._format_result_for_export(test_name, result)
                    res = res.replace('"', "'")
                    dt = date
                    req = (requester or "").upper()
                    diag = (diagnosis or "").upper()
                    age_txt = str(age_years) if age_years is not None else ""
                    line = f"{name},{surn},{doc},{test_name},\"{res}\",{dt},{req},{diag},{age_txt}\n"
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
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(QLabel("Período:"))
        self.range_combo = QComboBox()
        self.range_combo.addItems([
            "Hoy",
            "Esta semana",
            "Este mes",
            "Últimos 30 días",
            "Rango personalizado"
        ])
        controls_layout.addWidget(self.range_combo)
        controls_layout.addSpacing(10)
        self.start_date_edit = QDateEdit(QDate.currentDate())
        self.start_date_edit.setDisplayFormat("dd-MM-yyyy")
        self.start_date_edit.setCalendarPopup(True)
        controls_layout.addWidget(QLabel("Desde:"))
        controls_layout.addWidget(self.start_date_edit)
        self.end_date_edit = QDateEdit(QDate.currentDate())
        self.end_date_edit.setDisplayFormat("dd-MM-yyyy")
        self.end_date_edit.setCalendarPopup(True)
        controls_layout.addWidget(QLabel("Hasta:"))
        controls_layout.addWidget(self.end_date_edit)
        controls_layout.addSpacing(10)
        self.view_activity_btn = QPushButton("Mostrar registro")
        self.export_activity_pdf_btn = QPushButton("Exportar PDF")
        self.export_activity_csv_btn = QPushButton("Exportar CSV")
        controls_layout.addWidget(self.view_activity_btn)
        controls_layout.addWidget(self.export_activity_pdf_btn)
        controls_layout.addWidget(self.export_activity_csv_btn)
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        self.activity_caption = QLabel()
        self.activity_caption.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.activity_caption)
        self.activity_table = QTableWidget(0, 7)
        self.activity_table.setHorizontalHeaderLabels([
            "Fecha",
            "Orden",
            "Paciente",
            "Documento",
            "Edad",
            "Prueba",
            "Resultado"
        ])
        self.activity_table.setAlternatingRowColors(True)
        self.activity_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.activity_table)
        self.range_combo.currentIndexChanged.connect(self._update_range_controls)
        self.view_activity_btn.clicked.connect(self.load_activity_summary)
        self.export_activity_pdf_btn.clicked.connect(lambda: self.export_activity_record("pdf"))
        self.export_activity_csv_btn.clicked.connect(lambda: self.export_activity_record("csv"))
        self._update_range_controls()
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
        self.load_activity_summary()

    def _update_range_controls(self):
        if not hasattr(self, 'range_combo'):
            return
        is_custom = self.range_combo.currentIndex() == 4
        if hasattr(self, 'start_date_edit'):
            self.start_date_edit.setEnabled(is_custom)
        if hasattr(self, 'end_date_edit'):
            self.end_date_edit.setEnabled(is_custom)
        if not is_custom and hasattr(self, 'start_date_edit') and hasattr(self, 'end_date_edit'):
            today = QDate.currentDate()
            self.start_date_edit.blockSignals(True)
            self.end_date_edit.blockSignals(True)
            self.start_date_edit.setDate(today)
            self.end_date_edit.setDate(today)
            self.start_date_edit.blockSignals(False)
            self.end_date_edit.blockSignals(False)

    def _get_selected_range(self):
        today = datetime.date.today()
        start_date = today
        end_date = today
        description = today.strftime("%d/%m/%Y")
        idx = self.range_combo.currentIndex() if hasattr(self, 'range_combo') else 0
        if idx == 0:  # Hoy
            description = f"Hoy ({today.strftime('%d/%m/%Y')})"
        elif idx == 1:  # Esta semana
            start_date = today - datetime.timedelta(days=today.weekday())
            end_date = start_date + datetime.timedelta(days=6)
            description = f"Semana del {start_date.strftime('%d/%m/%Y')} al {end_date.strftime('%d/%m/%Y')}"
        elif idx == 2:  # Este mes
            start_date = today.replace(day=1)
            if start_date.month == 12:
                next_month = datetime.date(start_date.year + 1, 1, 1)
            else:
                next_month = datetime.date(start_date.year, start_date.month + 1, 1)
            end_date = next_month - datetime.timedelta(days=1)
            description = f"Mes del {start_date.strftime('%d/%m/%Y')} al {end_date.strftime('%d/%m/%Y')}"
        elif idx == 3:  # Últimos 30 días
            start_date = today - datetime.timedelta(days=29)
            end_date = today
            description = f"Últimos 30 días ({start_date.strftime('%d/%m/%Y')} al {end_date.strftime('%d/%m/%Y')})"
        else:  # Rango personalizado
            if hasattr(self, 'start_date_edit') and hasattr(self, 'end_date_edit'):
                start_q = self.start_date_edit.date()
                end_q = self.end_date_edit.date()
                if start_q.isValid():
                    start_date = datetime.date(start_q.year(), start_q.month(), start_q.day())
                if end_q.isValid():
                    end_date = datetime.date(end_q.year(), end_q.month(), end_q.day())
            if end_date < start_date:
                start_date, end_date = end_date, start_date
            description = f"Del {start_date.strftime('%d/%m/%Y')} al {end_date.strftime('%d/%m/%Y')}"
        start_dt = datetime.datetime.combine(start_date, datetime.time.min)
        end_dt = datetime.datetime.combine(end_date, datetime.time.max)
        return start_dt, end_dt, description

    def load_activity_summary(self):
        if not hasattr(self, 'activity_table'):
            return
        start_dt, end_dt, description = self._get_selected_range()
        rows = self.labdb.get_results_in_range(
            start_dt.strftime("%Y-%m-%d %H:%M:%S"),
            end_dt.strftime("%Y-%m-%d %H:%M:%S")
        )
        activity_data = []
        for order_id, date_str, first, last, doc_type, doc_number, age_years, test_name, result in rows:
            try:
                order_dt = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                date_display = order_dt.strftime("%d/%m/%Y %H:%M")
            except Exception:
                date_display = date_str or "-"
            patient_name = " ".join(part for part in [(first or "").upper(), (last or "").upper()] if part).strip() or "-"
            doc_text = " ".join(part for part in (doc_type, doc_number) if part).strip() or "-"
            age_display = str(age_years) if age_years not in (None, "") else "-"
            result_text = self._format_result_for_export(test_name, result).replace('\n', ' ')
            activity_data.append({
                "order_id": order_id,
                "date": date_display,
                "patient": patient_name,
                "document": doc_text,
                "age": age_display,
                "test": test_name,
                "result": result_text
            })
        self._activity_cache = {
            "data": activity_data,
            "description": description,
            "start": start_dt,
            "end": end_dt
        }
        self.activity_table.setRowCount(len(activity_data))
        for row_idx, item in enumerate(activity_data):
            self.activity_table.setItem(row_idx, 0, QTableWidgetItem(item["date"]))
            order_item = QTableWidgetItem(str(item["order_id"]))
            order_item.setTextAlignment(Qt.AlignCenter)
            self.activity_table.setItem(row_idx, 1, order_item)
            self.activity_table.setItem(row_idx, 2, QTableWidgetItem(item["patient"]))
            self.activity_table.setItem(row_idx, 3, QTableWidgetItem(item["document"]))
            age_item = QTableWidgetItem(item["age"])
            age_item.setTextAlignment(Qt.AlignCenter)
            self.activity_table.setItem(row_idx, 4, age_item)
            self.activity_table.setItem(row_idx, 5, QTableWidgetItem(item["test"]))
            self.activity_table.setItem(row_idx, 6, QTableWidgetItem(item["result"]))
        if hasattr(self, 'activity_caption'):
            self.activity_caption.setText(
                f"Registro de pruebas: {description} — {len(activity_data)} resultado(s)"
            )

    def export_activity_record(self, fmt):
        if fmt not in {"pdf", "csv"}:
            return
        if not getattr(self, '_activity_cache', None):
            self.load_activity_summary()
        cache = getattr(self, '_activity_cache', {"data": [], "description": ""})
        data = cache.get("data", [])
        if not data:
            QMessageBox.information(self, "Sin datos", "No hay registros para el período seleccionado.")
            return
        description = cache.get("description", "")
        if fmt == "csv":
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Exportar registro",
                "registro.csv",
                "Archivo CSV (*.csv)"
            )
            if not file_path:
                return
            if not file_path.lower().endswith(".csv"):
                file_path += ".csv"
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("Fecha,Orden,Paciente,Documento,Edad,Prueba,Resultado\n")
                    for item in data:
                        result_clean = item["result"].replace('"', "'")
                        line = (
                            f"{item['date']},{item['order_id']},\"{item['patient']}\"," \
                            f"{item['document']},{item['age']},\"{item['test']}\",\"{result_clean}\"\n"
                        )
                        f.write(line)
            except Exception as exc:
                QMessageBox.warning(self, "Error", f"No se pudo exportar el archivo CSV:\n{exc}")
                return
            QMessageBox.information(self, "Exportado", f"Registro guardado en:\n{file_path}")
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar registro",
            "registro.pdf",
            "Archivos PDF (*.pdf)"
        )
        if not file_path:
            return
        if not file_path.lower().endswith(".pdf"):
            file_path += ".pdf"
        pdf = FPDF('L', 'mm', 'A4')
        pdf.set_margins(12, 12, 12)
        pdf.set_auto_page_break(True, margin=14)
        pdf.add_page()
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 8, LAB_TITLE, ln=1, align='C')
        pdf.set_font("Arial", '', 9)
        pdf.cell(0, 6, f"Registro de resultados — {description}", ln=1, align='C')
        pdf.ln(2)
        headers = ["Fecha", "Orden", "Paciente", "Documento", "Edad", "Prueba", "Resultado"]
        column_widths = [35, 18, 60, 40, 16, 50, 64]
        pdf.set_fill_color(220, 220, 220)
        pdf.set_font("Arial", 'B', 8.5)
        for header, width in zip(headers, column_widths):
            pdf.cell(width, 6, header, border=1, align='C', fill=True)
        pdf.ln(6)

        def ensure_space(required_height):
            if pdf.get_y() + required_height > pdf.h - pdf.b_margin:
                pdf.add_page()
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 8, LAB_TITLE, ln=1, align='C')
                pdf.set_font("Arial", '', 9)
                pdf.cell(0, 6, f"Registro de resultados — {description}", ln=1, align='C')
                pdf.ln(2)
                pdf.set_fill_color(220, 220, 220)
                pdf.set_font("Arial", 'B', 8.5)
                for header, width in zip(headers, column_widths):
                    pdf.cell(width, 6, header, border=1, align='C', fill=True)
                pdf.ln(6)
                pdf.set_font("Arial", '', 7.8)

        pdf.set_font("Arial", '', 7.8)
        for item in data:
            cells = [
                item["date"],
                str(item["order_id"]),
                item["patient"],
                item["document"],
                item["age"],
                item["test"],
                item["result"],
            ]
            ensure_space(8)
            y_start = pdf.get_y()
            x_start = pdf.get_x()
            max_y = y_start
            for width, text in zip(column_widths, cells):
                pdf.set_xy(x_start, y_start)
                pdf.multi_cell(width, 5, str(text) if text not in (None, "") else "-", border=1)
                x_start += width
                max_y = max(max_y, pdf.get_y())
            pdf.set_y(max_y)
        try:
            pdf.output(file_path)
        except Exception as exc:
            QMessageBox.warning(self, "Error", f"No se pudo generar el PDF:\n{exc}")
            return
        QMessageBox.information(self, "Exportado", f"Registro guardado en:\n{file_path}")
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
