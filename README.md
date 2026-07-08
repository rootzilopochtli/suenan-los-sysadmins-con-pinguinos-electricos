# 🐧🤖 ¿Sueñan los SysAdmins con pingüinos eléctricos?

![Status](https://img.shields.io/badge/status-en%20desarrollo-orange)
![License](https://img.shields.io/badge/license-MIT-blue)

**Tareas en Linux asistidas con IA (Soberanía y Automatización en el Edge)**

> *"The best Linux engineers will not be replaced by AI, they will be the ones who know how to use it effectively."*
>
> — Ezequiel Lanza & Eduardo Spotti

Repositorio oficial del proyecto y laboratorio abierto sobre la evolución de la administración de sistemas. Diseñado como una prueba de concepto itinerante para demostrar el paso de la automatización estática a la resolución dinámica con Inteligencia Artificial.

## 🚀 El Concepto

La administración de infraestructura genera toneladas de datos, logs y métricas. Enviar información sensible de servidores de producción a APIs de terceros (como OpenAI) suele violar las políticas de seguridad y cumplimiento.

Este proyecto demuestra que **la soberanía tecnológica es posible**. Montamos un asistente de IA 100% local, efímero y seguro utilizando contenedores *rootless*, orquestado enteramente con Ansible. Porque recordar la regla de oro: *la limpieza también es trabajo del sysadmin.*

## 🌌 Nomenclatura y Filosofía (Tributo a la Ciencia Ficción)

Este proyecto no solo explora el futuro de la infraestructura, sino que rinde homenaje a las obras fundacionales de la ciencia ficción que moldearon nuestra visión de la inteligencia artificial. Para despertar la curiosidad y contextualizar los componentes, hemos adoptado la siguiente nomenclatura:

* **PositronicOps (El Concepto):** La evolución natural de DevOps y AIOps. Un guiño a los cerebros positrónicos de Isaac Asimov, donde la infraestructura no solo ejecuta, sino que deduce, protege y remedia siguiendo sus propias directivas.
* **Multivac (El Cerebro):** Nuestro motor de IA local (Ollama). Nombrada en honor a la supercomputadora oracular de Asimov (presente en relatos como *La última pregunta*), a la cual la humanidad consulta cuando la lógica lineal y estática no es suficiente.
* **Daneel (El Orquestador):** Nuestros playbooks de Ansible. Inspirado en *R. Daneel Olivaw*, el robot asimoviano que, operando en las sombras y de forma imperceptible, orquesta la protección y el desarrollo de todo un sistema.
* **PreCogs (Los Agentes):** Los scripts de monitoreo en Python. Tomados de *Minority Report* de Philip K. Dick, su función principal no es reaccionar a la caída del servidor, sino observar el contexto para predecir la anomalía (el "crimen") y alertar a Multivac antes de que el colapso ocurra.
* **Operaciones Hail Mary (Disaster Recovery):** Protocolos de último recurso. En honor a la obra de Andy Weir, representan los scripts de restauración autónoma que se ejecutan cuando el sistema está en un estado crítico, aislado, y la intervención del SysAdmin es imposible.

## 🏗️ Arquitectura del Laboratorio

1. **Multivac (IA Local):** Un modelo de lenguaje ligero (`qwen2.5-coder` o `llama3.2`) ejecutándose a través de **Ollama** dentro de un contenedor **Podman** sin privilegios. Cero basura en el host.
2. **Daneel:** **Ansible** se encarga de crear el escenario, aprovisionar los servicios, y al finalizar, destruir todo rastro de la infraestructura.
3. **Precogs:** Agentes ligeros (escritos en Python) que monitorean la carga de servicios (como Nginx) o cambios en archivos críticos (como `/etc`). Al detectar anomalías, consultan a la IA local para determinar la mejor acción de remediación.

## 🛠️ Requisitos Previos

* Sistema Operativo: Fedora Linux (o distribución compatible)
* Podman instalado
* Ansible y la colección de contenedores (`ansible-galaxy collection install containers.podman`)
* Al menos 8GB - 16GB de RAM disponibles para la inferencia de la IA.

## ⚙️ Uso / Despliegue

El proyecto se divide en fases orquestadas por playbooks de Ansible.

### 1. Despertar a Multivac
Este playbook descarga la imagen de Ollama, levanta el contenedor de Podman y descarga el modelo de IA base, dejándolo listo para recibir peticiones a través de una API REST local.

```
$ ansible-playbook playbooks/01-deploy-multivac.yml
```

_(Más instrucciones de despliegue se agregarán conforme el proyecto avance)._

## 🧹 Limpieza (Tear Down)

Como todo buen SysAdmin, dejamos el entorno tal como lo encontramos. Este playbook detiene y elimina los contenedores, limpiando todo el almacenamiento utilizado.

```
$ ansible-playbook playbooks/99-destroy-all.yml
```

## 📜 Licencia y Contacto
Creado para la comunidad. Si rompes tu servidor de producción con esto, al menos la IA te explicará por qué falló.

---
👤 **Alex (@rootzilopochtli)** *Technical Training Developer en Red Hat | Miembro de Fedora Project | Autor de "Fedora Linux System Administration"*
