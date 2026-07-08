#!/bin/bash
###############################################################################
# Autor: Alex Callejas (@rootzilopochtli)
# Proyecto: PositronicOps (Operaciones Hail Mary)
# Descripción: Deckard - Script de Retiro (Tear Down) del entorno
# Motto: "I've seen things you people wouldn't believe..."
###############################################################################

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

VM_NAME="positronic-node"
USER_SYSTEMD_DIR="$HOME/.config/systemd/user"
OLLAMA_SERVICE="container-ollama_brain.service"
KUBE_CONFIG="$HOME/.kube/config-microshift-positronic"

echo -e "${YELLOW}##########################################################${NC}"
echo -e "${YELLOW}#   DECKARD: Iniciando protocolo de retiro (Tear Down)   #${NC}"
echo -e "${YELLOW}##########################################################${NC}"

# 1. Retirar el Nodo Positrónico (KVM)
echo -e "\n${YELLOW}== Fase 1: Retirando infraestructura Edge (KVM) ==${NC}"
if sudo virsh dominfo "$VM_NAME" >/dev/null 2>&1; then
    echo -e "Apagando (destroy) $VM_NAME..."
    sudo virsh destroy "$VM_NAME" >/dev/null 2>&1
    echo -e "Eliminando (undefine) y purgando almacenamiento..."
    # --remove-all-storage elimina el archivo .qcow2 asociado al pool
    sudo virsh undefine "$VM_NAME" --remove-all-storage >/dev/null 2>&1
    echo -e "${GREEN}[OK] Nodo positrónico retirado.${NC}"
else
    echo -e "${GREEN}[OK] El nodo $VM_NAME no existe. Omitiendo.${NC}"
fi

# 2. Retirar a Multivac (Servicios y Contenedor, conservando datos)
echo -e "\n${YELLOW}== Fase 2: Apagando el Cerebro (Multivac) ==${NC}"
if systemctl --user is-active --quiet "$OLLAMA_SERVICE" || systemctl --user is-enabled --quiet "$OLLAMA_SERVICE"; then
    echo -e "Deteniendo y deshabilitando servicio de usuario..."
    systemctl --user disable --now "$OLLAMA_SERVICE" >/dev/null 2>&1

    echo -e "Eliminando manifiesto de systemd..."
    rm -f "$USER_SYSTEMD_DIR/$OLLAMA_SERVICE"
    systemctl --user daemon-reload
    echo -e "${GREEN}[OK] Servicio systemd retirado.${NC}"
else
    echo -e "${GREEN}[OK] Servicio de Multivac no encontrado. Omitiendo.${NC}"
fi

if podman ps -a --format "{{.Names}}" | grep -q "^ollama_brain$"; then
    echo -e "Purgando contenedor huérfano..."
    podman rm -f ollama_brain >/dev/null 2>&1
    echo -e "${GREEN}[OK] Contenedor retirado. (Datos preservados en ollama_data/)${NC}"
fi

# 3. Limpieza de credenciales
echo -e "\n${YELLOW}== Fase 3: Purgando accesos (Kubeconfig) ==${NC}"
if [ -f "$KUBE_CONFIG" ]; then
    rm -f "$KUBE_CONFIG"
    echo -e "${GREEN}[OK] Kubeconfig temporal eliminado.${NC}"
else
    echo -e "${GREEN}[OK] No hay kubeconfig residual.${NC}"
fi

echo -e "\n${GREEN}##########################################################${NC}"
echo -e "${GREEN}#   RETIRO COMPLETADO: El entorno está limpio.           #${NC}"
echo -e "${GREEN}##########################################################${NC}"
