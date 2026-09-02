# -*- coding: utf-8 -*-
"""Genera la documentación técnica del proyecto WebService-Reclut en un archivo Word."""

from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import datetime

AZUL = RGBColor(0x1F, 0x3A, 0x5F)
GRIS = RGBColor(0x55, 0x55, 0x55)

doc = Document()

# ── Estilos base ──────────────────────────────────────────────────────────
style = doc.styles['Normal']
style.font.name = 'Calibri'
style.font.size = Pt(11)
rpr = style.element.get_or_add_rPr()
rFonts = rpr.find(qn('w:rFonts'))
if rFonts is None:
    rFonts = OxmlElement('w:rFonts')
    rpr.append(rFonts)
rFonts.set(qn('w:eastAsia'), 'Calibri')

for i in range(1, 4):
    hstyle = doc.styles[f'Heading {i}']
    hstyle.font.name = 'Calibri'
    hstyle.font.color.rgb = AZUL
    hstyle.font.bold = True


def set_cell_shading(cell, color_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), color_hex)
    tcPr.append(shd)


def add_table(headers, rows, widths=None):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr_cells = table.rows[0].cells
    for i, h in enumerate(headers):
        hdr_cells[i].text = h
        for p in hdr_cells[i].paragraphs:
            for r in p.runs:
                r.font.bold = True
                r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        set_cell_shading(hdr_cells[i], '1F3A5F')
    for row in rows:
        cells = table.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = str(val)
    if widths:
        for row in table.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Cm(w)
    return table


def add_code_block(text):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.5)
    run = p.add_run(text)
    run.font.name = 'Consolas'
    run.font.size = Pt(9.5)
    rpr = run._element.get_or_add_rPr()
    rFonts = OxmlElement('w:rFonts')
    rFonts.set(qn('w:ascii'), 'Consolas')
    rFonts.set(qn('w:hAnsi'), 'Consolas')
    rpr.append(rFonts)
    # fondo gris claro
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), 'F2F2F2')
    pPr = p._p.get_or_add_pPr()
    pPr.append(shd)
    return p


# ═══════════════════════════════════════════════════════════════════════════
# PORTADA
# ═══════════════════════════════════════════════════════════════════════════
for _ in range(4):
    doc.add_paragraph()

title = doc.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = title.add_run('WebService-Reclut')
run.font.size = Pt(32)
run.font.bold = True
run.font.color.rgb = AZUL

subtitle = doc.add_paragraph()
subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = subtitle.add_run('Documentación Técnica del Servicio Web de Integración\nUnibagué ↔ Reqlut')
run.font.size = Pt(16)
run.font.color.rgb = GRIS

doc.add_paragraph()
info = doc.add_paragraph()
info.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = info.add_run('Universidad de Ibagué\nDirección de Admisiones / TI\n\n')
run.font.size = Pt(12)
run2 = info.add_run(f'Versión 1.0 — {datetime.date.today().strftime("%d de %B de %Y")}')
run2.font.size = Pt(11)
run2.italic = True

doc.add_page_break()

# ═══════════════════════════════════════════════════════════════════════════
# 1. RESUMEN EJECUTIVO
# ═══════════════════════════════════════════════════════════════════════════
doc.add_heading('1. Resumen Ejecutivo', level=1)
doc.add_paragraph(
    'WebService-Reclut es un microservicio desarrollado en PHP que actúa como capa de '
    'integración (adaptador) entre la API interna de estudiantes de la Universidad de '
    'Ibagué (Unibagué) y el formato de datos requerido por la plataforma de reclutamiento '
    'y admisiones Reqlut.'
)
doc.add_paragraph(
    'El servicio expone un único endpoint HTTP tipo REST que permite consultar la '
    'información académica de un estudiante o aspirante mediante su número de '
    'identificación o su correo electrónico. El servicio consulta (con caché local) la '
    'API oficial de Unibagué, transforma la estructura de datos recibida al esquema '
    'esperado por Reqlut, y devuelve la respuesta en formato JSON.'
)
doc.add_paragraph('Características principales:')
for item in [
    'Endpoint protegido con API key (header X-Api-Key o parámetro api_key).',
    'Caché en disco de 1 hora para cumplir el tiempo de respuesta máximo exigido por Reqlut (3 segundos).',
    'Transformación automática del modelo académico de Unibagué al modelo Reqlut '
    '(tipo de programa, estado académico, año de ingreso, género, nombre/apellido).',
    'Soporte para estudiantes con múltiples programas (carreras) asociados.',
    'Configuración por variables de entorno (.env): credenciales, CORS, API key y clave de administración de caché.',
    'Endpoint dedicado (clear_cache.php) para invalidar la caché manualmente sin acceso al servidor.',
    'Despliegue contenerizado mediante Docker y Docker Compose.',
]:
    doc.add_paragraph(item, style='List Bullet')

# ═══════════════════════════════════════════════════════════════════════════
# 2. ARQUITECTURA
# ═══════════════════════════════════════════════════════════════════════════
doc.add_heading('2. Arquitectura General', level=1)
doc.add_paragraph(
    'El servicio sigue una arquitectura simple de tipo "adaptador" (adapter/proxy), '
    'compuesta por tres capas lógicas dentro de un mismo script PHP:'
)
add_table(
    ['Capa', 'Archivo', 'Responsabilidad'],
    [
        ['Configuración', 'config.php', 'Define la URL y token de la API de Unibagué, el directorio y TTL de la caché.'],
        ['Mapeo de programas', 'career_ids.php', 'Traduce el código de programa de Unibagué al ID oficial del programa en Reqlut.'],
        ['Lógica de negocio', 'index.php', 'Recibe la petición HTTP, consulta/cachea los estudiantes, filtra, transforma y responde en JSON.'],
    ],
    widths=[3.5, 3.5, 8.5],
)
doc.add_paragraph()
doc.add_paragraph('Flujo de una petición:')
for i, item in enumerate([
    'El cliente (Reqlut) envía una petición GET a index.php con el parámetro identification o email.',
    'El servicio valida que al menos uno de los dos parámetros esté presente; si no, responde 400.',
    'Se cargan los estudiantes desde la caché local (cache/students.json) si es válida (menos de 1 hora), '
    'o se descargan desde la API de Unibagué (integra.unibague.edu.co) y se guarda la nueva caché.',
    'Se filtran los registros que coincidan con la identificación o el correo solicitado.',
    'Si no hay coincidencias, se responde 404.',
    'Si hay coincidencias, se construye la respuesta en el esquema Reqlut (datos personales + arreglo de carreras) y se devuelve como JSON.',
], start=1):
    doc.add_paragraph(f'{i}. {item}')

# ═══════════════════════════════════════════════════════════════════════════
# 3. ENDPOINT / API
# ═══════════════════════════════════════════════════════════════════════════
doc.add_heading('3. Especificación del Endpoint', level=1)

doc.add_heading('3.1 Consulta de estudiante', level=2)
add_table(
    ['Elemento', 'Detalle'],
    [
        ['Método', 'GET'],
        ['Ruta', '/index.php  (también accesible como /  gracias a mod_rewrite)'],
        ['Content-Type respuesta', 'application/json; charset=utf-8'],
        ['Autenticación', 'API key obligatoria vía header X-Api-Key o parámetro ?api_key= (ver sección 6.1)'],
        ['CORS', 'Configurable mediante REQLUT_ALLOWED_ORIGINS (ver sección 6.2)'],
    ],
    widths=[4, 11.5],
)

doc.add_heading('Parámetros de consulta (query string)', level=3)
add_table(
    ['Parámetro', 'Tipo', 'Obligatorio', 'Descripción'],
    [
        ['identification', 'string', 'Uno de los dos (identification o email)', 'Número de identificación del estudiante.'],
        ['email', 'string', 'Uno de los dos (identification o email)', 'Correo electrónico del estudiante (no distingue mayúsculas/minúsculas).'],
    ],
    widths=[3.5, 2, 4, 6],
)

doc.add_heading('Ejemplos de petición', level=3)
add_code_block(
    'GET /index.php?identification=1102345678\n'
    'Header: X-Api-Key: <clave entregada a Reqlut>\n\n'
    'GET /index.php?email=juan.perez@unibague.edu.co&api_key=<clave>'
)

doc.add_heading('Códigos de respuesta HTTP', level=3)
add_table(
    ['Código', 'Situación'],
    [
        ['200 OK', 'Se encontró al menos un registro y se devuelve el JSON con la información del estudiante.'],
        ['400 Bad Request', 'No se envió ni "identification" ni "email".'],
        ['401 Unauthorized', 'La API key es inválida o no fue enviada (solo si WEBSERVICE_API_KEY está configurada).'],
        ['404 Not Found', 'No se encontró ningún estudiante que coincida con los parámetros.'],
        ['503 Service Unavailable', 'No fue posible conectarse a la API de Unibagué y no existe caché de respaldo, o la respuesta de la API no es válida.'],
    ],
    widths=[4.5, 11],
)

doc.add_heading('3.2 Ejemplo de respuesta exitosa (200)', level=2)
add_code_block(
'''{
  "identification": "1102345678",
  "email": "juan.perez@unibague.edu.co",
  "email2": null,
  "name": "Juan Andres",
  "lastName": "Perez Gomez",
  "phone": null,
  "cellphone": "3001234567",
  "gender": 1,
  "birthDate": null,
  "careers": [
    {
      "type": 1,
      "state": 0,
      "active": true,
      "internship": false,
      "initialYear": 2021,
      "id": 103
    }
  ]
}'''
)

# ═══════════════════════════════════════════════════════════════════════════
# 4. MODELO DE DATOS Y REGLAS DE TRANSFORMACIÓN
# ═══════════════════════════════════════════════════════════════════════════
doc.add_heading('4. Modelo de Datos y Reglas de Transformación', level=1)

doc.add_heading('4.1 Campos de la respuesta (nivel estudiante)', level=2)
add_table(
    ['Campo', 'Tipo', 'Origen / Regla'],
    [
        ['identification', 'string', 'Tomado directamente del primer registro Unibagué.'],
        ['email', 'string', 'Tomado directamente del primer registro Unibagué.'],
        ['email2', 'null', 'No disponible en Unibagué; siempre null.'],
        ['name', 'string', 'Nombres, extraídos de "name" y convertidos a formato Título.'],
        ['lastName', 'string', 'Apellidos, extraídos de "name" y convertidos a formato Título.'],
        ['phone', 'null', 'No disponible en Unibagué; siempre null.'],
        ['cellphone', 'string | null', 'Campo "telephone"; se normaliza a null si está vacío o es "0".'],
        ['gender', 'int', '"sexo": F → 0, M → 1, otro/vacío → 4.'],
        ['birthDate', 'null', 'No disponible en Unibagué; siempre null.'],
        ['careers', 'array', 'Un elemento por cada programa académico del estudiante (ver 4.2).'],
    ],
    widths=[3.5, 2.5, 9],
)

doc.add_heading('4.2 Campos de cada carrera (careers[])', level=2)
add_table(
    ['Campo', 'Tipo', 'Regla'],
    [
        ['type', 'int', 'Ver tabla de tipos en 4.3, según "formation" y nombre del programa.'],
        ['state', 'int', 'Ver tabla de estados en 4.4, según "status".'],
        ['active', 'bool', 'true si status es "Activo" o "Inscrito".'],
        ['internship', 'bool', 'Siempre false (no se gestiona en Unibagué).'],
        ['initialYear', 'int | null', 'Extraído del código de estudiante (formato PPAAAANNNN, posiciones 3-6 = año).'],
        ['id', 'int', 'Solo para type 1 (Pregrado) y 10 (Programa de posgrado): ID Reqlut resuelto vía career_ids.php.'],
        ['programName', 'string', 'Para el resto de tipos: nombre del programa tal como llega de Unibagué.'],
    ],
    widths=[3, 2, 10],
)

doc.add_heading('4.3 Mapeo de tipo de programa (formation → type)', level=2)
add_table(
    ['formation Unibagué', 'Condición adicional', 'type Reqlut', 'Descripción'],
    [
        ['4', '—', '1', 'Pregrado (Undergraduate)'],
        ['5', 'Contiene "DOCTORADO"', '5', 'Doctorado'],
        ['5', 'Contiene "CICLO COTERMINAL"', '10', 'Programa de posgrado (requiere id)'],
        ['5', 'Contiene "ESPECIALIZACION" / "ESP."', '6', 'Especialización (Specialty)'],
        ['5', 'Contiene "CURSOS LIBRES" / "DIPLOMADO"', '2', 'Curso (Course)'],
        ['5 / otro', 'No coincide con lo anterior', '7', 'Otro (Other)'],
        ['6', 'o el nombre contiene "MAESTRIA"', '4', "Maestría (Master's)"],
    ],
    widths=[3, 5.5, 2.5, 4.5],
)

doc.add_heading('4.4 Mapeo de estado académico (status → state)', level=2)
add_table(
    ['status Unibagué', 'state Reqlut', 'Significado'],
    [
        ['Graduado', '1', 'Titulado (recibió diploma formal)'],
        ['Egresado', '2', 'Egresado (terminó materias, sin título)'],
        ['Activo / Inscrito', '0', 'Estudiante activo'],
        ['Otro (retirado, etc.)', '0', 'Por defecto; el campo "active" queda en false'],
    ],
    widths=[5, 3, 7.5],
)

# ═══════════════════════════════════════════════════════════════════════════
# 5. CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════════════
doc.add_heading('5. Configuración (config.php y .env)', level=1)
doc.add_paragraph(
    'Toda la configuración sensible se maneja mediante variables de entorno, cargadas '
    'desde un archivo .env en la raíz del proyecto (no versionado — ver .gitignore). '
    'config.php incluye un cargador simple (loadEnvFile) que lee ese archivo si existe, '
    'sin sobrescribir variables ya definidas por el sistema operativo o por Docker. '
    'El archivo .env.example documenta todas las variables disponibles y sirve de '
    'plantilla para crear el .env real en cada entorno.'
)
add_table(
    ['Variable', 'Obligatoria', 'Valor por defecto', 'Descripción'],
    [
        ['UNIBAGUE_API_URL', 'No', 'http://integra.unibague.edu.co/students/all', 'Endpoint de la API interna de Unibagué.'],
        ['UNIBAGUE_API_TOKEN', 'Sí', '(sin valor por defecto)', 'Token de autenticación ante la API de Unibagué. El servicio no arranca sin él.'],
        ['CACHE_TTL', 'No', '3600', 'Segundos de vigencia de la caché local de estudiantes.'],
        ['REQLUT_ALLOWED_ORIGINS', 'No', '*', 'Dominios permitidos para CORS, separados por coma; "*" = sin restricción.'],
        ['WEBSERVICE_API_KEY', 'No (recomendada)', '(vacío = sin autenticación)', 'API key exigida a los clientes del endpoint /index.php.'],
        ['CACHE_ADMIN_KEY', 'No (recomendada)', '(vacío = deshabilitado)', 'Clave para invalidar la caché vía /clear_cache.php.'],
    ],
    widths=[4, 2.5, 4, 5],
)
doc.add_paragraph(
    'El token de Unibagué y las claves generadas ya NO se almacenan en el código fuente '
    '(config.php), sino únicamente en el archivo .env de cada entorno, que está excluido '
    'del control de versiones y de la imagen Docker (ver .gitignore y .dockerignore).'
)

doc.add_heading('5.1 Mapeo de IDs de programa (career_ids.php)', level=2)
doc.add_paragraph(
    'El archivo career_ids.php contiene el arreglo $CAREER_ID_MAP, que traduce el código '
    'de programa de Unibagué (program_code) al ID oficial que Reqlut asigna a cada '
    'programa académico. Esta lista debe ser suministrada por Reqlut durante la '
    'implementación (disponible en el portal Reqlut: Admin > Users > Alumni Base).'
)
doc.add_paragraph(
    'Estado actual: el mapeo está pendiente de completar. Mientras no se configure, la '
    'función resolveReqlutCareerID() utiliza el program_code de Unibagué como valor de '
    'respaldo (fallback), lo cual puede no coincidir con el ID real esperado por Reqlut.'
)
add_code_block(
'''$CAREER_ID_MAP = [
    // '23' => 103,   // Ingeniería Industrial → ID 103 en Reqlut
    // '21' => 101,   // Ingeniería Mecánica   → ID 101 en Reqlut
    // Agregar aquí los mapeos cuando se reciban de Reqlut
];'''
)

# ═══════════════════════════════════════════════════════════════════════════
# 6. SEGURIDAD
# ═══════════════════════════════════════════════════════════════════════════
doc.add_heading('6. Seguridad', level=1)

doc.add_heading('6.1 Autenticación por API key', level=2)
doc.add_paragraph(
    'El endpoint /index.php exige una API key cuando la variable de entorno '
    'WEBSERVICE_API_KEY está configurada. El cliente (Reqlut) debe enviarla de una de '
    'estas dos formas:'
)
for item in [
    'Header HTTP: X-Api-Key: <clave>',
    'Parámetro de consulta: ?api_key=<clave>',
]:
    doc.add_paragraph(item, style='List Bullet')
doc.add_paragraph(
    'Si la clave no se envía o no coincide, el servicio responde 401 Unauthorized antes '
    'de procesar cualquier otra validación. La comparación se hace con hash_equals() '
    'para evitar ataques de temporización (timing attacks). Si WEBSERVICE_API_KEY se '
    'deja vacía en .env, el endpoint queda abierto (comportamiento previo, no recomendado '
    'en producción).'
)
doc.add_paragraph(
    'Estado actual: se generó una clave y quedó activa en el archivo .env del entorno '
    'actual. Esa clave debe compartirse de forma segura con Reqlut para que la incluyan '
    'en sus peticiones.'
)

doc.add_heading('6.2 CORS (Access-Control-Allow-Origin)', level=2)
doc.add_paragraph(
    'El origen permitido se controla con la variable REQLUT_ALLOWED_ORIGINS:'
)
for item in [
    '"*" (valor por defecto): permite cualquier origen — apropiado para integraciones '
    'servidor-a-servidor, donde el header Origin normalmente no aplica.',
    'Lista de dominios separados por coma (ej. https://app.reqlut.com): el servicio '
    'solo responde con Access-Control-Allow-Origin cuando el header Origin de la '
    'petición coincide exactamente con uno de la lista; en caso contrario, omite el '
    'header (bloqueando la lectura de la respuesta desde un navegador de otro origen).',
]:
    doc.add_paragraph(item, style='List Bullet')
doc.add_paragraph(
    'Estado actual: se dejó en "*" porque la integración es servidor-a-servidor y aún '
    'no se ha confirmado si Reqlut necesita llamadas desde el navegador. Si en algún '
    'momento se identifica el dominio exacto desde el que Reqlut llama al servicio, '
    'basta con actualizar REQLUT_ALLOWED_ORIGINS en el .env, sin tocar el código.'
)

doc.add_heading('6.3 Protección de archivos sensibles', level=2)
for item in [
    'El archivo .env (credenciales) nunca se sube al repositorio (.gitignore) ni se '
    'incluye en la imagen Docker (.dockerignore); se inyecta en tiempo de ejecución '
    'mediante env_file en docker-compose.yml.',
    'El .htaccess bloquea el acceso HTTP directo a .env y .env.example.',
    'El directorio /cache sigue bloqueado a nivel de .htaccess, como ya se documentó.',
]:
    doc.add_paragraph(item, style='List Bullet')

# ═══════════════════════════════════════════════════════════════════════════
# 7. CACHÉ
# ═══════════════════════════════════════════════════════════════════════════
doc.add_heading('7. Estrategia de Caché', level=1)
doc.add_paragraph(
    'Reqlut exige que las respuestas del webservice se entreguen en un máximo de 3 '
    'segundos. Dado que la API de Unibagué puede tardar más al descargar el listado '
    'completo de estudiantes, el servicio implementa una caché local en disco:'
)
for item in [
    'Ruta del archivo de caché: cache/students.json.',
    'Vigencia: 1 hora (CACHE_TTL = 3600 s). Mientras la caché sea vigente, no se '
    'vuelve a consultar la API de Unibagué.',
    'Respaldo ante fallas: si la API de Unibagué no responde y existe una caché '
    'previa (aunque haya expirado), se utiliza esa caché en lugar de fallar la petición.',
    'El acceso directo al directorio /cache está bloqueado vía .htaccess (regla '
    '"RewriteRule ^cache/ - [F,L]") para evitar exponer el listado completo de estudiantes.',
    'Invalidación manual: el endpoint GET /clear_cache.php?key=<CACHE_ADMIN_KEY> borra '
    'el archivo de caché sin necesidad de acceso al servidor, para cuando un cambio '
    'urgente en Unibagué no puede esperar a que expire el TTL. Si CACHE_ADMIN_KEY está '
    'vacía, este endpoint responde siempre 403.',
]:
    doc.add_paragraph(item, style='List Bullet')

# ═══════════════════════════════════════════════════════════════════════════
# 8. DESPLIEGUE
# ═══════════════════════════════════════════════════════════════════════════
doc.add_heading('8. Despliegue', level=1)

doc.add_heading('8.1 Estructura del proyecto', level=2)
add_code_block(
'''WebService-Reclut/
├── index.php          # Lógica principal del servicio
├── config.php          # Configuración (carga .env, define constantes)
├── career_ids.php       # Mapeo de programas Unibagué → Reqlut
├── clear_cache.php       # Invalidación manual de la caché
├── .env                 # Credenciales y claves (NO versionado)
├── .env.example          # Plantilla documentada de .env
├── cache/              # Caché de estudiantes (generada en tiempo de ejecución)
├── .htaccess            # Reescritura de URLs y bloqueo de /cache y .env
├── Dockerfile           # Imagen PHP 8.3 + Apache
├── docker-compose.yml     # Orquestación del contenedor (inyecta .env)
├── .gitignore
└── .dockerignore'''
)

doc.add_heading('8.2 Requisitos', level=2)
for item in [
    'PHP 8.3 o superior con extensión mbstring habilitada.',
    'Servidor Apache con mod_rewrite habilitado (o equivalente).',
    'Acceso de red saliente hacia integra.unibague.edu.co.',
    'Docker y Docker Compose (para despliegue contenerizado).',
]:
    doc.add_paragraph(item, style='List Bullet')

doc.add_heading('8.3 Despliegue con Docker (recomendado)', level=2)
add_code_block('docker compose up -d --build')
doc.add_paragraph(
    'El servicio queda expuesto en el puerto 8080 del host (mapeado al puerto 80 del '
    'contenedor), según lo definido en docker-compose.yml. La carpeta cache/ se monta '
    'como volumen para que la caché persista fuera del contenedor entre reinicios.'
)
add_table(
    ['Configuración Docker', 'Valor'],
    [
        ['Imagen base', 'php:8.3-apache'],
        ['Módulo habilitado', 'mod_rewrite (a2enmod rewrite)'],
        ['AllowOverride', 'All (para permitir .htaccess en la raíz)'],
        ['Puerto host → contenedor', '8080 → 80'],
        ['Volumen', './cache → /var/www/html/cache'],
        ['Permisos de cache/', 'www-data:www-data, 755'],
    ],
    widths=[6, 9.5],
)

doc.add_heading('8.4 Despliegue manual (sin Docker)', level=2)
for i, item in enumerate([
    'Copiar los archivos del proyecto al DocumentRoot de Apache/Nginx con soporte PHP.',
    'Habilitar mod_rewrite (Apache) y permitir AllowOverride All en el directorio del proyecto.',
    'Crear la carpeta cache/ con permisos de escritura para el usuario del servidor web.',
    'Copiar .env.example a .env y completar UNIBAGUE_API_TOKEN, WEBSERVICE_API_KEY y '
    'CACHE_ADMIN_KEY con valores reales.',
    'Completar career_ids.php con el mapeo real de programas entregado por Reqlut.',
], start=1):
    doc.add_paragraph(f'{i}. {item}')

# ═══════════════════════════════════════════════════════════════════════════
# 9. PRUEBAS
# ═══════════════════════════════════════════════════════════════════════════
doc.add_heading('9. Pruebas Manuales Sugeridas', level=1)
add_table(
    ['Caso', 'Petición', 'Resultado esperado'],
    [
        ['Sin API key', 'GET /index.php?identification=123', '401 (si WEBSERVICE_API_KEY está configurada)'],
        ['API key inválida', 'GET /index.php?identification=123&api_key=xxx', '401'],
        ['Con API key, sin parámetros', 'GET /index.php?api_key=<clave>', '400 con mensaje de error'],
        ['Identificación inexistente', 'GET /index.php?identification=0&api_key=<clave>', '404'],
        ['Identificación válida', 'GET /index.php?identification=<cédula real>&api_key=<clave>', '200 con JSON del estudiante'],
        ['Correo válido (mayúsculas)', 'GET /index.php?email=NOMBRE@UNIBAGUE.EDU.CO&api_key=<clave>', '200 (no distingue mayúsculas/minúsculas)'],
        ['Estudiante con varios programas', 'GET /index.php?identification=<cédula>&api_key=<clave>', 'careers[] con más de un elemento'],
        ['Acceso directo a la caché', 'GET /cache/students.json', '403 Forbidden'],
        ['Acceso directo a .env', 'GET /.env', '403 Forbidden'],
        ['Invalidar caché con clave correcta', 'GET /clear_cache.php?key=<CACHE_ADMIN_KEY>', '200 con success:true'],
        ['Invalidar caché sin clave', 'GET /clear_cache.php', '401 (o 403 si CACHE_ADMIN_KEY está vacía)'],
    ],
    widths=[4.5, 6, 4.5],
)

# ═══════════════════════════════════════════════════════════════════════════
# 10. PENDIENTES Y RECOMENDACIONES
# ═══════════════════════════════════════════════════════════════════════════
doc.add_heading('10. Pendientes y Recomendaciones', level=1)
doc.add_paragraph(
    'De las recomendaciones identificadas en la revisión inicial del servicio, el '
    'siguiente es el estado actual:'
)
add_table(
    ['Recomendación', 'Estado'],
    [
        ['Completar $CAREER_ID_MAP con los IDs oficiales de Reqlut', 'Pendiente — depende de que Reqlut entregue el listado (Admin > Users > Alumni Base).'],
        ['Mover UNIBAGUE_API_TOKEN a variable de entorno', 'Resuelto — ahora se lee desde .env (variable obligatoria).'],
        ['Restringir Access-Control-Allow-Origin a los dominios de Reqlut', 'Preparado, no aplicado — REQLUT_ALLOWED_ORIGINS queda en "*" hasta confirmar el dominio de Reqlut.'],
        ['Agregar autenticación (API key propia) al endpoint', 'Resuelto — WEBSERVICE_API_KEY activa, exigida vía X-Api-Key o ?api_key=.'],
        ['Automatizar la invalidación manual de la caché', 'Resuelto — endpoint /clear_cache.php protegido con CACHE_ADMIN_KEY.'],
    ],
    widths=[7.5, 7.5],
)
doc.add_paragraph('Acciones pendientes de coordinar con Reqlut:')
for item in [
    'Solicitar el listado oficial de IDs de programa para completar career_ids.php.',
    'Compartir de forma segura (no por correo plano) la API key generada en '
    'WEBSERVICE_API_KEY para que Reqlut la incluya en sus peticiones.',
    'Confirmar si Reqlut llama al servicio desde el navegador del usuario o desde su '
    'backend; si es desde el navegador, pedir el dominio exacto para configurar '
    'REQLUT_ALLOWED_ORIGINS.',
]:
    doc.add_paragraph(item, style='List Bullet')

# ── Pie de página con número de página ──────────────────────────────────
section = doc.sections[0]
footer = section.footer
p = footer.paragraphs[0]
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.add_run('WebService-Reclut — Documentación Técnica')

out_path = r'c:\Users\UNIBAGUE\Documents\WebService-Reclut\WebService-Reclut_Documentacion.docx'
doc.save(out_path)
print('OK:', out_path)
