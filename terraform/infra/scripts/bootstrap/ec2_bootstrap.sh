#!/bin/bash
set -e

# Atualiza pacotes
apt-get update -y
apt-get upgrade -y

# Instala dependências
apt-get install -y ca-certificates curl gnupg lsb-release

# Adiciona a chave GPG do Docker
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

# Adiciona o repositório Docker
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | \
  tee /etc/apt/sources.list.d/docker.list > /dev/null

# Instala Docker Engine
apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io

# Habilita e inicia Docker
systemctl enable docker
systemctl start docker

# Adiciona o usuário 'ubuntu' ao grupo docker
usermod -aG docker ubuntu

# Instala Docker Compose CLI (v2)
curl -SL https://github.com/docker/compose/releases/download/v2.24.6/docker-compose-linux-x86_64 \
    -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose