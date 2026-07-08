# 🐧🤖 ¿Sueñan los SysAdmins con pingüinos eléctricos?

![Status](https://img.shields.io/badge/status-en%20desarrollo-orange)
![License](https://img.shields.io/badge/license-MIT-blue)

**Tareas en Linux asistidas con IA (Soberanía y Automatización en el Edge)**

> *"The best Linux engineers will not be replaced by AI, they will be the ones who know how to use it effectively."*
>
> — Ezequiel Lanza & Eduardo Spotti

Repositorio oficial del proyecto y demostración técnica para **Posadev**. Este laboratorio es un caso práctico sobre cómo evolucionar la administración de sistemas en Linux: pasando de la automatización estática (el viejo y confiable `cron`) a la resolución dinámica de problemas con Inteligencia Artificial.

## 🚀 El Concepto

La administración de infraestructura genera toneladas de datos, logs y métricas. Enviar información sensible de servidores de producción a APIs de terceros (como OpenAI) suele violar las políticas de seguridad y cumplimiento.

Este proyecto demuestra que **la soberanía tecnológica es posible**. Montamos un asistente de IA 100% local, efímero y seguro utilizando contenedores *rootless*, orquestado enteramente con Ansible. Porque recordar la regla de oro: *la limpieza también es trabajo del sysadmin.*

## 🏗️ Arquitectura del Laboratorio

1. **El Cerebro (IA Local):** Un modelo de lenguaje ligero (`qwen2.5-coder` o `llama3.2`) ejecutándose a través de **Ollama** dentro de un contenedor **Podman** sin privilegios. Cero basura en el host.
2. **El Orquestador:** **Ansible** se encarga de crear el escenario, aprovisionar los servicios, y al finalizar, destruir todo rastro de la infraestructura.
3. **El Paciente (Scripts Python):** Agentes ligeros que monitorean la carga de servicios (como Nginx) o cambios en archivos críticos (como `/etc`). Al detectar anomalías, consultan a la IA local para determinar la mejor acción de remediación.

## 🛠️ Requisitos Previos

* Sistema Operativo: Fedora Linux (o distribución compatible)
* Podman instalado
* Ansible y la colección de contenedores (`ansible-galaxy collection install containers.podman`)
* Al menos 8GB - 16GB de RAM disponibles para la inferencia de la IA.

## ⚙️ Uso / Despliegue

El proyecto se divide en fases orquestadas por playbooks de Ansible.

### 1. Despertar al Cerebro
Este playbook descarga la imagen de Ollama, levanta el contenedor de Podman y descarga el modelo de IA base, dejándolo listo para recibir peticiones a través de una API REST local.

```
$ ansible-playbook playbooks/01-deploy-brain.yml
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
