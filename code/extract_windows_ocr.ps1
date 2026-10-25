param([string]$ImagePath, [switch]$Layout)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Runtime.WindowsRuntime
[Windows.Storage.StorageFile, Windows.Storage, ContentType=WindowsRuntime] > $null
[Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics.Imaging, ContentType=WindowsRuntime] > $null
[Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType=WindowsRuntime] > $null
function Await($Operation, $ResultType) {
 $method = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.IsGenericMethod -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' } | Select-Object -First 1
 $task = $method.MakeGenericMethod($ResultType).Invoke($null, @($Operation))
 $task.Wait()
 return $task.Result
}
$file = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($ImagePath)) ([Windows.Storage.StorageFile])
$stream = Await ($file.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
$decoder = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
$bitmap = Await ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
$result = Await ($engine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
if ($Layout) {
 $words = foreach ($line in $result.Lines) {
  foreach ($word in $line.Words) {
   @{ text=$word.Text; x=$word.BoundingRect.X; y=$word.BoundingRect.Y; width=$word.BoundingRect.Width; height=$word.BoundingRect.Height }
  }
 }
 @{ width=$bitmap.PixelWidth; height=$bitmap.PixelHeight; words=@($words); version=2 } | ConvertTo-Json -Depth 5 -Compress
} else {
 foreach ($line in $result.Lines) { $line.Text }
}
