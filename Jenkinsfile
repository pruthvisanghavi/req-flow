pipeline {
    agent any

    environment {
        OLLAMA_URL   = "http://ollama:11434/api/chat"
        OLLAMA_MODEL = "qwen3:8b"
        CI           = "true"   // skips human approval gate
    }

    stages {

        stage('Generate Tests') {
            steps {
                echo 'Running req-flow pipeline (CI mode — auto-approve)...'
                sh '''
                    docker compose run --rm \
                        -e CI=true \
                        pipeline python generate_test.py
                '''
            }
        }

        stage('Run Tests') {
            steps {
                echo 'Running generated pytest suite...'
                sh '''
                    docker compose run --rm \
                        -e CI=true \
                        pipeline python -m pytest tests/ -v \
                            --cov=src \
                            --cov-report=xml:reports/coverage.xml \
                            --cov-report=html:reports/coverage \
                            --junitxml=reports/results.xml
                '''
            }
        }

        stage('Publish Reports') {
            steps {
                junit 'reports/results.xml'
                publishHTML(target: [
                    allowMissing:          false,
                    alwaysLinkToLastBuild: true,
                    keepAll:               true,
                    reportDir:             'reports/coverage',
                    reportFiles:           'index.html',
                    reportName:            'Coverage Report'
                ])
            }
        }
    }

    post {
        success {
            echo '✅ All tests passed.'
        }
        failure {
            echo '❌ Tests failed — check the reports above.'
        }
        always {
            archiveArtifacts artifacts: 'reports/**', allowEmptyArchive: true
        }
    }
}