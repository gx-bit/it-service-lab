# 一键启动 IT 服务台全部微服务和 Web 服务
Write-Host "正在启动 3 个业务微服务 (8001/8002/8003)..." -ForegroundColor Green
Start-Process py -ArgumentList "services/ticket_service.py"
Start-Process py -ArgumentList "services/device_service.py"
Start-Process py -ArgumentList "services/network_service.py"
Start-Sleep -Seconds 2  # 等待微服务启动初始化

Write-Host "正在启动 Web 服务器 (8000) ..." -ForegroundColor Green
py server.py