# 🧪 Laboratorio 3 — Opción D: GitHub + Vercel 
Link video: https://youtu.be/eAs7Y5kchsc 
Link Vercel: https://lab3-compis.vercel.app

## 📋 Descripción General

En esta opción escribes un **DSL propio llamado SiteLang** que define la
estructura y el contenido de un sitio web. Tu compilador —construido con
ANTLR— parsea ese archivo, genera HTML, crea un repositorio en GitHub, sube el
código, y despliega el sitio en Vercel. Al terminar obtienes una **URL pública
real y accesible desde cualquier lugar del mundo**.

Así funcionan por dentro herramientas como **Vercel CLI** y **Netlify CLI**:
parsean un archivo de configuración (que es un DSL), generan un plan, y llaman a
APIs REST para desplegar tu aplicación. Aquí construyes exactamente ese pipeline,
desde cero, con ANTLR.

* **Modalidad: Individual**
* **Costo: $0.00** — No se requiere tarjeta de crédito.

---

## 🧠 ¿Cómo funciona SiteLang?

SiteLang es un lenguaje declarativo mínimo. Un programa (`.sl`) describe un sitio:

```text
site "javier-valladares-sitelang-lab3" {
  title       = "Javier Valladares — UVG 2026"
  description = "Compilador con ANTLR que genera y despliega un sitio estatico"
  theme       = "dark"

  page "index" {
    hero    = "Hola, este sitio lo construyo un compilador que escribi"
    about   = "Soy estudiante de la Universidad del Valle de Guatemala..."
    contact = "TU_CORREO_AQUI"
  }
}
```

Reglas del lenguaje:

- Hay exactamente una declaración raíz `site "<nombre>" { ... }`.
- Dentro del `site` puede haber **atributos** (`clave = valor`) y **páginas**.
- Cada `page "<nombre>" { ... }` contiene sus propios atributos.
- Los valores pueden ser **strings** (`"..."`), **números** o **booleanos**
  (`true` / `false`).
- Los comentarios empiezan con `#` y llegan hasta el fin de línea.
- El archivo debe terminar correctamente (la gramática valida el `EOF`).

El compilador aplica además estas reglas **semánticas** antes de desplegar:

- El nombre del sitio no puede estar vacío y debe producir un nombre de
  repositorio válido para GitHub.
- Debe existir una página llamada `index`.
- Si se define `theme`, su valor debe ser `light` o `dark`.

> El atributo `contact` del ejemplo usa el marcador `TU_CORREO_AQUI`.
> **Reemplázalo por un correo real antes de la demostración final.**

---

## 📁 Estructura del Proyecto

```
option-vercel/
├── Dockerfile              # Imagen con Java + ANTLR 4.13.2 + Python 3 + deps
├── .dockerignore
├── .gitignore              # Ignora .env y el código generado por ANTLR
├── requirements.txt        # requests + antlr4-python3-runtime==4.13.2
├── python-venv.sh
├── commands/
│   ├── antlr               # atajo -> java -jar antlr-4.13.2-complete.jar
│   └── grun                # atajo -> TestRig de ANTLR
├── scripts/                # Parte 1: exploración de las APIs con curl
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── create_repo.sh
│   ├── push_file.sh
│   └── deploy_to_vercel.sh
├── program/                # Parte 2: el compilador
│   ├── SiteLang.g4         # La gramática ANTLR — el corazón del DSL
│   ├── Driver.py           # Punto de entrada: CLI, parseo y orquestación
│   ├── SiteListener.py     # Listener: extrae el modelo y coordina el deploy
│   ├── html_generator.py   # Generación de código: modelo -> HTML
│   ├── validation.py       # Validación semántica del sitio
│   ├── deploy_api.py       # Clientes REST de GitHub y Vercel
│   ├── site.sl             # Tu programa (edita esto)
│   ├── .env.example        # Plantilla de variables de entorno
│   └── .env                # Tus tokens reales (NO subir a GitHub)
└── tests/                  # Pruebas con unittest + unittest.mock
    ├── _support.py
    ├── fixtures/*.sl
    └── test_*.py
```

Los archivos que ANTLR genera (`SiteLangLexer.py`, `SiteLangParser.py`,
`SiteLangListener.py`, `*.tokens`, `*.interp`) **no se versionan**: se generan
en cada ejecución con el comando `antlr` y están en `.gitignore`.

---

## 🔑 Configurar las Credenciales

### 1. Crear un Personal Access Token de GitHub

1. Ve a [github.com/settings/tokens](https://github.com/settings/tokens).
2. **Generate new token (classic)**, nombre `lab3-compiler`.
3. Marca el scope ✅ **repo** y genera el token (se muestra una sola vez).

### 2. Crear un API Token de Vercel

1. Ve a [vercel.com/account/tokens](https://vercel.com/account/tokens).
2. **Create**, nombre `lab3-compiler`, y copia el token.

### 3. Crear el archivo `.env`

```bash
cp program/.env.example program/.env
```

Edita `program/.env`:

```
GITHUB_TOKEN=ghp_tuTokenDeGitHubAqui
VERCEL_TOKEN=tuTokenDeVercelAqui
```

> ⚠️ **`program/.env` contiene tus tokens.** Está en `.gitignore` y **nunca**
> debe subirse a GitHub. Si alguien obtiene tus tokens puede crear repositorios
> y deployments en tu nombre. Si crees que se filtró un token, revócalo de
> inmediato en GitHub/Vercel y genera uno nuevo.

---

## 🧰 Parte 1: Explorar las APIs Directamente con `curl`

Antes de que ANTLR lo automatice, llama tú mismo a las APIs de GitHub y Vercel
con `curl` desde un contenedor Docker. Requiere tener ya tu `program/.env`.

Desde la carpeta `scripts/`:

```bash
docker-compose build

docker-compose run --rm api-explorer bash create_repo.sh       # POST /user/repos
docker-compose run --rm api-explorer bash push_file.sh         # PUT  /repos/.../contents/index.html
docker-compose run --rm api-explorer bash deploy_to_vercel.sh  # POST /v13/deployments
```

Cada script lee los tokens desde las variables de entorno, usa `set -e`, detecta
respuestas de error y **no imprime los tokens**. Tres llamadas `curl`, tres
APIs, un sitio publicado en internet — exactamente lo que la Parte 2 automatiza.

---

## 🐳 Parte 2: Construir la Imagen del Compilador

Desde `option-vercel/`:

```bash
docker build --rm . -t lab3-vercel
```

## 🔧 Ejecutar el Compilador (compilación + deployment real)

```bash
docker run --rm \
  --env-file program/.env \
  -v "$(pwd)/program":/program \
  lab3-vercel bash -c "antlr -Dlanguage=Python3 -listener SiteLang.g4 && python3 Driver.py site.sl"
```

Este comando, en un solo paso:

1. Genera el lexer y el parser a partir de `SiteLang.g4`.
2. Parsea `site.sl` y construye el árbol sintáctico.
3. El listener recorre el árbol y extrae el modelo del sitio.
4. Se valida el modelo (nombre, página `index`, tema).
5. Se genera `index.html` estilizado (generación de código).
6. Se crea un repositorio público en GitHub y se sube el HTML (API de contenidos).
7. Se despliega el HTML en Vercel (API de deployments) y se imprime la URL.

## 📤 Salida Esperada

```
[*] Compiling site definition 'javier-valladares-sitelang-lab3'...
[+] GitHub repo ready: https://github.com/tu-usuario/javier-valladares-sitelang-lab3
[+] index.html pushed to GitHub
[✓] Deployed to Vercel: https://javier-valladares-sitelang-lab3-abc123.vercel.app

[✓] Done! Your compiler just deployed a live website.
```

Abre la URL de Vercel en tu navegador: tu compilador acaba de construir y
publicar un sitio web real.

---

## 🧪 Prueba Local Sin Deployment (`--dry-run`)

Puedes ejecutar todo el pipeline (parseo → validación → generación de HTML)
**sin tokens y sin llamar a ninguna API**. Es ideal para probar tu `.sl` y ver
el HTML antes de desplegar:

```bash
docker run --rm \
  -v "$(pwd)/program":/program \
  lab3-vercel bash -c "antlr -Dlanguage=Python3 -listener SiteLang.g4 && python3 Driver.py site.sl --dry-run"
```

Esto genera `program/index.html` localmente y no toca GitHub ni Vercel.

### Ejecutar las pruebas

Las pruebas usan `unittest` + `unittest.mock` (las llamadas HTTP están
simuladas, **no** crean repos ni deployments reales):

```bash
docker run --rm \
  -e ANTLR_JAR=/usr/local/lib/antlr-4.13.2-complete.jar \
  -v "$(pwd)":/opt/lab -w /opt/lab/tests \
  lab3-vercel python3 -m unittest discover -p 'test_*.py' -v
```

Cubren: un `.sl` válido, uno con error sintáctico, uno sin página `index`, un
tema inválido, variables de entorno faltantes, y respuestas simuladas
(éxito y error HTTP) de GitHub y Vercel.

---

## 🩹 Errores Comunes

| Mensaje | Causa y solución |
|--------|------------------|
| `input file not found: site.sl` | Ruta incorrecta; ejecuta desde `/program` (el volumen montado). |
| `GITHUB_TOKEN and VERCEL_TOKEN must be set` | Falta `program/.env` o está incompleto. Usa `--dry-run` si no quieres desplegar. |
| `the SiteLang file has syntax errors` | Revisa llaves, comillas y el `=`. El deployment se detiene: no se llama a ninguna API. |
| `a page named "index" is required` | Tu `.sl` no define `page "index" { ... }`. |
| `theme "..." is invalid` | Usa `theme = "light"` o `theme = "dark"`. |
| `GitHub ... failed (401, authentication failed ...)` | Token de GitHub inválido o expirado. |
| `GitHub ... failed (403, permission denied ...)` | El token no tiene el scope `repo`. |
| `Repo '...' already exists — reusing it.` | No es un error: en una segunda ejecución el repo se reutiliza y `index.html` se actualiza. |
| `Vercel deployment failed (401/403, ...)` | Token de Vercel inválido. |
| `network error contacting GitHub/Vercel` | Sin conexión o API caída. |

Los errores previsibles se muestran como mensajes claros (con el código HTTP)
y **nunca** revelan los tokens.

---

## 📦 Entregables

- **Video de YouTube no listado** mostrando el compilador corriendo, la URL de
  Vercel impresa, y el sitio abierto en el navegador (ver `GUIA_VIDEO.md`).
- **Repositorio de GitHub** con el código fuente: `SiteLang.g4`, `Driver.py`,
  `SiteListener.py`, `html_generator.py`, `validation.py`, `deploy_api.py`,
  `site.sl`, `Dockerfile`, `.env.example`, scripts de la Parte 1 y `tests/`.
  **No subas `program/.env`.**
- **Escrito breve** (`INFORME.md`): cómo tu compilador mapea a Vercel CLI /
  Netlify CLI.

---

## 🧹 Limpiar los Recursos de Prueba

Cada ejecución real crea un repo en GitHub y un deployment en Vercel. Para no
acumular basura durante las pruebas:

- **GitHub:** borra el repo en `https://github.com/tu-usuario/<repo>` →
  *Settings* → *Delete this repository*. (O vía API:
  `DELETE /repos/{owner}/{repo}` con un token que tenga el scope `delete_repo`.)
- **Vercel:** en el dashboard, entra al proyecto → *Settings* → *Delete Project*,
  o elimina deployments individuales desde la pestaña *Deployments*.
- **Local:** borra `program/index.html` y los archivos generados por ANTLR
  (`SiteLang*.py`, `*.tokens`, `*.interp`); ya están en `.gitignore`.
