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
                // 关键修改：强制指定 Python 3.10 的绝对路径 (注意更新为你电脑的真实路径)
                bat 'C:\\Users\\Lenovo\\AppData\\Local\\Programs\\Python\\Python310-32\\python.exe -m pip install numpy requests openai'
            }
        }
        stage('运行评测 (冒烟测试)') {
            steps {
                echo '正在执行 evaluate.py 进行自动化测试...'
                // 同样使用绝对路径启动 python
                bat 'C:\\Users\\Lenovo\\AppData\\Local\\Programs\\Python\\Python310-32\\python.exe evaluate.py'
            }
        }
        stage('自动化部署') {
            steps {
                echo '正在执行一键启动脚本重启全套服务...'
                // 这里继续用 PowerShell 调用脚本，但你要确保 restart.ps1 里的命令也是绝对路径
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