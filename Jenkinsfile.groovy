pipeline {

    agent { 
        label 'docker' 
    }

    stages {

        stage('Unit Tests') {
            steps {
                sh 'make test-unit'
            }
        }

        stage('API Tests') {
            steps {
                sh 'make test-api'
            }
        }

        stage('E2E Tests') {
            steps {
                sh 'make test-e2e'
            }
        }

        stage('Build Docker Images') {
            steps {
                sh 'make build'
            }
        }

        stage('Push Docker Images') {
            steps {
                sh 'make push'
            }
        }

        stage('Autenticacion en AWS Academy') {
            steps {
                sh 'make aws-login'
            }
        }

        stage('Aplicar manifiestos Kubernetes') {
            steps {
                sh 'make deploy'
            }
        }    

        stage('Obtener url pública aplicación') {
            steps {
                sh 'make deploy'
            }
        }       

    }

    post {
        failure {

            echo "Job: ${JOB_NAME}"
            echo "Ejecución: #${BUILD_NUMBER}"
            echo "URL: ${BUILD_URL}"           
    //         mail to: 'correo@ejemplo.com',
    //             subject: "Fallo en el job ${JOB_NAME} #${BUILD_NUMBER}",
    //             body: """El pipeline ha fallado.

    //         Job: ${JOB_NAME}
    //         Ejecución: #${BUILD_NUMBER}
    //         URL: ${BUILD_URL}

    //         Revise los logs para más detalles.

    //         Notificación automática desdeJenkins
    //         """
        }
    }
}

