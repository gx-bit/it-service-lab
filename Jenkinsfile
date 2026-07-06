pipeline {
    agent any

    stages {
        stage('拉取代码') {
            steps {
                echo '正在从 Git 拉取最新代码...'
                checkout scm
            }
        }
        stage('安装依赖') {
            steps {
                echo '正在安装 Python 依赖...'
                // 注意使用 py -m 来确保 Jenkins 调用正确的 Python 启动器
                bat 'py -m pip install numpy requests openai'
            }
        }
        stage('运行评测 (冒烟测试)') {
            steps {
                echo '正在执行 evaluate.py 进行自动化测试...'
                bat 'py evaluate.py'
            }
        }
        stage('自动化部署') {
            steps {
                echo '正在执行一键启动脚本重启全套服务...'
                // 使用 PowerShell 调用你之前写的重启脚本
                bat 'powershell -ExecutionPolicy Bypass -File restart.ps1'
            }
        }
    }
    
    post {
        always {
            echo '构建结束。'
        }
        success {
            echo '恭喜！流水线运行成功！'
        }
        failure {
            echo '构建失败，请检查日志排查错误。'
        }
    }
}