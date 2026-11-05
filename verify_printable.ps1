$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $MyInvocation.MyCommand.Path
$slicerPath='C:\Program Files\SuperSlicer_2.7.62.0_win64_251119\superslicer_console.exe'
$checkRoot=Join-Path $projectRoot 'output\printable\slice_checks'
New-Item -ItemType Directory -Force -Path $checkRoot | Out-Null
$summary=@()
foreach ($section in @('tray','cover','adapter_front','adapter_back')) {
    $logPath=Join-Path $checkRoot ($section+'_final.log')
    $gcodePath=Join-Path $checkRoot ($section+'_verification.gcode')
    $sliceArgs=@('--datadir',(Join-Path $checkRoot ('settings_'+$section)),
        '--threads','2','--export-gcode','--nozzle-diameter','0.4',
        '--layer-height','0.2','--first-layer-height','0.2',
        '--perimeters','4','--perimeter-generator','arachne','--fill-density','20%',
        '--filament-diameter','1.75','--skirts','0',
        '--temperature','0','--first-layer-temperature','0',
        '--bed-temperature','0','--first-layer-bed-temperature','0',
        '--start-gcode','; Geometry verification only - not printer ready',
        '--end-gcode','; Geometry verification only - not printer ready')
    if ($section -eq 'tray') { $sliceArgs+='--no-support-material' }
    else { $sliceArgs+=@('--support-material','--support-material-auto','--support-material-buildplate-only') }
    $sliceArgs+=@('--output',$gcodePath,(Join-Path $projectRoot ('output\printable\'+$section+'_print.stl')))
    & $slicerPath @sliceArgs *> $logPath
    if ($LASTEXITCODE -ne 0) { throw "Slice failed for $section. See $logPath" }
    $warnings=@(Get-Content -LiteralPath $logPath | Select-String -Pattern 'print warning:|error:')
    $summary+=@{part=$section;exit_code=$LASTEXITCODE;warnings=$warnings.Count;supports=($section -ne 'tray');engine='arachne';layer_height_mm=0.2;nozzle_mm=0.4}
    if ($warnings.Count -gt 0) { throw "Slicer warning for $section. See $logPath" }
}
$summary | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $checkRoot 'slice_validation.json')
$summary | Format-Table -AutoSize
