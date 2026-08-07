<#
.SYNOPSIS
    AI辅助减脂饮食管理系统 — 一键启动
.DESCRIPTION
    同时启动 Flask 后端 (9876) 和 Vite 前端 (5173)
    支持彩色日志输出，按 Ctrl+C 优雅关闭所有服务
#>

$ErrorActionPreference = "SilentlyContinue"
$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path

function Write-Title { Write-Host @"

╔══════════════════════════════════════════╗
║   🚀 AI辅助减脂饮食管理系统              ║
║      数据库实验项目                       ║
╚══════════════════════════════════════════╝
"@ -ForegroundColor Cyan }

function Write-Step($num, $msg) {
    Write-Host "`n[$num/4] $msg" -ForegroundColor Yellow
}

function Test-Command($cmd) {
    if (!(Get-Command $cmd -ErrorAction SilentlyContinue)) {
        Write-Host "[❌] 未找到 $cmd，请安装后重试" -ForegroundColor Red
        Read-Host "按回车退出"
        exit 1
    }
    Write-Host "  [✅] $cmd 已就绪" -ForegroundColor Green
}

# ── 环境检查 ──
Write-Title
Write-Host "正在检查环境..." -ForegroundColor Gray
Test-Command "python"
Test-Command "node"

# ── 安装依赖 ──
Write-Step 1 "安装后端依赖"
Push-Location "$RootDir/backend"
pip install -r requirements.txt -q 2>&1 | Out-Null
Write-Host "  [✅] 后端依赖就绪" -ForegroundColor Green
Pop-Location

Write-Step 2 "安装前端依赖"
Push-Location "$RootDir/frontend"
if (!(Test-Path "node_modules")) {
    npm install --silent 2>&1 | Out-Null
}
Write-Host "  [✅] 前端依赖就绪" -ForegroundColor Green
Pop-Location

# ── 杀旧进程 ──
Write-Host "`n清理旧进程..." -ForegroundColor Gray
Get-Process | Where-Object { $_.ProcessName -eq "python" -and $_.CommandLine -match "manage|run" } | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process | Where-Object { $_.ProcessName -eq "node" -and $_.CommandLine -match "vite" } | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep 1

# ── 启动后端 ──
Write-Step 3 "启动后端服务 (http://localhost:9876)"
$BackendJob = Start-Job -Name "Backend" -ScriptBlock {
    param($dir)
    Set-Location $dir
    python run.py
} -ArgumentList "$RootDir/backend"

Start-Sleep 3
if ($BackendJob.State -eq "Failed") {
    Write-Host "  [❌] 后端启动失败: $($BackendJob.ChildJobs[0].Error | Out-String)" -ForegroundColor Red
} else {
    Write-Host "  [✅] 后端服务已启动" -ForegroundColor Green
}

# ── 启动前端 ──
Write-Step 4 "启动前端服务 (http://localhost:5173)"
$FrontendJob = Start-Job -Name "Frontend" -ScriptBlock {
    param($dir)
    Set-Location $dir
    npm run dev
} -ArgumentList "$RootDir/frontend"

Start-Sleep 3
if ($FrontendJob.State -eq "Failed") {
    Write-Host "  [❌] 前端启动失败: $($FrontendJob.ChildJobs[0].Error | Out-String)" -ForegroundColor Red
} else {
    Write-Host "  [✅] 前端服务已启动" -ForegroundColor Green
}

# ── 完成 ──
Write-Host @"

╔══════════════════════════════════════════╗
║   ✅ 全部启动成功！                       ║
║                                          ║
║   后端: http://localhost:9876             ║
║   前端: http://localhost:5173             ║
║                                          ║
║   按 Ctrl+C 停止所有服务                  ║
╚══════════════════════════════════════════╝
"@ -ForegroundColor Cyan

Start-Process "http://localhost:5173"

# ── 等待用户中断，然后清理 ──
try {
    while ($true) {
        if ($BackendJob.State -eq "Failed") {
            Write-Host "[⚠] 后端异常退出" -ForegroundColor Red
            break
        }
        if ($FrontendJob.State -eq "Failed") {
            Write-Host "[⚠] 前端异常退出" -ForegroundColor Red
            break
        }
        Start-Sleep 2
        # 显示实时日志
        Receive-Job $BackendJob -ErrorAction SilentlyContinue | ForEach-Object { Write-Host "  [后端] $_" -ForegroundColor DarkCyan }
        Receive-Job $FrontendJob -ErrorAction SilentlyContinue | ForEach-Object { Write-Host "  [前端] $_" -ForegroundColor DarkMagenta }
    }
} finally {
    Write-Host "`n⏹  正在停止所有服务..." -ForegroundColor Yellow
    Stop-Job $BackendJob -ErrorAction SilentlyContinue
    Stop-Job $FrontendJob -ErrorAction SilentlyContinue
    Remove-Job $BackendJob -ErrorAction SilentlyContinue
    Remove-Job $FrontendJob -ErrorAction SilentlyContinue

    # 再补一刀：确保端口释放
    netstat -ano | findstr ":9876 " | findstr LISTEN | ForEach-Object {
        $pid = ($_ -split '\s+')[-1]
        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
    }
    netstat -ano | findstr ":5173 " | findstr LISTEN | ForEach-Object {
        $pid = ($_ -split '\s+')[-1]
        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
    }

    if (Test-Path "$RootDir/backend/.server.pid") { Remove-Item "$RootDir/backend/.server.pid" -Force }

    Write-Host "[✅] 所有服务已停止" -ForegroundColor Green
    Read-Host "按回车退出"
}
