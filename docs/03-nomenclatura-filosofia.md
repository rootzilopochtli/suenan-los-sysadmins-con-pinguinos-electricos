## 🌌 Nomenclatura y Filosofía (Tributo a la Ciencia Ficción)

![Banner Conceptual de Nomenclatura y Lore de PositronicOps](../assets/lore-banner.png)

Este proyecto no solo explora el futuro de la infraestructura, sino que rinde homenaje a las obras fundacionales de la ciencia ficción que moldearon nuestra visión de la inteligencia artificial. Para despertar la curiosidad y contextualizar los componentes, hemos organizado nuestra nomenclatura por autor y obra:

### 🤖 Isaac Asimov

#### La Saga de la Fundación
* **El Mulo (El Agente de Estrés):**
  * **Ubicación:** Script `chaos/el_mulo.py` (Locust).
  * **El Porqué:** En la saga, El Mulo es un mutante impredecible capaz de llevar al colapso el plan perfecto y estático de Hari Seldon. En nuestro laboratorio, actúa como una fuerza disruptiva anómala que bombardea la infraestructura con picos de tráfico extremos (DDoS masivos) para estresar las capacidades físicas del clúster, obligándonos a demostrar la necesidad de una remediación inteligente.
* **Gaia (El Balanceador):**
  * **Ubicación:** Topología de Ingress, proxy inverso y balanceo de carga (HAProxy + Nginx) en MicroShift.
  * **El Porqué:** En honor al planeta donde todas las entidades comparten una conciencia colectiva, enrutando y distribuyendo la carga de procesamiento de forma transparente y en perfecta armonía a través de todos sus nodos.
* **Términus (La Base de Datos):**
  * **Ubicación:** Clúster de PostgreSQL operando nativamente en MicroShift (Edge).
  * **El Porqué:** Términus es el planeta remoto, aislado en el borde de la galaxia, elegido para salvaguardar el conocimiento de la humanidad tras la caída del Imperio Central (Trántor). En nuestra arquitectura, cumple exactamente esa función: un nodo de almacenamiento soberano, resiliente y desconectado de la nube pública, garantizando la supervivencia de los datos.

#### Serie de los Robots y Relatos Cortos
* **PositronicOps (El Concepto Central):**
  * **Ubicación:** Nombre y arquitectura global del proyecto.
  * **El Porqué:** Un guiño a los cerebros positrónicos de Asimov, donde la infraestructura no solo ejecuta comandos, sino que deduce, protege y remedia siguiendo sus propias directivas asimovianas.
* **Multivac (El Cerebro):**
  * **Ubicación:** Motor de IA local (Ollama) ejecutándose en contenedores *rootless* dentro del host físico.
  * **El Porqué:** Nombrada en honor a la supercomputadora oracular (presente en relatos como *La última pregunta*), a la cual la humanidad consulta cuando la lógica lineal y estática no es suficiente para resolver un problema.
* **Daneel (El Orquestador):**
  * **Ubicación:** Playbooks de aprovisionamiento en `/magrathea` (Ansible).
  * **El Porqué:** Inspirado en el legendario *R. Daneel Olivaw*, el robot que opera en las sombras y de forma imperceptible para orquestar la protección y el desarrollo de todo un sistema a gran escala.
* **Andrew (El Agente ChatOps):**
  * **Ubicación:** Bot de Telegram centralizado en `precogs/temple.py`.
  * **El Porqué:** Bautizado por el androide protagonista de *El Hombre Bicentenario*, cuyo propósito original era servir e interactuar de forma natural con los humanos. Andrew es nuestra interfaz móvil conversacional que traduce la complejidad de Kubernetes a un chat simple.

### 👁️ Philip K. Dick

#### Minority Report
* **El Templo (El Orquestador Central):**
  * **Ubicación:** Script central `precogs/temple.py`.
  * **El Porqué:** En la historia, es el recinto aislado y sagrado donde los tres Precogs coexisten y analizan el flujo temporal. En el código, es el orquestador maestro que utiliza hilos (*threading*) para mantener a todas las entidades de IA trabajando en paralelo dentro de un solo proceso de Python.
* **Agatha (La Precog Principal):**
  * **Ubicación:** Hilo de ejecución en segundo plano (*background*) dentro del Templo.
  * **El Porqué:** Agatha es la más talentosa de los mutantes capaces de ver los crímenes antes de que sucedan. Como agente ligero, se sumerge en el flujo de logs de Nginx en tiempo real para predecir el colapso (cazando códigos `499` o `50x`), disparando la auto-remediación antes de que la experiencia del usuario caiga.
* **Arthur (El Analista):**
  * **Ubicación:** Hilo de ejecución interactivo (*foreground*) de comandos bajo demanda en el Templo (`/status`).
  * **El Porqué:** Uno de los gemelos Precog, encargado de traducir las visiones a datos duros. En PositronicOps, Arthur es el puente interactivo de lectura que consulta la API de MicroShift y traduce la salida cruda de Kubernetes a un formato tabular amigable en tu celular.
* **Dashiell (El Guardián):**
  * **Ubicación:** Hilo de seguridad y transmisión (WIP) dentro del Templo.
  * **El Porqué:** El segundo gemelo Precog. Su función será el aislamiento y la difusión: operará como un escudo táctico que transmitirá las visiones y alertas a canales de Telegram públicos para demostraciones en vivo, protegiendo al bot principal.

#### ¿Sueñan los androides con ovejas eléctricas? (Blade Runner)
* **Deckard (El Retiro):**
  * **Ubicación:** Script de limpieza `04-teardown-deckard.sh` en `/magrathea`.
  * **El Porqué:** Su trabajo consiste en "retirar" implacablemente a los componentes, redes y máquinas virtuales que ya han cumplido su ciclo de vida dentro del laboratorio, manteniendo el host físico impecable.

### 🪐 Douglas Adams

#### The Hitchhiker's Guide to the Galaxy
* **Magrathea (El Centro de Mando):**
  * **Ubicación:** Directorio principal de aprovisionamiento `/magrathea`.
  * **El Porqué:** Al igual que la mítica fábrica constructora de planetas, es donde ensamblamos infraestructuras complejas desde cero, guiados por el principio del 42 (el asterisco `*` en Bash/Ansible, el comodín que permite crear mundos enteros).

### 🚀 Andy Weir

#### Project Hail Mary
* **Operaciones Hail Mary (Disaster Recovery):**
  * **Ubicación:** Protocolos y scripts de restauración de último recurso.
  * **El Porqué:** Representan las acciones de supervivencia autónoma que se ejecutan cuando el sistema está en un estado crítico, aislado en el Edge, y la intervención manual del SysAdmin es físicamente imposible.

---
👤 **Alex (@rootzilopochtli)** *Technical Training Developer en Red Hat | Miembro de Fedora Project | Autor de "Fedora Linux System Administration"*
