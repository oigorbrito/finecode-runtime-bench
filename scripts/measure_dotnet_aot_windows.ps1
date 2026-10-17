param(
  [Parameter(Mandatory=$true)][string]$Binary,
  [Parameter(Mandatory=$true)][string]$Out,
  [int]$Iterations = 25
)
$ErrorActionPreference = 'Stop'
if ($Iterations -lt 3) { throw 'At least 3 iterations required' }
$exe = (Resolve-Path $Binary).Path
$wall = [System.Collections.Generic.List[double]]::new()
$cpu = [System.Collections.Generic.List[double]]::new()
$rss = [System.Collections.Generic.List[double]]::new()
for ($i = 0; $i -lt $Iterations; $i++) {
  $p = [System.Diagnostics.Process]::new()
  $p.StartInfo.FileName = $exe
  $p.StartInfo.Arguments = '--help'
  $p.StartInfo.UseShellExecute = $false
  $p.StartInfo.RedirectStandardOutput = $true
  $p.StartInfo.RedirectStandardError = $true
  $timer = [System.Diagnostics.Stopwatch]::StartNew()
  try {
    if (-not $p.Start()) { throw 'Unable to start process' }
    $output = $p.StandardOutput.ReadToEnd()
    $stderr = $p.StandardError.ReadToEnd()
    $p.WaitForExit()
    $timer.Stop()
    if ($p.ExitCode -ne 0 -or -not $output.Contains('finecode-dotnet-aot-probe')) {
      throw "Unexpected CLI output (exit=$($p.ExitCode)): $stderr"
    }
    $wall.Add($timer.Elapsed.TotalMilliseconds)
    $cpu.Add($p.TotalProcessorTime.TotalMilliseconds)
    $peakBytes = $p.PeakWorkingSet64
    if ($peakBytes -gt 0) { $rss.Add($peakBytes / 1MB) }
  } finally {
    $p.Dispose()
  }
}
function Median([double[]]$values) {
  $sorted = @($values | Sort-Object)
  $mid = [int][Math]::Floor($sorted.Count / 2)
  if ($sorted.Count % 2 -eq 0) { return (($sorted[$mid - 1] + $sorted[$mid]) / 2.0) }
  return $sorted[$mid]
}
$rssMedian = if ($rss.Count -gt 0) { Median $rss.ToArray() } else { $null }
$result = [ordered]@{
  kind = 'process_probe_only_not_agent_parity'
  language = 'C#'
  publish = 'Native AOT'
  os = 'windows'
  arch = 'x64'
  command = '--help'
  iterations = $Iterations
  wall_ms_median = (Median $wall.ToArray())
  cpu_ms_median = (Median $cpu.ToArray())
  peak_rss_mib_median = $rssMedian
  rss_status = $(if ($null -eq $rssMedian) { 'unavailable_after_fast_process_exit' } else { 'reported_by_process_api' })
  binary_bytes = (Get-Item $exe).Length
  warning = 'Process probe only. Windows Process CPU resolution may be coarse; RSS may be unavailable for short-lived exited processes. Not agent feature parity.'
}
$parent = Split-Path -Parent $Out
New-Item -ItemType Directory -Path $parent -Force | Out-Null
$result | ConvertTo-Json -Depth 5 | Set-Content -Encoding utf8 $Out
$result | ConvertTo-Json -Depth 5
