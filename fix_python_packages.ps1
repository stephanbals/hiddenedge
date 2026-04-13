$base = "C:\Projects\AIJobHunter"

$folders = @(
    "config",
    "analysis",
    "crawlers"
)

foreach ($folder in $folders) {

    $path = Join-Path $base $folder
    $initFile = Join-Path $path "__init__.py"

    if (!(Test-Path $initFile)) {

        New-Item -Path $initFile -ItemType File | Out-Null
        Write-Host "Created:" $initFile

    } else {

        Write-Host "Already exists:" $initFile

    }

}

Write-Host ""
Write-Host "Python package structure verified."