# ====================================================================
# AWS Lambda用 デプロイZIP作成スクリプト (Create-LambdaZip.ps1)
# ====================================================================

$ZipFileName = "lambda_deployment.zip"
$StagingDir = "build_staging"

Write-Host "📦 Lambda用のZIPパッケージを作成中..." -ForegroundColor Cyan

# 1. 過去の古いZIPや一時フォルダが残っていれば削除
if (Test-Path $ZipFileName) { 
    Remove-Item $ZipFileName -Force 
}
if (Test-Path $StagingDir) { 
    Remove-Item $StagingDir -Recurse -Force 
}

# 2. 作業用の一時フォルダ（ステージング領域）を作成
New-Item -ItemType Directory -Path $StagingDir | Out-Null

# 3. 🔴 ZIPに【含めたくない】不要なファイル・フォルダのリスト
$ExcludePatterns = @(
    "build_staging",
    "lambda_deployment.zip",
    ".git",
    ".github",
    ".venv",
    "env",
    "tests",
    "__pycache__",
    "*.ps1",          # このスクリプト自体も除外
    ".pytest_cache",
    "README.md"
)

# 4. 必要なファイル・フォルダだけを一時フォルダにコピー
Get-ChildItem -Path . | Where-Object {
    $itemName = $_.Name
    $shouldExclude = $false
    foreach ($pattern in $ExcludePatterns) {
        if ($itemName -like $pattern) {
            $shouldExclude = $true
            break
        }
    }
    !$shouldExclude
} | Copy-Item -Destination $StagingDir -Recurse -Force

# 5. 🤐 一時フォルダの「中身」をZIP圧縮（ルート直下に配置される構造にする）
Compress-Archive -Path "$StagingDir\*" -DestinationPath $ZipFileName -Force

# 6. 🧹 後片付け（一時フォルダの削除）
Remove-Item $StagingDir -Recurse -Force

Write-Host "✨ 成功！ Lambda用ZIP [$ZipFileName] が作成されました。" -ForegroundColor Green