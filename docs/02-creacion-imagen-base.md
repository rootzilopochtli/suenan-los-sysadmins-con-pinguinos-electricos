# 🏗️ Creación de la Imagen Base con Red Hat Image Builder

Para el despliegue de Daneel se requiere una base sólida. En lugar de una instalación pesada desde un ISO tradicional, utilizaremos una **Virtual Guest Image (.qcow2)** optimizada para la nube y el laboratorio local.

## 🎯 Objetivo
Aprovisionar una imagen de **Red Hat Enterprise Linux (RHEL) 9** personalizada y registrada, lista para ser "secuestrada" por nuestros scripts de automatización.

## 🛠️ Paso a paso: El Proceso de Construcción

### 1. Acceso al Portal
Inicia sesión en el [portal de desarrolladores de Red Hat](https://developers.redhat.com/) y dirígete a la sección de descargas de productos.

### 2. Selección de RHEL 9
Busca la sección de **Red Hat Enterprise Linux** y selecciona la opción de "Más formas de probar" (More ways to try). Es vital desplazarse hasta el apartado de **Cloud ready RHEL images**.

⚠️ **Nota importante:** No descargues el ISO estándar ("Download RHEL at no-cost"). Para este laboratorio Edge, requerimos una imagen preparada para virtualización que Image Builder pueda procesar eficientemente.

### 3. Configuración en Hybrid Cloud Console
Al seleccionar **Virtual Guest image**, serás redirigido al asistente (wizard) de Image Builder en la consola de Red Hat.

1. **Salida de Imagen:** Selecciona *Red Hat Enterprise Linux (RHEL) 9* y la arquitectura de tu equipo (x86_64 o aarch64). Elige el formato **Virtualization - Guest Image (.qcow2)**.
2. **Registro:** Selecciona tu **Llave de activación** (previamente configurada en la [Configuración de Recursos Globales de Red Hat](01-configuracion-recursos.md) del repositorio). Esto asegura que la imagen nazca con acceso a los repositorios oficiales de Red Hat.
3. **Seguridad y Revisión:** En el paso de seguridad, puedes avanzar hacia "Revisar y finalizar" (Review and finish) para mantener la configuración base inmutable.
4. **Creación del Blueprint:** Haz clic en **Create blueprint** para guardar esta configuración técnica.

### 4. Generación y Descarga
Dentro de tu nuevo blueprint:
1. Haz clic en **Build latest images**. El sistema iniciará la creación de la instancia en la infraestructura de Red Hat.
2. Una vez que el estado cambie a "Listo", haz clic en el enlace **Download (.qcow2)**.
3. **Crítico:** Guarda este archivo directamente dentro del directorio `magrathea/` de tu repositorio local para que el script de provisionamiento pueda detectarlo sin problemas.

---
## 🛡️ Siguiente Paso
Con la imagen `.qcow2` en tu poder, ya tienes los cimientos del despliegue. Regresa al manual principal del [Centro de Mando](../magrathea/README.md) para lanzar el Nodo Positrónico.

---

> *Geek by nature, Linux by choice, Fedora of course...*

---
👤 **Alex (@rootzilopochtli)** *Technical Training Developer en Red Hat | Miembro de Fedora Project | Autor de "Fedora Linux System Administration"*
