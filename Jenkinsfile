node {
    def app

    stage('Clone repository') {
        checkout scm
    }

    stage('Build image') {
        app = docker.build("cityenergyanalyst/cea")
    }

    stage('Push image') {
        docker.withRegistry('https://registry.hub.docker.com', 'c19c1459-d091-49c4-9e7b-1a6ae70f50d0') {
            // app.push("${env.BUILD_NUMBER}")
            app.push("latest")
        }
    }
}