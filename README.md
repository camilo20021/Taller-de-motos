# Motos JL Racing — Sistema de gestión del taller

Sistema web hecho a la medida para **Motos JL Racing** (un único taller) que controla:

- **Clientes y motos**: nombre, cédula, celular, correo y las motos asociadas a cada cliente.
- **Órdenes de servicio**: ingreso y salida de motos, estado (recibida → diagnóstico → en reparación → esperando repuesto → terminado → entregado), diagnóstico y observaciones.
- **Notificación automática por correo**: cuando se marca una orden como "terminado", se envía un correo al cliente avisando que su moto ya está lista.
- **Inventario de repuestos**: stock, stock mínimo, entradas/salidas, y descuento automático de stock cuando se usa un repuesto en una orden.
- **Cotizaciones y facturas**: generadas a partir de los repuestos y mano de obra registrados en cada orden, con IVA calculado.
- **Cierre de caja**: se abre la caja con una base inicial y se cierra contando el efectivo real; el sistema calcula lo esperado (base + ventas pagadas) y muestra el sobrante o faltante.

## Roles de usuario

El sistema tiene dos roles, cada uno con acceso distinto:

| Sección | Administrador | Mecánico |
|---|---|---|
| Panel / dashboard | ✅ completo | ✅ (sin datos de inventario) |
| Ver clientes y motos | ✅ | ✅ |
| Crear / editar / eliminar clientes | ✅ | ❌ |
| Registrar / modificar motos | ✅ | ✅ |
| Órdenes de servicio (ingreso, estado, diagnóstico, repuestos usados) | ✅ | ✅ |
| Inventario (crear repuestos, editar precios, movimientos manuales) | ✅ | ❌ |
| Cotizaciones / facturas | ✅ | ❌ |
| Cierre de caja | ✅ | ❌ |
| Gestión de usuarios | ✅ | ❌ |

Si un mecánico intenta entrar a una sección restringida, ve una página de "Acceso restringido" en vez de romperse.

## Estructura del proyecto

```
Taller de motos/
├── run.py                  Punto de entrada (arranca el servidor)
├── requirements.txt         Dependencias de Python
├── .env.example               Plantilla de configuración (copiar a .env)
├── python/                   Todo el código Python (backend)
│   ├── __init__.py             Fabrica la aplicación Flask + siembra el taller inicial
│   ├── config.py                Configuración (BD, correo, claves, datos del taller/admin)
│   ├── extensions.py             Instancias de SQLAlchemy, Login, Mail
│   ├── models.py                 Modelos de la base de datos
│   ├── decorators.py             Decorador @admin_required para rutas solo-admin
│   ├── email_utils.py            Envío del correo "moto lista"
│   ├── routes_auth.py             Login
│   ├── routes_dashboard.py        Panel principal
│   ├── routes_clientes.py          Clientes y motos
│   ├── routes_ordenes.py           Órdenes de servicio
│   ├── routes_inventario.py        Inventario de repuestos (solo admin)
│   ├── routes_documentos.py        Cotizaciones / facturas (solo admin)
│   ├── routes_caja.py              Cierre de caja (solo admin)
│   └── routes_usuarios.py          Gestión de usuarios (solo admin)
├── css/                      Hojas de estilo
├── js/                       Javascript del lado del cliente
├── img/                      Imágenes (logos, etc.)
├── instance/                 Base de datos SQLite local (se crea sola, no se sube a git)
└── *.html                     Todas las plantillas HTML (sueltas, fuera de css/js/python)
```

## Requisitos

- Python 3.10 o superior.

## Instalación y ejecución local

```bash
# 1. Crear y activar un entorno virtual
python -m venv .venv
.venv\Scripts\activate          # en Windows (PowerShell/CMD)

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables de entorno
copy .env.example .env
# Edita el archivo .env con tus datos (ver secciones de abajo)

# 4. Ejecutar la aplicación
python run.py
```

Abre `http://127.0.0.1:5000` en el navegador.

### Primer ingreso (cuenta administradora)

La primera vez que la app arranca con la base de datos vacía, crea automáticamente:
- El taller **Motos JL Racing** (o el nombre que pongas en `TALLER_NOMBRE` en `.env`).
- Una cuenta de **administrador** con el correo/contraseña que definas en `ADMIN_EMAIL` / `ADMIN_PASSWORD` en `.env` (si no los cambias, por defecto es `admin@motosjlracing.com` / `cambiar123`).

**Entra con esa cuenta y cambia la contraseña cuanto antes.** Desde el menú **Usuarios** (solo visible para el administrador) puedes crear las cuentas de los mecánicos, eligiendo el rol "Mecánico" o "Administrador" para cada una.

## Conectar la base de datos a Supabase (Postgres)

Por defecto la app guarda todo en un archivo SQLite local. Para que los datos queden en Supabase:

1. En el panel de Supabase, entra a **Project Settings → Database → Connection string**, pestaña **URI**, y copia la cadena. Se ve así:
   ```
   postgresql://postgres.xxxxxxxxxxxx:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:5432/postgres
   ```
2. Reemplaza `[YOUR-PASSWORD]` por tu contraseña real de la base de datos.
3. Pega esa cadena completa en tu archivo `.env`, en la línea `DATABASE_URL=...`.
4. Instala dependencias si no lo has hecho (`pip install -r requirements.txt`) — ya incluye el driver `psycopg` necesario para hablar con Postgres.
5. Corre `python run.py`. La primera vez que arranca, la app crea automáticamente todas las tablas dentro de tu proyecto de Supabase (no hay que crear nada a mano en el editor de tablas) y siembra el taller + la cuenta admin ahí mismo.

Puedes verificar que quedó todo en Supabase entrando a **Table Editor** en su panel: deberías ver las tablas `talleres`, `usuarios`, `clientes`, `motos`, `ordenes_servicio`, `repuestos`, `documentos`, `cierres_caja`, etc.

> Importante: el archivo `.env` nunca se sube a git (`.gitignore` ya lo excluye) porque contiene la contraseña real de tu base de datos.

## Configurar el envío de correos ("moto lista")

Cuando se cambia el estado de una orden a **"Terminado"**, el sistema intenta enviar un correo automático al cliente. Para que funcione de verdad necesitas configurar un correo remitente en `.env`:

```
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=tu_correo@gmail.com
MAIL_PASSWORD=tu_clave_de_aplicacion
MAIL_DEFAULT_SENDER=tu_correo@gmail.com
```

Con Gmail: activa la verificación en dos pasos en la cuenta y genera una **"contraseña de aplicación"** (no uses tu contraseña normal). Otros proveedores de correo (Outlook, un correo corporativo, SendGrid, etc.) funcionan igual, solo cambia `MAIL_SERVER` y el puerto.

Si el cliente no tiene correo registrado, o el correo falla, la orden se actualiza igual — el sistema solo muestra un aviso, nunca se rompe por eso.

Para probar sin enviar correos de verdad, pon `MAIL_SUPPRESS_SEND=true` en `.env`.

## Cómo funciona el cierre de caja

1. El administrador **abre la caja** al iniciar el turno/día, ingresando la base inicial (el efectivo con el que arranca).
2. Mientras la caja está abierta, cada factura que se marca como **pagada** queda ligada automáticamente a esa caja.
3. Al final del turno, el administrador **cierra la caja**: cuenta el efectivo físico y lo ingresa.
4. El sistema calcula:
   - **Esperado** = base inicial + ventas pagadas durante ese turno.
   - **Diferencia** = efectivo contado − esperado (positivo = sobrante, negativo = faltante).
5. Queda guardado en el historial de cierres, con quién abrió y quién cerró la caja.

Solo puede haber una caja abierta a la vez.

## Pasar a producción

1. **Servidor**: no usar `python run.py` (servidor de desarrollo). Usar un servidor WSGI como `waitress` (funciona bien en Windows) o `gunicorn` (Linux), detrás de un proveedor de hosting (Render, Railway, un VPS, etc.).
2. **SECRET_KEY**: generar una clave larga y aleatoria distinta a la de desarrollo.
3. **Copias de seguridad**: si usas Supabase, ya tiene respaldos automáticos; si usas SQLite local, programa respaldos periódicos del archivo `instance/taller.db`.

## Flujo típico de uso

1. El administrador crea las cuentas de los mecánicos (`Usuarios → + Nueva cuenta`).
2. El administrador registra un cliente con sus datos (nombre, cédula, celular, correo).
3. Se registra la moto del cliente (placa, marca, modelo...) — esto lo puede hacer el administrador o el mecánico.
4. Cuando el cliente trae la moto, se crea una **orden de servicio** (esto es el "ingreso" de la moto) — lo hace el mecánico.
5. El mecánico va actualizando el estado de la orden y el diagnóstico.
6. Se agregan los repuestos usados (descuentan del inventario automáticamente) y la mano de obra.
7. Al terminar la reparación, se cambia el estado a **"Terminado"** → el cliente recibe un correo automático.
8. El administrador genera la cotización o factura, y la marca como pagada cuando corresponda (queda ligada a la caja abierta).
9. Al entregar la moto, se cambia el estado a **"Entregada"** (esto es la "salida" de la moto).
10. Al final del turno, el administrador cierra la caja y verifica que cuadre.
