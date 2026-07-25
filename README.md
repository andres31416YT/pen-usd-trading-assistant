# PEN/USD Trading Assistant — Despliegue

Repositorio de despliegue del asistente de trading PEN/USD. Contiene los
servicios de aplicacion (frontend, autenticacion, backend), la infraestructura
como codigo (Terraform) y los workflows de CI/CD (GitHub Actions) para
desplegar todo en **Render**.

> Este repo NO contiene el entrenamiento del modelo ni el dataset — esos
> viven en sus propios repositorios en Hugging Face:
> - Dataset: `andres31416/pen-usd-trading-dataset`
> - Modelo: `andres31416/pen-usd-trading-model`
>
> Este repo se encarga de **servir** ese modelo ya entrenado dentro de una
> arquitectura de produccion con autenticacion, backend y base de datos.

---

## 1. Arquitectura

```
                          ┌──────────────────┐
                          │                  │
                          │     Frontend     │
                          │  (React / Vite)  │
                          │                  │
                          └───────┬────┬─────┘
                                  │    │
                     (1) Login    │    │  (2) Peticiones autenticadas
                                  │    │      (ya con sesion iniciada)
                                  ▼    ▼
                     ┌────────────┐  ┌──────────────────┐
                     │            │  │                  │
                     │   Acceso   │  │     Backend      │
                     │  (Auth)    │  │   (API + logica  │
                     │            │  │    de negocio)    │
                     └─────┬──────┘  └────┬─────────┬────┘
                           │              │         │
                           │              │         │
                           ▼              ▼         ▼
                     ┌───────────────────────┐  ┌──────────────┐
                     │                       │  │              │
                     │   PostgreSQL (Render) │  │    Modelo    │
                     │                       │  │  (PatchTST)  │
                     └───────────────────────┘  │  Transformer │
                                                 │              │
                                                 └──────────────┘
```

### Flujo de comunicacion

1. **Front -> Acceso**: el usuario inicia sesion (login/registro). El
   servicio de **Acceso** valida credenciales contra **su propia conexion**
   a la base de datos PostgreSQL y devuelve un token (JWT) al frontend.
2. **Front -> Backend**: una vez autenticado, el frontend usa ese token
   para consumir el **Backend**, que expone los endpoints de negocio
   (historico de precios, señales de trading, alarmas combinadas, etc).
3. **Backend -> Modelo**: el backend carga el checkpoint del modelo
   (`best_model.pt`, entrenado en el repo `pen-usd-trading-model`) y lo
   usa para generar predicciones + señales bajo demanda.
4. **Backend -> DB**: el backend persiste historico de señales generadas,
   logs de uso, configuracion de usuario, etc, en la **misma instancia**
   de PostgreSQL (en un esquema/tablas separadas de las de Acceso).

### Por que separar "Acceso" del "Backend"

- **Seguridad**: el servicio de autenticacion es la unica pieza que
  maneja contraseñas/tokens; el backend de negocio nunca necesita tocar
  credenciales directamente, solo valida el token recibido.
- **Escalabilidad independiente**: en Render, cada servicio escala por
  separado. El backend (que corre el modelo, mas pesado en CPU/RAM) puede
  escalar distinto al servicio de Acceso (mas liviano).
- **Separacion de responsabilidades**: si en el futuro se agrega OAuth,
  2FA, o un proveedor externo de identidad, solo se toca el servicio de
  Acceso, sin afectar la logica de trading del backend.

---

## 2. Estructura del repositorio

```
pen-usd-trading-deploy/
│
├── README.md                        # Este archivo
├── .gitignore
├── docker-compose.yml                # Levanta todo el stack en local
├── .env.example                      # Plantilla de variables de entorno
│
├── app/                              # Codigo de aplicacion
│   ├── frontend/
│   │   ├── Dockerfile
│   │   ├── .dockerignore
│   │   ├── package.json
│   │   └── src/
│   │       ├── pages/
│   │       ├── components/
│   │       └── services/             # Clientes HTTP hacia Acceso y Backend
│   │
│   ├── auth-service/                 # "Acceso"
│   │   ├── Dockerfile
│   │   ├── .dockerignore
│   │   ├── requirements.txt
│   │   └── src/
│   │       ├── main.py               # API de login/registro/JWT
│   │       ├── models/               # Modelos de tabla (usuarios, sesiones)
│   │       └── db/                   # Conexion a PostgreSQL
│   │
│   ├── backend/
│   │   ├── Dockerfile
│   │   ├── .dockerignore
│   │   ├── requirements.txt
│   │   └── src/
│   │       ├── main.py               # API principal (FastAPI)
│   │       ├── routes/
│   │       │   ├── predictions.py    # Consume el modelo
│   │       │   ├── senales.py        # Alarma combinada
│   │       │   └── historico.py
│   │       ├── model_loader/          # Carga el checkpoint del modelo
│   │       │   └── load_model.py
│   │       └── db/                   # Conexion a PostgreSQL (otro esquema)
│   │
│   └── model/                        # Artefactos del modelo listos para servir
│       ├── best_model.pt             # Descargado desde el repo HF del modelo
│       └── model_config.json
│
├── infrastructure/                   # Infraestructura como codigo (Terraform)
│   └── terraform/
│       ├── main.tf                    # Recursos principales de Render
│       ├── variables.tf               # Variables (region, plan, nombres)
│       ├── outputs.tf                 # URLs/endpoints generados
│       ├── providers.tf               # Provider de Render + backend de estado
│       ├── terraform.tfvars.example   # Plantilla de valores
│       └── modules/
│           ├── render-service/         # Modulo reusable por servicio (front/auth/backend)
│           └── render-postgres/        # Modulo para la base de datos gestionada
│
├── .github/
│   └── workflows/
│       ├── ci.yml                     # Tests + build de las 3 imagenes en cada PR
│       ├── cd-frontend.yml            # Deploy automatico del frontend a Render
│       ├── cd-auth-service.yml        # Deploy automatico del servicio de Acceso
│       ├── cd-backend.yml             # Deploy automatico del backend
│       └── terraform-plan-apply.yml   # Plan/Apply de Terraform sobre infrastructure/
│
└── docs/
    └── arquitectura.md                # Diagramas y decisiones tecnicas ampliadas
```

---

## 3. Contenedores (Docker)

Cada servicio (`frontend`, `auth-service`, `backend`) tiene su propio
`Dockerfile` independiente, siguiendo buenas practicas:

- **Multi-stage builds**: una etapa de build (instala dependencias,
  compila) y una etapa final minima (solo el runtime + artefactos),
  para imagenes mas livianas y con menor superficie de ataque.
- **Usuario no-root** dentro del contenedor.
- **`.dockerignore`** en cada servicio, para no copiar `node_modules/`,
  `venv/`, archivos `.env`, ni el historico de git dentro de la imagen.
- Variables de entorno inyectadas en tiempo de ejecucion (nunca
  hardcodeadas en el Dockerfile ni en el codigo).

### `docker-compose.yml` (entorno local)

Permite levantar los 3 servicios + una instancia local de PostgreSQL con
un solo comando, replicando (de forma aproximada) el entorno de Render:

```bash
docker compose up --build
```

Esto es solo para desarrollo local; en Render cada servicio se despliega
como un servicio independiente (no se usa docker-compose en produccion,
Render orquesta cada contenedor por separado).

---

## 4. Base de datos: PostgreSQL en Render

Se usa el **PostgreSQL gestionado de Render** (Render Postgres), en vez de
levantar un contenedor propio de base de datos en produccion. Ventajas:

- Backups automaticos gestionados por Render.
- Conexion interna privada (network privado de Render) entre los
  servicios (`auth-service`, `backend`) y la base de datos, sin exponer
  el puerto de PostgreSQL a internet.
- Una sola instancia de PostgreSQL, con **dos esquemas separados**:
  - `auth` -> tablas de usuarios, sesiones, tokens (usado solo por
    `auth-service`)
  - `trading` -> tablas de historico de señales, logs de predicciones,
    configuracion de usuario (usado solo por `backend`)

Esta separacion por esquema (en vez de bases de datos separadas) permite
compartir la misma instancia de Render Postgres (mas economico en planes
iniciales) sin mezclar responsabilidades entre Acceso y Backend.

---

## 5. Infraestructura como Codigo (`infrastructure/terraform`)

Se usa el **provider de Terraform para Render** (`render-oss/render`)
para declarar toda la infraestructura de forma reproducible:

- `render_web_service` para `frontend`, `auth-service` y `backend`
  (cada uno apuntando a su Dockerfile correspondiente).
- `render_postgres` para la base de datos gestionada.
- Variables de entorno de cada servicio declaradas como
  `render_env_group` o directamente en el recurso del servicio,
  referenciando secretos desde GitHub Actions (nunca hardcodeados en
  el `.tf`).

Flujo de trabajo:

```bash
cd infrastructure/terraform
terraform init
terraform plan   -var-file="terraform.tfvars"
terraform apply  -var-file="terraform.tfvars"
```

En CI/CD, esto se automatiza con el workflow
`terraform-plan-apply.yml`: cada Pull Request corre `terraform plan`
(para revisar cambios antes de aplicarlos), y al hacer merge a `main`
se ejecuta `terraform apply` automaticamente.

El estado de Terraform (`terraform.tfstate`) se guarda en un backend
remoto (ej. un bucket de almacenamiento con locking), **nunca** en el
repositorio de Git.

---

## 6. CI/CD (`.github/workflows`)

| Workflow | Disparador | Que hace |
|---|---|---|
| `ci.yml` | Cada Pull Request | Corre tests unitarios y linters de los 3 servicios, y verifica que las 3 imagenes de Docker compilen sin errores |
| `cd-frontend.yml` | Push a `main` (cambios en `app/frontend/`) | Construye la imagen y dispara el deploy hook de Render para el servicio de frontend |
| `cd-auth-service.yml` | Push a `main` (cambios en `app/auth-service/`) | Construye la imagen y dispara el deploy hook de Render para Acceso |
| `cd-backend.yml` | Push a `main` (cambios en `app/backend/` o `app/model/`) | Construye la imagen, descarga el checkpoint mas reciente del modelo desde Hugging Face, y dispara el deploy hook de Render para el backend |
| `terraform-plan-apply.yml` | PR (plan) / Push a `main` (apply) | Gestiona la infraestructura declarada en `infrastructure/terraform` |

### Deploys condicionados por carpeta ("path filtering")

Cada workflow de CD solo se dispara si hubo cambios dentro de la carpeta
del servicio correspondiente (usando `paths:` en el trigger de GitHub
Actions). Esto evita reconstruir y redeployar el frontend cuando solo
cambio el backend, por ejemplo.

### Secretos necesarios en GitHub Actions

Configurar en **Settings -> Secrets and variables -> Actions** del repo:

- `RENDER_API_KEY` — para autenticar el Terraform provider y los deploy hooks
- `RENDER_DEPLOY_HOOK_FRONTEND`
- `RENDER_DEPLOY_HOOK_AUTH`
- `RENDER_DEPLOY_HOOK_BACKEND`
- `HF_TOKEN` — para descargar el checkpoint del modelo desde Hugging Face en el pipeline de backend
- `DATABASE_URL` — (o gestionado directamente por Render como variable inyectada automaticamente al vincular el servicio con la base de datos)

---

## 7. Variables de entorno por servicio

### `app/auth-service/.env`
```
DATABASE_URL=postgresql://usuario:password@host:5432/dbname?schema=auth
JWT_SECRET=<secreto-para-firmar-tokens>
JWT_EXPIRATION=3600
```

### `app/backend/.env`
```
DATABASE_URL=postgresql://usuario:password@host:5432/dbname?schema=trading
AUTH_SERVICE_URL=https://acceso.tu-dominio.com
MODEL_CHECKPOINT_PATH=/app/model/best_model.pt
BANK_SPREAD_MULTIPLIER=1.0
```

### `app/frontend/.env`
```
VITE_AUTH_API_URL=https://acceso.tu-dominio.com
VITE_BACKEND_API_URL=https://backend.tu-dominio.com
```

Nunca se commitean los `.env` reales — solo `.env.example` con las
claves (sin valores sensibles). Los valores reales se configuran
directamente en el panel de Render (o via Terraform, referenciando
secretos de GitHub Actions).

---

## 8. Orden recomendado para el primer despliegue

1. Crear el repositorio en GitHub con esta estructura.
2. Configurar los secretos necesarios en GitHub Actions (seccion 6).
3. Ejecutar `terraform apply` (manual la primera vez, o via el workflow)
   para crear: la base de datos PostgreSQL, y los 3 servicios web en Render.
4. Verificar que `auth-service` puede conectarse a PostgreSQL y correr sus
   migraciones iniciales (creacion de tablas de usuarios).
5. Verificar que `backend` puede descargar/cargar el checkpoint del
   modelo y responder al endpoint de salud (`/health`).
6. Verificar que `frontend` puede alcanzar tanto a `auth-service` como a
   `backend` a traves de sus URLs publicas de Render.
7. Hacer un primer login de prueba de punta a punta (Front -> Acceso ->
   DB -> token -> Front -> Backend -> Modelo -> respuesta).

---

## 9. Notas importantes

- Este repositorio asume que el **entrenamiento** del modelo ya ocurrio
  en el repo `pen-usd-trading-model` (Hugging Face). Aqui solo se
  **descarga y sirve** el checkpoint ya entrenado — no se re-entrena
  nada en produccion.
- La actualizacion incremental del modelo (`incremental_update.py`,
  definida en el repo del modelo) se ejecuta como un proceso aparte
  (ej. un cron job o un workflow programado), y su resultado (nuevo
  checkpoint) se publica de vuelta al repo de Hugging Face; el backend
  de este repo simplemente descarga la version mas reciente en cada
  deploy o en un intervalo programado.
- Este proyecto es una herramienta de apoyo a la decision de trading,
  no un sistema de ejecucion automatica de ordenes contra un broker real
  por si solo — la conexion a un broker especifico (si se agrega en el
  futuro) deberia tratarse como un servicio adicional, con su propia
  capa de seguridad y confirmaciones explicitas del usuario.