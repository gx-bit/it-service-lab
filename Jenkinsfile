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
                echo '正在使用 Python 3.10 安装依赖...'
                bat 'C:\\Users\\Lenovo\\AppData\\Local\\Programs\\Python\\Python310-32\\python.exe -m pip install numpy requests openai'
            }
        }
        stage('运行评测 (冒烟测试)') {
            steps {
                echo '正在执行 evaluate.py 进行自动化测试...'
                bat 'C:\\Users\\Lenovo\\AppData\\Local\\Programs\\Python\\Python310-32\\python.exe evaluate.py'
            }
        }
        stage('自动化部署') {
            steps {
                echo '正在执行一键启动脚本重启全套服务...'
                bat 'powershell -ExecutionPolicy Bypass -File restart.ps1'
            }
        }
        // 【新增】：添加 SLA 服务质量与监控指标生成阶段
        stage('生成SLA质量报告') {
            steps {
                echo '正在生成服务可用性与效率指标报告...'
                bat 'C:\\Users\\Lenovo\\AppData\\Local\\Programs\\Python\\Python310-32\\python.exe health_check.py'
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