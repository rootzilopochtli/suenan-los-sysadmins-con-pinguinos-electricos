#!/bin/bash
###############################################################################
# Autor: Alex Callejas (@rootzilopochtli)
# Proyecto: PositronicOps
# Versión 2.0: CentOS Stream 10 / Airgap-Safe
# Descripción: Marvin - Script de mantenimiento y recolección de basura
###############################################################################

# 1. Resolver IP y llave SSH respetando variables heredadas de Agatha/.env
NODE_IP="${NODE_IP:-192.168.122.32}"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
SSH_KEY_PATH="${SSH_KEY_PATH:-${SCRIPT_DIR}/../labkey}"

echo "##########################################################"
echo "#   MARVIN: Iniciando protocolo de recolección de basura #"
echo "##########################################################"
echo "Conectando al nodo positrónico en ${NODE_IP}..."

# 2. Ejecutar limpieza no interactiva vía SSH (falla rápido si hay error de red/llave)
ssh -i "${SSH_KEY_PATH}" \
    -o BatchMode=yes \
    -o ConnectTimeout=5 \
    -o StrictHostKeyChecking=no \
    -o GSSAPIAuthentication=no \
    "positronic-user@${NODE_IP}" << 'EOF'
  echo ""
  echo "1. Purgando artefactos huérfanos de Podman (conservando imágenes etiquetadas)..."
  sudo podman system prune -f

  echo "2. Vaciando bitácoras del sistema (Journald máx. 50M)..."
  sudo journalctl --vacuum-size=50M

  echo "3. Limpiando caché de paquetes dnf..."
  sudo dnf clean all

  echo "4. Limpiando y truncando logs masivos de MicroShift (API Server y Pods)..."
  for dir in /var/log/kube-apiserver /var/log/pods; do
    if [ -d "$dir" ]; then
      sudo find "$dir" -type f \( -name "*.log.*" -o -name "*.gz" \) -delete 2>/dev/null
      sudo find "$dir" -type f -name "*.log" -exec truncate -s 0 {} + 2>/dev/null
    fi
  done

  echo ""
  echo "Estado actual del almacenamiento (/):"
  df -h /
EOF

SSH_RC=$?
if [ $SSH_RC -ne 0 ]; then
  echo ""
  echo "[ERROR] Marvin no pudo completar el mantenimiento en ${NODE_IP} (SSH exit: ${SSH_RC})." >&2
  exit $SSH_RC
fi

echo ""
echo "[OK] Marvin ha terminado. El nodo está listo para el estrés."
