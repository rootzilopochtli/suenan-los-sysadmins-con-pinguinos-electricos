# 🪐 Magrathea: Centro de Mando y Despliegue

Al igual que la mítica constructora de planetas de Douglas Adams, este directorio contiene todos los planos (playbooks) y herramientas (scripts) necesarios para ensamblar nuestra infraestructura desde cero, guiados por el principio del 42 (el asterisco `*`, el comodín que permite crear cualquier cosa que el operador decida).

## 📋 Prerrequisitos de Construcción

Antes de ejecutar cualquier orquestación, asegúrate de tener los recursos base. Consulta nuestra documentación oficial en el directorio `docs/`:

* [Configuración de Recursos Globales de Red Hat](../docs/01-configuracion-recursos.md): Pasos para obtener tu cuenta de desarrollador, el Activation Key y el Pull Secret.
* [Creación de la Imagen Base (Golden Image)](../docs/02-creacion-imagen-base.md): Guía para generar tu imagen `.qcow2` optimizada para KVM.

## ⚙️ Instrucciones de Despliegue

El aprovisionamiento se ejecuta en fases estrictamente ordenadas. **Asegúrate de estar posicionado dentro del directorio `magrathea/` en tu terminal antes de comenzar:**

### 1. Despertar a Multivac
Este playbook descarga la imagen de Ollama, levanta el contenedor local de Podman rootless y prepara el modelo de IA base, dejándolo listo para recibir peticiones a través de una API REST.

```bash
$ ansible-playbook playbooks/01-deploy-multivac.yml
```

### 2. Aprovisionar el Hardware (KVM)

Prepara el terreno levantando la máquina virtual que albergará el nodo positrónico. **(Nota: Asegúrate de colocar tu Golden Image y tus llaves SSH dentro de este directorio `magrathea/` antes de ejecutar)**.

```bash
$ ./scripts/02-provision-daneel-kvm.sh
```

### 3. Orquestar el Nodo Positrónico

Daneel (Ansible) entra en acción para instalar y configurar MicroShift en la máquina virtual recién creada, abriendo puertos y habilitando los certificados.

```bash
$ ansible-playbook playbooks/02-deploy-daneel.yml -e "local_ip=<TU_IP> local_key=<TU_LLAVE>"
```

### 4. El Retiro (Tear Down)

Cuando el laboratorio termina, Deckard se encarga de limpiar el entorno de forma segura, eliminando la máquina virtual de KVM y manteniendo el host impoluto.

```bash
$ ./scripts/04-teardown-deckard.sh
```

---
👤 **Alex (@rootzilopochtli)** *Technical Training Developer en Red Hat | Miembro de Fedora Project | Autor de "Fedora Linux System Administration"*
