pipeline {

    agent { 
        label 'node' 
    }

    stages {

        stage('Unit Tests') {
            steps {
                sh 'make test-unit'
                archiveArtifacts artifacts: "results/*.xml"
            }
        }

        stage('API Tests') {
            steps {
                sh 'make test-api'
                archiveArtifacts artifacts: "results/*.xml"
            }
        }

        stage('GENERADOR Tests') {
            steps {
                sh 'make test-generador'
                archiveArtifacts artifacts: "results/*.xml"
            }
        }

        // stage('E2E Tests') {
        //     steps {
        //         sh 'make test-e2e'
        //         archiveArtifacts artifacts: "results/*.xml"
        //     }
        // }

        // stage('Debug workspace') {
        //     steps {
        //         sh "ls -R ${WORKSPACE}"
        //     }
        // }

        // stage('Convertir XML a HTML') {
        //     steps {
        //         sh '''
        //             apk add --no-cache libxslt
        //             mkdir -p results/e2e
        //             xsltproc test/e2e/junit-to-html.xsl results/cypress_result.xml > results/e2e/index.html
        //         '''
        //     }
        // }

        stage('Publicar Reportes') {
            steps {

                junit 'results/*_result.xml' 

                publishHTML(target: [
                    reportDir: 'results/unit',
                    reportFiles: 'index.html',
                    reportName: 'Unit Tests Report'
                ])

                publishHTML(target: [
                    reportDir: 'results/api',
                    reportFiles: 'index.html',
                    reportName: 'API Tests Report'
                ])

                publishHTML(target: [
                    reportDir: 'results/generador',
                    reportFiles: 'index.html',
                    reportName: 'Generador Tests Report'
                ])                

                publishHTML(target: [
                    reportDir: 'results/coverage',
                    reportFiles: 'index.html',
                    reportName: 'Cobertura de Código'
                ])

                // publishHTML(target: [
                //     reportDir: 'results/e2e',
                //     reportFiles: 'index.html',
                //     reportName: 'Reporte E2E'
                // ])
            }
        }

        stage('Build Docker Images') {
            steps {
                sh 'make build'
            }
        }

        stage('Push Docker Images') {
            environment {
                DOCKERHUB = credentials('dockerhub-credentials')
            }            
            steps {
                sh 'make push'
            }
        }

        stage('Autenticacion en AWS Academy') {
            steps {
                withCredentials([file(credentialsId: 'aws-credentials-file', variable: 'AWS_CREDS')]) {
                sh '''
                    echo " "
                    echo "▶ Configurando credenciales AWS Academy..."

                    mkdir -p ~/.aws
                    cp $AWS_CREDS ~/.aws/credentials
                '''
        }
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
                sh 'make urls'
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

