param()

$ErrorActionPreference = "Stop"

function Write-Section($Title) {
    Write-Host ""
    Write-Host "== $Title =="
}

function Get-VersionOrMissing($Command, $Args = @("--version")) {
    $cmd = Get-Command $Command -ErrorAction SilentlyContinue
    if (-not $cmd) {
        return $null
    }

    try {
        return (& $cmd.Source @Args | Select-Object -First 1).ToString().Trim()
    }
    catch {
        return "<installed, version probe failed>"
    }
}

function Get-CmdVersionOrMissing($CommandLine) {
    $commandName = $CommandLine.Split(" ")[0]
    $cmd = Get-Command $commandName -ErrorAction SilentlyContinue
    if (-not $cmd) {
        return $null
    }

    try {
        return ((cmd.exe /d /c $CommandLine) | Select-Object -First 1).ToString().Trim()
    }
    catch {
        return "<installed, version probe failed>"
    }
}

function Test-WebView2Runtime {
    $paths = @(
        "HKLM:\SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}",
        "HKLM:\SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}",
        "HKCU:\SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"
    )

    foreach ($path in $paths) {
        if (Test-Path $path) {
            try {
                $item = Get-ItemProperty -Path $path
                return $item.pv
            }
            catch {
                return "<installed, version probe failed>"
            }
        }
    }

    return $null
}

function Test-MSVCBuildTools {
    $cl = Get-Command cl.exe -ErrorAction SilentlyContinue
    if ($cl) {
        return "cl.exe found in PATH"
    }

    $vswhereCandidates = @(
        "$env:ProgramFiles(x86)\Microsoft Visual Studio\Installer\vswhere.exe",
        "$env:ProgramFiles\Microsoft Visual Studio\Installer\vswhere.exe"
    )

    foreach ($candidate in $vswhereCandidates) {
        if (Test-Path $candidate) {
            $result = & $candidate -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationName 2>$null
            if ($LASTEXITCODE -eq 0 -and $result) {
                return $result.Trim()
            }
        }
    }

    return $null
}

$nodeVersion = Get-CmdVersionOrMissing "node -v"
$npmVersion = Get-CmdVersionOrMissing "npm -v"
$rustcVersion = Get-CmdVersionOrMissing "rustc -V"
$cargoVersion = Get-CmdVersionOrMissing "cargo -V"
$rustupVersion = Get-CmdVersionOrMissing "rustup -V"
$msvcStatus = Test-MSVCBuildTools
$webView2Version = Test-WebView2Runtime

Write-Section "Runtime"
Write-Host ("node  : {0}" -f $(if ($nodeVersion) { $nodeVersion } else { "missing" }))
Write-Host ("npm   : {0}" -f $(if ($npmVersion) { $npmVersion } else { "missing" }))

Write-Section "Rust"
Write-Host ("rustup: {0}" -f $(if ($rustupVersion) { $rustupVersion } else { "missing" }))
Write-Host ("rustc : {0}" -f $(if ($rustcVersion) { $rustcVersion } else { "missing" }))
Write-Host ("cargo : {0}" -f $(if ($cargoVersion) { $cargoVersion } else { "missing" }))

Write-Section "Windows Tooling"
Write-Host ("MSVC Build Tools: {0}" -f $(if ($msvcStatus) { $msvcStatus } else { "missing" }))
Write-Host ("WebView2 Runtime: {0}" -f $(if ($webView2Version) { $webView2Version } else { "missing" }))

Write-Section "Recommended Commands"
if (-not $rustupVersion) {
    Write-Host "winget install --id Rustlang.Rustup -e --accept-package-agreements --accept-source-agreements"
}
if (-not $msvcStatus) {
    Write-Host "winget install --id Microsoft.VisualStudio.2022.BuildTools -e --accept-package-agreements --accept-source-agreements"
    Write-Host "Then install the 'Desktop development with C++' workload and Windows SDK in the Visual Studio installer."
}
if (-not $webView2Version) {
    Write-Host "winget install --id Microsoft.EdgeWebView2Runtime -e --accept-package-agreements --accept-source-agreements"
}

Write-Section "Tauri Readiness"
if ($nodeVersion -and $npmVersion -and $rustupVersion -and $rustcVersion -and $cargoVersion -and $msvcStatus -and $webView2Version) {
    Write-Host "Environment looks ready for a Windows Tauri app."
}
else {
    Write-Host "Environment is not ready yet. Install the missing dependencies above first."
}
