#!/bin/bash
# set -x
###############################################################################
# Autor: Alex Callejas (@rootzilopochtli)
# Versión: 2.4 (Universal Edition)
# Versión: 2.5 (Dynamic Identity Edition)
# Versión: 2.6 (Exit & Discovery Edition)
# Versión: 2.6.1 (Bug Fix)
# Versión: 2.7 (Hygiene & Safety Edition)
# Versión: 2.8 (Clean & Secure Edition)
# Versión: 2.9 (Pedagogical Edition)
# Versión: 2.9.1 (Generic & Clean Edition)
# Versión: 2.9.2 (Bulletproof Edition)
# Descripción: Validador de salud para MicroShift (Local KVM / AWS / GCP)
# Motto: "Geek by nature, Linux by choice, Fedora of course..."
###############################################################################

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Definición de rutas globales
LOCAL_KUBE_DIR="$HOME/.kube"

echo -e "${YELLOW}##########################################################${NC}"
echo -e "${YELLOW}#   Mando de Control: Querida, encogí el clúster         #${NC}"
echo -e "${YELLOW}##########################################################${NC}"

# Paso 0: Higiene del entorno (Prevención de conflictos)
echo -e "\n${YELLOW}== Paso 0: Preparando higiene del entorno local (.kube) ==${NC}"
if [ -d "$LOCAL_KUBE_DIR" ]; then
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_PATH="${LOCAL_KUBE_DIR}_backup_$TIMESTAMP"
    mv "$LOCAL_KUBE_DIR" "$BACKUP_PATH"
    echo -e "${GREEN}[OK] Directorio .kube actual respaldado en: $BACKUP_PATH${NC}"
fi
mkdir -p "$LOCAL_KUBE_DIR"

# 1. Selección de Llave SSH ((Filtro v2.9.1))
echo -e "\n${YELLOW}🔍 Buscando identidades SSH disponibles...${NC}"

MAPFILE_KEYS=()
while IFS= read -r line; do
    if [[ -f "$line" ]]; then
        MAPFILE_KEYS+=("$line")
    fi
# Exclusión total de extensiones de datos y documentos
done < <(ls -d * ~/.ssh/* 2>/dev/null | grep -vE "\.pub$|\.sh$|\.yml$|\.yaml$|\.md$|\.png$|\.qcow2$|pull-secret|inventory|ansible\.cfg|authorized_keys|known_hosts|config|bkp")

MAPFILE_KEYS+=("SALIR DEL SCRIPT")

echo "Selecciona la llave SSH para la conexión:"
select SELECTED_KEY in "${MAPFILE_KEYS[@]}"; do
    if [[ "$SELECTED_KEY" == "SALIR DEL SCRIPT" ]]; then
        echo -e "${YELLOW}Abortando. ¡Hasta luego!${NC}"; exit 0
    elif [ -n "$SELECTED_KEY" ]; then
        SSH_KEY="$SELECTED_KEY"
        break
    else
        echo -e "${RED}Opción no válida.${NC}"
    fi
done

# 2. Configuración de Usuario según Entorno
echo -e "\n${YELLOW}Selecciona el entorno/usuario:${NC}"
select USER_CHOICE in "Local (edge-user)" "AWS (ec2-user)" "SALIR"; do
    case $REPLY in
        1) SSH_USER="edge-user"; ENV_LABEL="LOCAL"; break ;;
        2) SSH_USER="ec2-user"; ENV_LABEL="AWS"; break ;;
        3) exit 0 ;;
        *) echo "${RED}❌ Opción no válida." ;;
    esac
done

# 3. Solicitud de IP
read -p "Introduce la IP del nodo: " INSTANCE_IP
[[ -z "$INSTANCE_IP" ]] && { echo -e "${RED}[ERROR] IP requerida.${NC}"; exit 1; }

# Función centralizada para SSH
remote_cmd() {
    ssh -i "$SSH_KEY" -o ConnectTimeout=5 -o StrictHostKeyChecking=accept-new "$SSH_USER@$INSTANCE_IP" "$1" 2>/dev/null
}

echo -e "\n${GREEN}== Paso 1: Validando salud del nodo ($ENV_LABEL) ==${NC}"

# Validación de Conectividad y OS
OS_VER=$(remote_cmd "grep VERSION_ID /etc/os-release | cut -d'\"' -f2")
if [[ $? -ne 0 ]]; then
    echo -e "${RED}[ERROR] No hay conexión SSH con $INSTANCE_IP usando la llave $SSH_KEY${NC}"; exit 1
fi
echo -e "[OK] Conectividad establecida (RHEL $OS_VER)"

# Validación del servicio
SERVICE_STATUS=$(remote_cmd "systemctl is-active microshift")
[[ "$SERVICE_STATUS" == "active" ]] && echo -e "[OK] MicroShift está ACTIVO" || echo -e "${RED}[FAIL] Servicio inactivo${NC}"

# 3. Configuración mTLS Local
echo -e "\n${YELLOW}== Paso 2: Sincronizando acceso mTLS local ==${NC}"
LOCAL_KUBE_DIR="$HOME/.kube"
LOCAL_KUBE_CONFIG="$LOCAL_KUBE_DIR/config-microshift-${ENV_LABEL,,}"

mkdir -p "$LOCAL_KUBE_DIR"

# Descarga y Parcheo
scp -i "$SSH_KEY" "$SSH_USER@$INSTANCE_IP:~/.kube/config" "$LOCAL_KUBE_CONFIG" 2>/dev/null
REMOTE_CA=$(remote_cmd "sudo cat /var/lib/microshift/certs/kube-apiserver-external-signer/ca.crt | base64 -w 0")

# ... [Paso 0, 1 y 2 se mantienen iguales de la v2.8] ...

if [[ -n "$REMOTE_CA" ]]; then
    # REFUERZO: Buscamos específicamente la línea del servidor para evitar el error de localhost
    sed -i "s|server: https://.*:6443|server: https://$INSTANCE_IP:6443|g" "$LOCAL_KUBE_CONFIG"
    sed -i "s|certificate-authority-data:.*|certificate-authority-data: $REMOTE_CA|g" "$LOCAL_KUBE_CONFIG"

    echo -e "${GREEN}[OK] Acceso mTLS configurado para $ENV_LABEL.${NC}"
    # ... [Lógica de parcheo mTLS] ...

    echo -e "\n${YELLOW}##########################################################${NC}"
    echo -e "${YELLOW}#   PREPARACIÓN PARA EL ACTO 3: DESPLIEGUE DE APP        #${NC}"
    echo -e "${YELLOW}##########################################################${NC}"
    echo -e "1. Exporta las variables de entorno:"
    echo -e "${GREEN}   export KUBECONFIG=$LOCAL_KUBE_CONFIG${NC}"
    echo -e "${GREEN}   export NODE_IP=$INSTANCE_IP${NC}"
    echo -e "\n2. Valida la conexión:"
    echo -e "   oc get nodes"
    echo -e "\n3. Despliega tu aplicación (Zero-Touch):"
    # Instrucción 100% genérica para los talleres
    echo -e "   ${CYAN}envsubst < TU_ARCHIVO.yaml | oc apply -f -${NC}"
    echo -e "${YELLOW}##########################################################${NC}"
else
    echo -e "${RED}[ERROR] No se pudo obtener la cadena de confianza TLS.${NC}"
fi

echo -e "\n${GREEN}== Verificación finalizada con éxito ==${NC}"
