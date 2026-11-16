# Publicação na Microsoft Store (gratuito)

## 1. Antes de tudo
1. Crie uma conta de desenvolvedor no **Partner Center** (conta pessoal).
2. **Reserve o nome** do app (ex.: "StartupMessage").
3. Em *Gerenciamento de produtos → Identidade do produto*, copie:
   `Package/Identity/Name`, `Package/Identity/Publisher` (CN=GUID) e `PublisherDisplayName`.

## 2. Gerar o pacote
```powershell
./packaging/build.ps1 `
  -IdentityName "<Package/Identity/Name>" `
  -Publisher "<Package/Identity/Publisher>" `
  -PublisherDisplayName "<PublisherDisplayName>" `
  -DisplayName "<Nome reservado>"
```
O arquivo `release/StartupMessage_<versão>_x64.msix` **não precisa ser assinado**: a Store assina. Não é gerado ZIP portátil.

**Atenção:** a compilação padrão permanece **somente para validação**, independentemente do nome do arquivo. Para solicitar um pacote destinado à Store, você deverá:

1. Substituir **todos** os ícones provisórios em `assets/` e `packaging/Assets/` pela arte final aprovada. Remover `assets/PLACEHOLDER_ASSETS.txt` **somente depois** de substituir e aprovar a arte.
2. Publicar e conferir um canal de suporte adequado para solicitações privadas na política de privacidade.
3. Executar e registrar todos os testes manuais de `docs/WINDOWS_VALIDATION.md` em Windows 10 e Windows 11.
4. Conferir a identidade e a versão no Partner Center. A versão MSIX deve ser superior à anterior.
5. Executar uma compilação específica para submissão, **sem** `-SignTest`:

```powershell
./packaging/build.ps1 `
  -IdentityName "pablopcdsantos.DailyMessage" `
  -Publisher "CN=A3E973B8-1411-4314-B754-F3DADD99C070" `
  -PublisherDisplayName "pablopcdsantos" `
  -DisplayName "StartupMessage" `
  -StoreSubmission -ArtworkApproved -PrivacyContactApproved -WindowsValidationPassed
```

Os três últimos parâmetros são **declarações manuais de aprovação** — não substituem revisão ou testes. O script também rejeita arquivos faltantes, inválidos, marcados como provisórios ou o ícone principal idêntico ao placeholder. O CI continuará publicando `VALIDATION-ONLY` até uma decisão explícita de alterar o pipeline.

## 3. Ficha do app (checklist)
- [ ] Categoria: *Utilitários e ferramentas* · Preço: **Gratuito**
- [ ] Classificação etária (IARC): sem conteúdo sensível, sem internet, sem compras
- [ ] **URL da Política de Privacidade**: link para `PRIVACY.md` (raw do GitHub ou GitHub Pages)
- [ ] Descrição pt-BR e en-US (modelo abaixo)
- [ ] ≥ 1 captura de tela (ideal 3–4: configurações com blocos, mensagem com imagem, mensagem com checklist) em 1366×768 ou maior
- [ ] Ícone de listagem 300×300 (`assets/icon.png` redimensionado)
- [ ] Notas de certificação (modelo abaixo)

## 4. Modelo de descrição (pt-BR)
> Exiba uma mensagem personalizada sempre que o Windows iniciar. Monte a mensagem com textos (curtos ou longos), imagens e checklists interativas. Escolha por quantos segundos ela deve permanecer na tela; enquanto o contador não zerar — e, se você criar uma checklist obrigatória, enquanto os itens não forem marcados — o botão de fechar fica indisponível. Tema claro/escuro, cores de destaque, 100% offline, sem anúncios e sem coleta de dados. Você pode desativar a inicialização automática a qualquer momento, no app ou em Configurações > Aplicativos > Inicialização.

## 5. Notas de certificação (modelo)
> O app declara a capacidade restrita `runFullTrust` porque é um aplicativo desktop Win32 (Python empacotado com PyInstaller) distribuído em MSIX. A inicialização automática usa o `windows.startupTask` (desativado por padrão; o usuário ativa pelo app ou pelo Windows). Como testar: abra o app, escreva um texto, adicione uma checklist com 2 itens, defina 5 s e clique em "Visualizar" — o X e o Ok ficam esmaecidos até o contador zerar e os 2 itens serem marcados. O bloqueio vale apenas para a janela do app; não interfere no Gerenciador de Tarefas nem no desligamento do Windows. O tempo é limitado a 600 s e definido pelo próprio usuário.

## 6. English listing description (en-US)

> Display a personalized message every time you sign in to Windows. Build your message with short or long text, images, and interactive checklists. Choose how long the message must remain on screen; if a checklist is marked as required, every item must also be checked before the window can close. Customize the theme and accent color. The app works offline, has no ads, and does not collect or transmit personal data. Startup is optional and can be managed in the app or in Windows Settings.

## 7. English certification notes

> StartupMessage is a Win32 desktop app packaged as MSIX and declares the restricted runFullTrust capability to run its Python/PyInstaller interface. Automatic startup uses the windows.startupTask extension, disabled by default and enabled only after the user requests it. To test: open the app, add text and a required checklist with two items, set five seconds, and select Preview. The Close and OK controls remain disabled until the countdown reaches zero and both items are checked. The app does not interfere with Task Manager, Ctrl+Alt+Del, or Windows shutdown. The maximum display time is 600 seconds.

## 8. GitHub Actions package identity

Identidade confirmada no Partner Center para este produto:

- `MSIX_IDENTITY_NAME`: `pablopcdsantos.DailyMessage`
- `MSIX_PUBLISHER`: `CN=A3E973B8-1411-4314-B754-F3DADD99C070`
- `MSIX_PUBLISHER_DISPLAY_NAME`: `pablopcdsantos`
- `MSIX_DISPLAY_NAME`: `StartupMessage`

O workflow já utiliza esses valores como padrão. Se desejar, eles também podem ser cadastrados como Repository Variables em Settings → Secrets and variables → Actions → Variables:

- MSIX_IDENTITY_NAME
- MSIX_PUBLISHER
- MSIX_PUBLISHER_DISPLAY_NAME
- MSIX_DISPLAY_NAME

O workflow usa esses valores, mas **publica somente `StartupMessage-MSIX-VALIDATION-ONLY`** nesta fase. Não submeta esse pacote à Store: falta aprovar os ícones definitivos, o canal de suporte e os testes funcionais em Windows. O MSIX não assinado não é instalável diretamente; use o kit de instalação de teste para validar.

## 9. Atualizações

Aumente `__version__` em `src/dailymessage/__init__.py` antes de cada nova submissão. A versão atual de validação é `1.0.1`, produzindo `1.0.1.0` no MSIX.

O script `python versioning.py` valida e imprime a versão MSIX. O CI verifica versões no formato `X.Y.Z` e, nos builds de tags, exige que a tag `vX.Y.Z` coincida exatamente com o código (por exemplo, `v1.0.1`). A Microsoft Store exige uma versão estritamente superior à da submissão anterior; **verifique no Partner Center qual foi a última versão publicada antes de enviar o próximo pacote**. O quarto componente permanece zero. Não troque `Identity Name` nem `Publisher`.

`requirements-lock.txt` fixa o conjunto de dependências usado no build de Windows e deve ser atualizado somente junto com uma nova validação do CI.
