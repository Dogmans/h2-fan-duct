param([switch]$FailOnWarnings)
$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $MyInvocation.MyCommand.Path
$slicerPath='C:\Program Files\SuperSlicer_2.7.62.0_win64_251119\superslicer_console.exe'
$artifactRoot=Join-Path $projectRoot 'output\underside_down'
$checkRoot=Join-Path $artifactRoot 'slice_checks'
New-Item -ItemType Directory -Force -Path $checkRoot | Out-Null
$summary=@()
$sections=@('duct','fan_bracket','chain_plate','spacer_2mm','spacer_4mm')
foreach ($section in $sections) {
    $logPath=Join-Path $checkRoot ($section+'.log')
    $gcodePath=Join-Path $checkRoot ($section+'_verification.gcode')
    $supportArgs=@('--no-support-material')
    $fillDensity='20%'
    $fillArgs=@()
    if ($section -ne 'fan_bracket') { $fillDensity='100%'; $fillArgs=@('--fill-pattern','rectilinear') }
    if ($section -eq 'fan_bracket') { $supportArgs=@('--support-material','--support-material-buildplate-only') }
    $sliceArgs=@('--datadir',(Join-Path $checkRoot ('settings_'+$section)),
        '--threads','2','--export-gcode','--nozzle-diameter','0.4',
        '--layer-height','0.2','--first-layer-height','0.2',
        '--perimeters','4','--perimeter-generator','arachne','--fill-density',$fillDensity,
        '--no-perimeter-unsupported-algo','bridges','--brim-width','3',
        '--filament-diameter','1.75','--skirts','0',
        '--temperature','0','--first-layer-temperature','0',
        '--bed-temperature','0','--first-layer-bed-temperature','0',
        '--start-gcode','; Geometry verification only - not printer ready',
        '--end-gcode','; Geometry verification only - not printer ready',
        '--output',$gcodePath) + $supportArgs + $fillArgs + @(
        (Join-Path $artifactRoot ($section+'_print.stl')))
    & $slicerPath @sliceArgs *> $logPath
    if ($LASTEXITCODE -ne 0) { throw "Slice failed for $section. See $logPath" }
    $warnings=@(Get-Content -LiteralPath $logPath | Select-String -Pattern 'print warning:|error:')
    $summary+=@{part=$section;exit_code=$LASTEXITCODE;warnings=$warnings.Count;
        supports=($section -eq 'fan_bracket');fill_density=$fillDensity;engine='arachne';layer_height_mm=0.2;nozzle_mm=0.4}
}
ConvertTo-Json -InputObject @($summary) | Set-Content -LiteralPath (Join-Path $checkRoot 'slice_validation.json')
$summary | ForEach-Object { [pscustomobject]$_ } | Format-Table -AutoSize
$checks=Get-Content -Raw -LiteralPath (Join-Path $artifactRoot 'export_checks.json') | ConvertFrom-Json
if ($checks.duct.steep_nonbridge_area_mm2 -gt 0.0001) { throw 'Unsupported non-flat duct face remains.' }
if (@($summary | Where-Object warnings -gt 0).Count -gt 0) {
    if ($FailOnWarnings) { throw 'Slicer alerts remain; see slice_checks logs.' }
    Write-Warning 'Slicer alerts are retained in slice_checks logs. Inspect bridges before printing.'
}
