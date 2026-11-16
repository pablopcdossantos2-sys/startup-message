[CmdletBinding()]
param(
    [switch]$CheckOnly
)

$ErrorActionPreference = "Stop"
$msixPath = Join-Path $PSScriptRoot "StartupMessage-validation.msix"
$certificatePath = Join-Path $PSScriptRoot "StartupMessage-test.cer"

if (-not (Test-Path $msixPath)) {
    throw "Arquivo StartupMessage-validation.msix não foi encontrado na mesma pasta deste instalador."
}
if (-not (Test-Path $certificatePath)) {
    throw "Certificado StartupMessage-test.cer não foi encontrado na mesma pasta deste instalador."
}

# Recupera nome/versão do manifesto real do pacote (sem presumir identidade padrão).
# A leitura ocorre antes de elevar privilégios ou instalar um certificado confiável.
Add-Type -AssemblyName System.IO.Compression.FileSystem
$archive = [System.IO.Compression.ZipFile]::OpenRead($msixPath)
try {
    $manifestEntry = $archive.GetEntry("AppxManifest.xml")
    if (-not $manifestEntry) { throw "MSIX sem AppxManifest.xml." }
    $reader = [System.IO.StreamReader]::new($manifestEntry.Open())
    try {
        [xml]$manifest = $reader.ReadToEnd()
    }
    finally {
        $reader.Dispose()
    }
}
finally {
    $archive.Dispose()
}
$identityNode = $manifest.SelectSingleNode("/*[local-name()='Package']/*[local-name()='Identity']")
if (-not $identityNode) {
    throw "Identidade do pacote não encontrada no manifesto."
}
$packageName = $identityNode.GetAttribute("Name")
$packageVersion = $identityNode.GetAttribute("Version")
if (-not $packageName -or -not $packageVersion) {
    throw "Identidade ou versão MSIX inválida."
}

Write-Host "==> Conferindo certificado público do pacote..."
$certificate = [System.Security.Cryptography.X509Certificates.X509Certificate2]::new($certificatePath)
if ($certificate.HasPrivateKey) {
    throw "O arquivo .cer deveria conter somente a chave pública, sem chave privada."
}
$signature = Get-AuthenticodeSignature -FilePath $msixPath
if (-not $signature.SignerCertificate) {
    throw "Não foi possível identificar o certificado que assinou o MSIX."
}
if ($signature.SignerCertificate.Thumbprint -ne $certificate.Thumbprint) {
    throw "O certificado fornecido não corresponde à assinatura deste pacote MSIX."
}

Write-Host "Pacote: $packageName | Versão: $packageVersion"
if ($CheckOnly) {
    Write-Host "TEST_KIT_SIGNATURE_AND_IDENTITY=PASS" -ForegroundColor Green
    return
}

# A instalação manual não pode substituir silenciosamente a versão da Store
# ou uma cópia de desenvolvimento já usada e configurada.
$prior = Get-AppxPackage -Name $packageName | Select-Object -First 1
if ($prior) {
    throw "Já existe uma instalação de $packageName (versão $($prior.Version)). Não será substituída. Faça backup das configurações e desinstale manualmente a versão antiga antes de instalar o kit de teste, se desejar."
}

$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = [Security.Principal.WindowsPrincipal]::new($identity)
$isAdmin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "O certificado de teste precisa ser confiado pelo computador. O Windows solicitará autorização de administrador." -ForegroundColor Yellow
    $arguments = '-NoProfile -ExecutionPolicy Bypass -File "' + $PSCommandPath + '"'
    $elevated = Start-Process -FilePath "powershell.exe" -Verb RunAs -ArgumentList $arguments -Wait -PassThru
    exit $elevated.ExitCode
}

Write-Host "==> Adicionando certificado a Computador Local > Pessoas Confiáveis..."
$storePath = "Cert:\LocalMachine\TrustedPeople"
$existing = Get-ChildItem $storePath | Where-Object Thumbprint -EQ $certificate.Thumbprint
$addedCertificate = $false
try {
    if (-not $existing) {
        Import-Certificate -FilePath $certificatePath -CertStoreLocation $storePath | Out-Null
        $addedCertificate = $true
    }

    Write-Host "==> Instalando StartupMessage..."
    Add-AppxPackage -Path $msixPath -ErrorAction Stop
}
catch {
    # Se a instalação falhar, não deixar um novo certificado de confiança na máquina.
    if ($addedCertificate) {
        Remove-Item -Path (Join-Path $storePath $certificate.Thumbprint) -Force -ErrorAction SilentlyContinue
    }
    throw
}

Write-Host ""
Write-Host "StartupMessage foi instalado com sucesso." -ForegroundColor Green
Write-Host "Abra o aplicativo pelo menu Iniciar."
Write-Host "O certificado público permanecerá em Pessoas Confiáveis enquanto este build de teste estiver instalado."
Write-Host ""
Read-Host "Pressione Enter para fechar"
