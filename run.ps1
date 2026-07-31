# LlamaForge one-click runner.
# Reads config.json, starts the llama.cpp router + the LlamaForge backend,
# then opens the dashboard in your browser. Safe to run repeatedly.
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$cfg  = Get-Content (Join-Path $here "config.json") -Raw | ConvertFrom-Json

function Listening($port){ [bool](Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue) }

$logDir = Join-Path $here "logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

# 1. llama.cpp / ik_llama router (only if not already up)
if (-not (Listening $cfg.router_port)) {
  # Choose binary based on active_engine setting
  $engine = if ($cfg.active_engine) { $cfg.active_engine } else { "llamacpp" }
  if ($engine -eq "ikllama") {
    $serverBin = $cfg.ik_llama_server_bin
    $engineLabel = "ik_llama"
    # Mirror config.ini_path(): derive a sibling of models_ini, splitting on the
    # extension. .Replace(".ini", ...) is a global replace and would also rewrite
    # any parent directory whose name contains ".ini".
    $modelsIni = if ($cfg.ik_llama_models_ini) { $cfg.ik_llama_models_ini } else {
      Join-Path ([IO.Path]::GetDirectoryName($cfg.models_ini)) `
                ([IO.Path]::GetFileNameWithoutExtension($cfg.models_ini) + "-ikllama" +
                 [IO.Path]::GetExtension($cfg.models_ini))
    }
  } else {
    $serverBin = $cfg.server_bin
    $engineLabel = "llama.cpp"
    $modelsIni = $cfg.models_ini
  }
  if (Test-Path $serverBin) {
    $routerHost = if ($cfg.router_host) { $cfg.router_host } else { "127.0.0.1" }
    $args = @("--models-preset", $modelsIni, "--models-max", "1", "--offline",
              "--host", $routerHost, "--port", "$($cfg.router_port)", "--metrics")
    if ($cfg.router_api_key) { $args += @("--api-key", $cfg.router_api_key) }
    Start-Process -FilePath $serverBin -ArgumentList $args -WindowStyle Hidden `
                  -RedirectStandardOutput (Join-Path $logDir "router.out.log") `
                  -RedirectStandardError  (Join-Path $logDir "router.err.log")
    Write-Host "started $engineLabel router on $($routerHost):$($cfg.router_port)"
  } else {
    Write-Host "server_bin not found ($serverBin) - open the dashboard Build tab to build $engineLabel first." -ForegroundColor Yellow
  }
}

# 2. LlamaForge backend (dashboard)
if (-not (Listening $cfg.panel_port)) {
  Start-Process -FilePath "python" -ArgumentList (Join-Path $here "backend\server.py") `
                -WorkingDirectory (Join-Path $here "backend") -WindowStyle Hidden
  Write-Host "started LlamaForge dashboard on port $($cfg.panel_port)"
}

# 3. open the dashboard
Start-Sleep -Seconds 2
Start-Process "http://127.0.0.1:$($cfg.panel_port)/"
