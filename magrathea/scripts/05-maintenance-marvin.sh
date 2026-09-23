#!/bin/bash
###############################################################################
# Autor: Alex Callejas (@rootzilopochtli)
# Proyecto: PositronicOps
# Descripción: Marvin - Script de mantenimiento y recolección de basura
# Motto: "Here I am, brain the size of a planet, and they ask me to clean the disk..."
###############################################################################

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Validación de seguridad: Asegura que la variable heredada exista
if [ -z "$NODE_IP" ]; then
    echo -e "${RED}Error: La variable \$NODE_IP no está definida.${NC}"
    echo -e "Ejecuta 'export NODE_IP=tu_ip' antes de invocar a Marvin."
    exit 1
fi

SSH_KEY="labkey"
USER="positronic-user"

echo -e "${YELLOW}##########################################################${NC}"
echo -e "${YELLOW}#   MARVIN: Iniciando protocolo de recolección de basura #${NC}"
echo -e "${YELLOW}##########################################################${NC}"
echo -e "Conectando al nodo positrónico en $NODE_IP...\n"

ssh -i "$SSH_KEY" "$USER@$NODE_IP" << 'EOF'
    echo -e "1. Purgando artefactos huérfanos de Podman..."
    sudo podman system prune -a -f > /dev/null 2>&1

    echo -e "2. Limpiando imágenes sin uso en CRI-O..."
    sudo crictl rmi --prune > /dev/null 2>&1

    echo -e "3. Vaciando bitácoras antiguas del sistema (Journald)..."
    sudo journalctl --vacuum-size=50M > /dev/null 2>&1

    echo -e "4. Limpiando caché de paquetes dnf..."
    sudo dnf clean all > /dev/null 2>&1

    echo -e "5. Truncando logs masivos de MicroShift (API Server y Pods)..."
    # Elimina logs rotados/comprimidos antiguos
    sudo find /var/log/kube-apiserver/ /var/log/pods/ -type f -name "*.log.*" -delete > /dev/null 2>&1
    sudo find /var/log/kube-apiserver/ /var/log/pods/ -type f -name "*.gz" -delete > /dev/null 2>&1
    # Vacía los logs activos a cero bytes sin romper el descriptor de archivo
    sudo find /var/log/kube-apiserver/ /var/log/pods/ -type f -name "*.log" -exec truncate -s 0 {} + > /dev/null 2>&1

    echo -e "\nEstado actual del almacenamiento (/):"
    df -h /
EOF

echo -e "\n${GREEN}[OK] Marvin ha terminado. El nodo está listo para el estrés.${NC}"

