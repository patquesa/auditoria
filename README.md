# ⚖️🛡️ Panel GRC: Auditoría de Seguridad en Microsoft Entra ID + Vigilancia Normativa (BOE)

## 💡 Cómo nace la idea
Esta herramienta nace de unir dos mundos que en las empresas suelen ir por separado: **la seguridad informática** y **el cumplimiento legal**.

A la hora de plantear una auditoría sobre un entorno de Microsoft (Tenant), el enfoque habitual es puramente técnico (sacar listados de usuarios o configuraciones). Sin embargo, desde una perspectiva de **Derecho Digital y Cumplimiento Normativo (GRC)**, un dato técnico aislado no sirve si no se interpreta bajo la ley aplicable (RGPD, Esquema Nacional de Seguridad o Directiva NIS2).

Por eso, la solución propuesta combina en un único panel visual:
1. **Mirar hacia dentro:** Revisar los puntos críticos de acceso y seguridad de la empresa en Microsoft.
2. **Mirar hacia fuera:** Vigilar en tiempo real el Boletín Oficial del Estado (BOE) para detectar nuevas normas sobre ciberseguridad y protección de datos que obliguen a tomar medidas.

---

## 🎯 ¿Qué problema soluciona?
- **Traduce datos técnicos a riesgos legales y de negocio:** No solo muestra quién tiene permisos o qué credenciales caducan, sino por qué eso supone un riesgo de fuga de datos (Art. 32 RGPD) o de interrupción del servicio (NIS2 / ENS).
- **Centraliza la vigilancia normativa:** Evita tener que revisar manualmente el BOE cada día en busca de novedades sobre ciberseguridad, generando alertas automáticas y permitiendo abrir el documento oficial (HTML o PDF) con un solo clic desde el propio panel.
- **Facilita la toma de decisiones:** Ofrece una vista ejecutiva rápida tanto para perfiles técnicos (IT/Sistemas) como para responsables de cumplimiento (DPO/Legal).

---

## ⚙️ ¿Cómo funciona?
El panel se divide en dos bloques principales conectados en tiempo real:

### 1. Auditoría interna del entorno Microsoft (Microsoft Graph)
La aplicación se conecta al entorno de la empresa (**Tenant**) utilizando permisos exclusivamente de **lectura** (sigendo el principio de mínimo privilegio: puede auditar, pero nunca modificar ni borrar nada). Analiza tres vectores clave:
- **Cuentas con privilegios máximos (`Global Administrators`):** Controla cuántas personas tienen el control total del sistema para evitar abusos o accesos no autorizados.
- **Usuarios externos invitados (`Guests`):** Identifica a proveedores o colaboradores externos con acceso activo a la información corporativa.
- **Caducidad de credenciales de aplicaciones:** Detecta claves internas caducadas o a punto de caducar que podrían provocar la caída de servicios críticos.

*(Nota: Incluye un **Modo Demo** integrado que permite visualizar y probar todo el panel con datos simulados sin necesidad de conectar un entorno real).*

### 2. Sistema de alertas normativas (API Datos Abiertos del BOE)
De forma automática, la herramienta consulta los sumarios oficiales publicados en el BOE durante los últimos días (configurable de 1 a 14 días), filtra las disposiciones relacionadas con **ciberseguridad, protección de datos, inteligencia artificial o servicios digitales**, lanza un aviso visual si detecta novedades y ofrece enlaces directos para leer la norma o descargar el PDF oficial. Además, incluye en el lateral acceso directo a las leyes base de referencia (ENS y LOPDGDD).

---

## 🛠️ Herramientas utilizadas
Para construir una solución funcional, segura y rápida de desplegar se ha utilizado un entorno ligero basado en Python:
- **Python:** Lenguaje principal para la lógica de conexión, filtrado y análisis de datos.
- **Microsoft Graph API:** Puerta de enlace oficial de Microsoft para extraer la información de seguridad de usuarios, roles y aplicaciones.
- **MSAL (Microsoft Authentication Library):** Librería oficial para gestionar la conexión segura mediante credenciales de aplicación.
- **API de Datos Abiertos del BOE:** Fuente pública oficial para obtener el sumario diario del Boletín Oficial del Estado en formato estructurado.
- **Streamlit y Pandas:** Herramientas utilizadas para procesar la información y transformarla en un panel web interactivo sin necesidad de desarrollar un frontend complejo desde cero.

---

## 🚀 Cómo ponerlo en marcha

**Crear entorno virtual e instalar dependencias:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```


### 🔄 Siguientes ejecuciones
Una vez instalado el entorno, para volver a levantar el panel en cualquier momento basta con activar el entorno virtual y arrancar Streamlit:

```bash
source venv/bin/activate
streamlit run dashboard_grc.py
```
### ¿Qué falta para usarlo con datos reales de una empresa?
No hay que programar nada más; solo configurar las credenciales en el portal de Microsoft (unos 3 minutos):
1. Registrar la aplicación en **Microsoft Entra ID** para obtener sus 3 claves (`TENANT_ID`, `CLIENT_ID` y `CLIENT_SECRET`).
2. Darle permisos de **solo lectura** (`User.Read.All`, `Directory.Read.All` y `Application.Read.All`).
3. Desactivar el interruptor **"Modo Demo"** en el menú lateral del panel y pegar esas 3 claves.