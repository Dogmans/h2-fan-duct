param([switch]$FailOnWarnings)
$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $MyInvocation.MyCommand.Path
$slicerPath='C:\Program Files\SuperSlicer_2.7.62.0_win64_251119\superslicer_console.exe'
$checkRoot=Join-Path $projectRoot 'output\support_free\slice_checks'
New-Item -ItemType Directory -Force -Path $checkRoot | Out-Null
$summary=@()
foreach ($section in @('tray','cover','adapter_front','adapter_back')) {
    $logPath=Join-Path $checkRoot ($section+'.log')
    $gcodePath=Join-Path $checkRoot ($section+'_verification.gcode')
    $sliceArgs=@('--datadir',(Join-Path $checkRoot ('settings_'+$section)),
        '--threads','2','--export-gcode','--nozzle-diameter','0.4',
        '--layer-height','0.2','--first-layer-height','0.2',
        '--perimeters','4','--perimeter-generator','arachne','--fill-density','20%',
        '--no-perimeter-unsupported-algo','bridges','--brim-width','3',
        '--filament-diameter','1.75','--skirts','0',
        '--temperature','0','--first-layer-temperature','0',
        '--bed-temperature','0','--first-layer-bed-temperature','0',
        '--start-gcode','; Geometry verification only - not printer ready',
        '--end-gcode','; Geometry verification only - not printer ready',
        '--no-support-material','--output',$gcodePath,
        (Join-Path $projectRoot ('output\support_free\'+$section+'_print.stl')))
    & $slicerPath @sliceArgs *> $logPath
    if ($LASTEXITCODE -ne 0) { throw "Slice failed for $section. See $logPath" }
    $warnings=@(Get-Content -LiteralPath $logPath | Select-String -Pattern 'print warning:|error:')
    $summary+=@{part=$section;exit_code=$LASTEXITCODE;warnings=$warnings.Count;supports=$false;engine='arachne';layer_height_mm=0.2;nozzle_mm=0.4}
    if ($warnings.Count -gt 0) { Get-Content -LiteralPath $logPath | Select-String -Pattern 'warning|Collapsing|Loose|Consider|bridge' -Context 0,3 }
}
$summary | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $checkRoot 'slice_validation.json')
$summary | ForEach-Object { [pscustomobject]$_ } | Format-Table -AutoSize
$cadChecks=Get-Content -Raw -LiteralPath (Join-Path $projectRoot 'output\support_free\export_checks.json') | ConvertFrom-Json
foreach ($entry in $cadChecks.PSObject.Properties) {
    if ($entry.Value.steep_nonbridge_area_mm2 -gt 0.0001) { throw 'Steep unsupported CAD face remains.' }
}
if (@($summary | Where-Object warnings -gt 0).Count -gt 0) {
    if ($FailOnWarnings) { throw 'No-support slicing retains stability/bridge alerts. Inspect logs.' }
    Write-Warning 'Slicing completed with supports disabled. Stability/bridge alerts are retained in the logs; CAD audit finds only deliberate flat bridges beyond 45 degrees.'
}
