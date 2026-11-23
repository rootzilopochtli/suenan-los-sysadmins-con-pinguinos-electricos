#!/bin/bash
###############################################################################
# Autor: Alex Callejas (@rootzilopochtli)
# Proyecto: PositronicOps (Operaciones Hail Mary)
# Version 2.0: CentOS release
# Descripción: Validador de salud y extractor mTLS para MicroShift (Local KVM)
###############################################################################

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Definición de rutas globales
LOCAL_KUBE_DIR="$HOME/.kube"
SSH_USER="positronic-user"

echo -e "${YELLOW}##########################################################${NC}"
echo -e "${YELLOW}#   Mando de Control: PositronicOps (Operaciones Hail Mary) #${NC}"
echo -e "${YELLOW}##########################################################${NC}"

# Paso 0: Higiene del entorno (No Destructivo)
echo -e "\n${YELLOW}== Paso 0: Preparando entorno local (.kube) ==${NC}"
mkdir -p "$LOCAL_KUBE_DIR"
echo -e "${GREEN}[OK] Directorio .kube verificado.${NC}"

# 1. Selección de Perfil (Multiclúster)
echo -e "\n${YELLOW}Selecciona el perfil del clúster a conectar:${NC}"
select PROFILE_CHOICE in "RHEL 9 (positronic)" "CentOS 10 (centos10)" "SALIR"; do
    case $REPLY in
        1) ENV_LABEL="positronic"; break ;;
        2) ENV_LABEL="centos10"; break ;;
        3) exit 0 ;;
        *) echo -e "${RED}❌ Opción no válida.${NC}" ;;
    esac
done

# 2. Selección de Llave SSH
echo -e "\n${YELLOW}🔍 Buscando identidades SSH disponibles...${NC}"

MAPFILE_KEYS=()
while IFS= read -r line; do
    if [[ -f "$line" ]]; then
        MAPFILE_KEYS+=("$line")
    fi
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

# 3. Solicitud de IP
echo -e "\n${YELLOW}Configuración de Entorno: $ENV_LABEL ($SSH_USER)${NC}"
read -p "Introduce la IP del nodo positrónico: " INSTANCE_IP
[[ -z "$INSTANCE_IP" ]] && { echo -e "${RED}[ERROR] IP requerida.${NC}"; exit 1; }

# Función centralizada para SSH
remote_cmd() {
    ssh -i "$SSH_KEY" -o ConnectTimeout=5 -o StrictHostKeyChecking=accept-new "$SSH_USER@$INSTANCE_IP" "$1" 2>/dev/null
}

echo -e "\n${GREEN}== Paso 1: Validando salud del nodo ==${NC}"

# Validación de Conectividad y OS
OS_VER=$(remote_cmd "grep VERSION_ID /etc/os-release | cut -d'\"' -f2")
if [[ $? -ne 0 ]]; then
    echo -e "${RED}[ERROR] No hay conexión SSH con $INSTANCE_IP usando la llave $SSH_KEY${NC}"; exit 1
fi
echo -e "${GREEN}[OK] Conectividad establecida (OS ID: $OS_VER)${NC}"

# Validación del servicio MicroShift
SERVICE_STATUS=$(remote_cmd "systemctl is-active microshift")
[[ "$SERVICE_STATUS" == "active" ]] && echo -e "${GREEN}[OK] MicroShift está ACTIVO${NC}" || echo -e "${RED}[FAIL] Servicio inactivo${NC}"

# 4. Configuración mTLS Local
echo -e "\n${YELLOW}== Paso 2: Sincronizando acceso mTLS local ==${NC}"
LOCAL_KUBE_CONFIG="$LOCAL_KUBE_DIR/config-microshift-${ENV_LABEL,,}"

# Descarga del kubeconfig base y la entidad certificadora
scp -i "$SSH_KEY" "$SSH_USER@$INSTANCE_IP:~/.kube/config" "$LOCAL_KUBE_CONFIG" 2>/dev/null
REMOTE_CA=$(remote_cmd "sudo cat /var/lib/microshift/certs/kube-apiserver-external-signer/ca.crt | base64 -w 0")

if [[ -n "$REMOTE_CA" ]]; then
    # Parcheo del kubeconfig para acceso externo seguro
    sed -i "s|server: https://.*:6443|server: https://$INSTANCE_IP:6443|g" "$LOCAL_KUBE_CONFIG"
    sed -i "s|certificate-authority-data:.*|certificate-authority-data: $REMOTE_CA|g" "$LOCAL_KUBE_CONFIG"

    echo -e "${GREEN}[OK] Acceso mTLS configurado para $ENV_LABEL.${NC}"
    echo -e "Archivo generado: ${CYAN}$LOCAL_KUBE_CONFIG${NC}"

    echo -e "\n${YELLOW}##########################################################${NC}"
    echo -e "${YELLOW}#   PREPARACIÓN PARA EL DESPLIEGUE DE LA CARGA BASE      #${NC}"
    echo -e "${YELLOW}##########################################################${NC}"
    echo -e "1. Exporta las variables de entorno:"
    echo -e "${CYAN}   export KUBECONFIG=$LOCAL_KUBE_CONFIG${NC}"
    echo -e "${CYAN}   export NODE_IP=$INSTANCE_IP${NC}"
    echo -e "\n2. Valida la conexión con el clúster:"
    echo -e "   oc get nodes"
    echo -e "${YELLOW}##########################################################${NC}"
else
    echo -e "${RED}[ERROR] No se pudo obtener la cadena de confianza TLS.${NC}"
fi

echo -e "\n${GREEN}== Verificación finalizada con éxito ==${NC}"
