#!/bin/bash
# jenkins_setup.sh
# Run this once after Jenkins starts to install Docker CLI inside the container.
# Jenkins needs Docker to run `docker compose` commands in the pipeline.

set -e

CONTAINER="req_flow_jenkins"

echo "Installing Docker CLI inside Jenkins container..."
docker exec -u root $CONTAINER bash -c "
    apt-get update -q &&
    apt-get install -y -q docker.io &&
    curl -SL https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-linux-x86_64 \
        -o /usr/local/bin/docker-compose &&
    chmod +x /usr/local/bin/docker-compose &&
    ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
"

echo "Adding jenkins user to docker group..."
docker exec -u root $CONTAINER bash -c "
    groupadd -f docker &&
    usermod -aG docker jenkins
"

echo "Restarting Jenkins container..."
docker restart $CONTAINER

echo ""
echo "✅ Done. Jenkins is available at http://localhost:8080"
echo ""
echo "Next steps:"
echo "  1. Open http://localhost:8080"
echo "  2. Create a Pipeline job"
echo "  3. Set Pipeline Definition to 'Pipeline script from SCM'"
echo "  4. Point it at your repo — Jenkins will find the Jenkinsfile"