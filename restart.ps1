# 指定 Python 3.10 的绝对路径（避免 Jenkins 环境变量冲突）
$PYTHON_CMD = "C:\Users\Lenovo\AppData\Local\Programs\Python\Python310-32\python.exe"

Write-Host "正在启动 3 个业务微服务 (8001/8002/8003)..." -ForegroundColor Green
Start-Process $PYTHON_CMD -ArgumentList "services/ticket_service.py"
Start-Process $PYTHON_CMD -ArgumentList "services/device_service.py"
Start-Process $PYTHON_CMD -ArgumentList "services/network_service.py"
Start-Sleep -Seconds 2

Write-Host "正在启动 Web 服务器 (8000) ..." -ForegroundColor Green
Start-Process $PYTHON_CMD -ArgumentList "server.py"