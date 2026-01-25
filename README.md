# PicooHelloWorld - Automated Research Data Extraction & Visualization

Proyecto de automatización con **Playwright** para extraer datos de investigadores de la Universidad de Salamanca (USAL) y visualizarlos en un panel LED Pixoo.

## 📋 Características

- **Automatización Web**: Extrae datos de publicaciones, tesis, financiación y proyectos de investigación
- **SAML2 Authentication**: Pruebas de login federated con USAL IdP
- **Extracción de TFG/TFM**: Recupera trabajos fin de grado supervisados con paginación
- **JSON Consolidado**: Todos los datos se guardan en un único archivo `all-results.json`
- **Visualización LED**: Script Python que lee los datos y los muestra en pantalla Pixoo 64x64
- **CI/CD Automático**: GitHub Actions ejecuta tests automáticamente en push/PR y diariamente

## 🎯 Datos Extraídos

El proyecto recolecta y almacena:

- **Publicaciones**: Por tipo y por cuartiles JIF (Q1-Q4)
- **Tesis Dirigidas**: Número total de tesis supervisadas
- **Financiación**: Total de proyectos y dinero gestionado
- **Proyectos por Tipo**: 
  - IP Nacionales
  - IP Regionales
  - IP Innovación Docente
  - Otros
- **Docencia**:
  - TFM Supervisados
  - Prácticas Supervisadas
  - Cursos Impartidos
  - Cursos Recibidos
- **Propiedad Intelectual**:
  - Patentes
  - Registros de Utilidad

## 🚀 Inicio Rápido

### Instalación

```bash
# Clonar el repositorio
git clone https://github.com/gabri15/PicooHelloWorld.git
cd PicooHelloWorld

# Instalar dependencias
npm ci

# Instalar navegadores Playwright
npx playwright install --with-deps
```

### Ejecutar Tests

```bash
# Ejecutar todos los tests
npx playwright test

# Modo interactivo (UI)
npx playwright test --ui

# Debug con inspector
npx playwright test --debug

# Ver último reporte HTML
npx playwright show-report
```

### Visualizar Datos en Pixoo

```bash
# Los tests generan: tests/test-results/extracted-data/all-results.json
# Luego ejecuta el script de visualización:
cd tests
python screen.py
```

## 📁 Estructura del Proyecto

```
PicooHelloWorld/
├── tests/
│   ├── example.spec.ts          # Tests principales (login, TFG)
│   ├── screen.py                # Visualización en Pixoo LED
│   └── test-results/
│       └── extracted-data/
│           └── all-results.json  # Datos consolidados (generado)
├── .github/
│   ├── workflows/
│   │   └── playwright.yml       # CI/CD automation
│   └── copilot-instructions.md  # Instrucciones para IA
├── playwright.config.ts          # Configuración Playwright
├── package.json                  # Dependencias
├── .gitignore                    # Archivos ignorados
└── README.md                     # Este archivo
```

## 🔧 Configuración

### Credenciales SAML

En [tests/example.spec.ts](tests/example.spec.ts), actualiza:

```typescript
const CREDENTIALS = {
  username: 'tu_usuario',
  password: 'tu_contraseña',
};
```

### URLs Base

```typescript
const RESEARCHER_ID = '57921';  // Cambia al ID de investigador
const BASE_URL = 'https://produccioncientifica.usal.es';
```

### Configuración Pixoo

En [tests/screen.py](tests/screen.py), actualiza la IP:

```python
PIXOO_IP = "192.168.0.21"  # IP de tu dispositivo Pixoo
```

## 📊 Salida JSON

El archivo `all-results.json` tiene esta estructura:

```json
{
  "timestamp": "2026-01-25T10:30:00.000Z",
  "tests": {
    "login-automatico": {
      "publicationTypes": [...],
      "supervisedTheses": 5,
      "funding": {
        "totalProjects": 60,
        "totalMoney": "€ 500,000.00"
      },
      "projectsByType": {
        "ipNacionales": 1,
        "ipRegionales": 2,
        "ipInnovacionDocente": 13,
        "otros": 90
      },
      "tfmSupervisadas": 10,
      "practicasSupervisadas": 80,
      "patentes": 5,
      "registrosDeUtilidad": 70,
      "cursosdocentesImpartidos": 21,
      "cursosdocentesRecibidos": 41,
      "publicationsByJIFQuartiles": [...]
    },
    "recuperacion-tfg": [...]
  }
}
```

## 🔄 CI/CD Pipeline

Los tests se ejecutan automáticamente:

- **En push/PR** a `main` o `master`
- **Diariamente** a las 09:00 UTC (configurable en `.github/workflows/playwright.yml`)

Características:
- ✅ 2 reintentos en CI
- ✅ Ejecución serial (1 worker)
- ✅ Traces en primer reintento para debugging
- ✅ HTML report guardado como artifact (30 días)

## 📝 Tests

### Test 1: `login automatico`
Extrae datos públicos y protegidos via SAML2:
- Publicaciones por tipo
- Tesis dirigidas
- Financiación
- Publicaciones por cuartiles JIF (requiere login)

### Test 2: `recuperacion de tfg`
Extrae trabajos fin de grado supervisados:
- Navega frames en diaweb.usal.es
- Itera cursos académicos
- Maneja paginación automática
- Deduplica resultados

## 🛠️ Stack Técnico

- **Playwright**: 1.58.0 - Automatización E2E
- **TypeScript**: Type-safe test code
- **Node.js**: Runtime
- **Python**: Visualización (requests, base64)
- **GitHub Actions**: CI/CD

## 📚 Documentación Adicional

- [Playwright Docs](https://playwright.dev)
- [USAL Producción Científica](https://produccioncientifica.usal.es)
- [Pixoo API](https://github.com/divinerite/pixooapi)

## 📄 Licencia

ISC

## 👤 Autor

Desarrollado para USAL - Extracción de datos de investigación

---

**Última actualización**: Enero 2026
