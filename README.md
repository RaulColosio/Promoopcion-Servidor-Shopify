# Sincronizador de Catálogo: PromoOpción a Shopify

Este proyecto contiene el código para una aplicación de backend que sincroniza el catálogo de productos del proveedor PromoOpción con una tienda de Shopify. La aplicación está diseñada para ser desplegada en la App Platform de Digital Ocean.

## Funcionalidades

- **Sincronización de Productos:** Crea, actualiza y elimina productos en Shopify basándose en los datos del proveedor.
- **Lógica de Precios Personalizada:** Aplica una fórmula de precios configurable (descuento del proveedor + margen de ganancia) antes de publicar en Shopify.
- **Programación Automática:** Utiliza un trabajo programado (cron job) para ejecutar la sincronización de forma automática.
- **Dashboard (Prototipo):** Incluye un prototipo para un panel de administración para monitorear y configurar la aplicación.

## Estructura del Proyecto

- `promooption_client.py`: Cliente de Python para interactuar con la API de PromoOpción.
- `shopify_client.py`: Cliente de Python para interactuar con la API de Shopify.
- `sync_manager.py`: El script principal que orquesta el proceso de sincronización.
- `requirements.txt`: Lista de las dependencias de Python necesarias.
- `.do/app.yaml`: Archivo de especificaciones para el despliegue en la App Platform de Digital Ocean.
- `dashboard-frontend/`: Carpeta que contiene el prototipo del panel de administración, listo para ser desplegado en Vercel.

## Configuración

Antes de desplegar, es necesario configurar las siguientes credenciales como **variables de entorno**.

### Variables Requeridas

| Variable         | Descripción                                            | Ejemplo                               |
|------------------|--------------------------------------------------------|---------------------------------------|
| `PROMO_USER`     | El usuario para la API de PromoOpción.                 | `MTY4895`                             |
| `PROMO_PASSWORD` | La contraseña para la API de PromoOpción.              | `zzWZqF2ubPKCLSkttula`                |
| `SHOPIFY_URL`    | El dominio `.myshopify.com` de tu tienda.              | `promotienda-mx.myshopify.com`        |
| `SHOPIFY_TOKEN`  | El Token de Acceso de la API de Admin de tu app privada. | `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` |

## Despliegue

El proyecto está diseñado para un despliegue sencillo en dos partes.

### 1. Backend en Digital Ocean

La lógica de sincronización se despliega en la **App Platform de Digital Ocean**.

1.  **Sube el proyecto a GitHub:** Crea un repositorio en GitHub y sube todos los archivos del proyecto.
2.  **Crea una App en Digital Ocean:**
    - En tu panel de Digital Ocean, ve a `Apps` y haz clic en `Create App`.
    - Elige **GitHub** y selecciona el repositorio que acabas de crear.
    - Digital Ocean detectará automáticamente el archivo `.do/app.yaml`. Revisa la configuración que propone y asegúrate de que coincide con el contenido del archivo.
3.  **Configura las Variables de Entorno:**
    - En la página de configuración de la app, ve a la sección de **Environment Variables**.
    - Digital Ocean te pedirá que introduzcas los valores para las variables que definimos en el `app.yaml` (`PROMO_USER`, `SHOPIFY_TOKEN`, etc.). Rellena los valores con tus credenciales. Asegúrate de que estén marcadas como "Secret" para que se encripten.
4.  **Despliega:** Finaliza el proceso de creación. Digital Ocean construirá la aplicación e implementará el trabajo programado (`full-sync`) automáticamente. El cron job comenzará a ejecutarse según el horario definido (diariamente a las 7:05 AM GMT-6).

### 2. Frontend en Vercel

El prototipo del dashboard se puede desplegar fácilmente en **Vercel**.

1.  **Conecta tu cuenta de GitHub a Vercel.**
2.  **Crea un nuevo proyecto en Vercel:**
    - Importa el mismo repositorio de GitHub que usaste para el backend.
    - Cuando Vercel te pida configurar el proyecto, especifica que el **Root Directory** es `dashboard-frontend`.
    - No se necesita ningún framework o comando de build, ya que es un sitio estático.
3.  **Despliega:** Vercel publicará el archivo `index.html` en una URL pública.

*Nota: Para que el dashboard sea completamente funcional, se necesitaría desarrollar la API en el backend (Digital Ocean) y el código JavaScript en el frontend para conectar ambos servicios.*
