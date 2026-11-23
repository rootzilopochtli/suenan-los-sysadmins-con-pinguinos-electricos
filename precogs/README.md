# 👁️ Precogs v2.0: Observabilidad Predictiva, SysAdmin Autónoma y RAG Offline

En *Minority Report* de Philip K. Dick, los "Precogs" ven los crímenes antes de que sucedan. En **PositronicOps v2.0**, el directorio `/precogs` es el sistema nervioso central de operaciones: combina reflejos deterministas de SysAdmin, inferencia local acotada (**ASD-STE100 + JSON Schema**) y memoria episódica sobre **CentOS Stream 10 + MicroShift** en modo *Airgap*.

## 🌌 Topología de la Solución (v2.0)

```mermaid
flowchart LR
    MULO["💥 El Mulo<br/>(Locust Chaos)"]

    subgraph EDGE["🐧 Nodo Edge: CentOS Stream 10 + MicroShift (100% Airgap)"]
        direction TB
        ROUTE["Ingress Route<br/>gaia.positronic-c.local"]
        NGINX["Gaia Frontend<br/>Nginx (IfNotPresent)"]

        subgraph N0["🟢 Nivel 0: Supervivencia Nativa (K8s)"]
            direction LR
            BACKEND["Gaia Backend (FastAPI)<br/>Probes: /health & /status/db"]
            HPA["HPA<br/>1 → 5 réplicas"]
            HPA -.->|"CPU > 75%"| BACKEND
        end

        DB[("Términus<br/>PostgreSQL StatefulSet")]
        OS["Host Linux<br/>Systemd + Disco/Inodos"]

        ROUTE --> NGINX --> BACKEND --> DB
    end

    subgraph HOST["🏛️ Host Administrativo (calvin-node)"]
        direction TB

        subgraph N1["🟡 Nivel 1: El Templo (temple.py) — AIOps Local"]
            direction TB
            AG["🔮 Agatha (SysAdmin)<br/>Logs Nginx + Hilo 60s"]
            MARVIN["🧹 Marvin<br/>Limpieza Airgap-Safe"]
            LLM["⚡ Multivac (Ollama)<br/>qwen2.5-coder:1.5b<br/>STE-100 + JSON Schema"]
            MEM[("📜 episodic_memory.jsonl<br/>Memoria STE-100")]
            AR["🧠 Arthur<br/>/auditoria & /rag"]
            DA["📊 Dashiell<br/>/status & /perf (Read-Only)"]
        end

        AW["🤖 Andrew<br/>ChatOps + Escudo BOFH"]
    end

    subgraph N2["🔴 Nivel 2: Freno Ético Humano"]
        direction TB
        TG["📱 Telegram + 📧 SMTP<br/>Botones & Post-Mortem"]
        SRE["👤 SRE Humano"]
        TG <--> SRE
    end

    MULO -->|"Ataque HTTP"| ROUTE
    NGINX -.->|"Stream logs"| AG
    OS -.->|"Telemetría SSH"| AG
    OS -.->|"oc top / df"| DA

    AG -->|"Reflejo 0% LLM"| MARVIN
    MARVIN -->|"Purga segura"| OS
    AG <-->|"Prompt STE-100<br/>JSON enum"| LLM
    AG -->|"oc scale / restart"| BACKEND

    AG -->|"Registra episodio"| MEM
    MEM -->|"RAG bilingüe"| AR
    AR <-->|"Síntesis"| LLM

    AG -->|"Ataque persistente"| AW
    AR --> AW
    DA --> AW
    AW <-->|"Alertas / Botones"| TG

    classDef chaos fill:#4a1019,stroke:#ff4d6d,stroke-width:2px,color:#fff;
    classDef n0 fill:#0d3b26,stroke:#2ec4b6,stroke-width:2px,color:#fff;
    classDef n1 fill:#1b263b,stroke:#4ea8de,stroke-width:2px,color:#fff;
    classDef llm fill:#3c1642,stroke:#c77dff,stroke-width:2px,color:#fff;
    classDef n2 fill:#590d22,stroke:#ff758f,stroke-width:2px,color:#fff;

    class MULO chaos;
    class BACKEND,HPA n0;
    class AG,MARVIN,AR,DA,AW n1;
    class LLM,MEM llm;
    class TG,SRE n2;
```

## 🛡️ Defensa en 3 Niveles

1. **Nivel 0 — Supervivencia Nativa (Kubernetes):** `livenessProbe` (`/health`), `readinessProbe` (`/status/db`) y `HPA` (1 → 5 réplicas) absorben carga y fallas triviales sin quemar tokens.
2. **Nivel 1 — SysAdmin Autónoma (Agatha + Multivac):**
   - **Reflejos deterministas (0% LLM):** Saturación de disco/inodos (≥ 90%) invoca a Marvin; caída de `microshift`/`crio` dispara `systemctl`.
   - **Respaldo cognitivo local:** Ante patrones ambiguos, consulta a `qwen2.5-coder:1.5b` (Ollama) con instrucciones **ASD-STE100**, `temperature: 0.0` y **JSON Schema (`format`)** con lista blanca de acciones (`enum`). *El LLM propone; Python valida y dispone.*
3. **Nivel 2 — Freno Ético Humano (Andrew / Telegram + SMTP):** Si una anomalía sobrevive al periodo de gracia, la IA se detiene, despliega botones de contención interactivos y envía el reporte post-mortem por correo electrónico.

## 🏛️ Temple: El Orquestador Central (`temple.py`)

Centraliza el ecosistema mediante hilos sincronizados (`threading.Lock`) y actúa como API Gateway hacia Telegram con escudo BOFH integrado.

**Comandos Operativos Soportados:**
* `/status` - Estado en vivo de contenedores (Dashiell).
* `/perf` - Telemetría de CPU, RAM y Disco físico (Dashiell).
* `/agatha` - Pulso SysAdmin y nivel de amenaza actual (Agatha).
* `/auditoria` - Auditoría incremental sobre memoria episódica y logs (Arthur).
* `/rag <pregunta>` - Consulta RAG interactiva citando *timestamps* exactos (Arthur).
* `/marvin` - Ejecución bajo demanda de limpieza segura *Airgap* (Marvin).
* `/nivel1` - Bitácora estructurada desde `episodic_memory.jsonl`.
* `/resumen` - Dashboard ejecutivo global de defensas.
* `/baneados` - Muro de la Vergüenza (comandos BOFH interceptados).
* `/ping` y `/?` - Enlace y manual de operaciones.

## 🧠 Arthur v2.0: Memoria Episódica y RAG 100% Offline (`arthur.py`)

Cada incidente resuelto o escalado se persiste en `episodic_memory.jsonl` con su resumen en **ASD-STE100**. Arthur realiza recuperación determinista en Python con expansión bilingüe de sinónimos SRE (`disco <-> disk`, `memoria <-> oom`) y sintetiza respuestas con Multivac sin requerir bases vectoriales pesadas en el Edge.

## 🚀 Puesta en Marcha

```bash
cd precogs
cp .env.example .env
vim .env

source ../chaos/venv/bin/activate
python3 temple.py
```

---
👤 **Alex Callejas (`@dark_axl` / `@rootzilopochtli`)** *Technical Training Developer en Red Hat | Líder de Fedora México*
