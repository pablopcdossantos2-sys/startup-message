# StartupMessage — Microsoft Store

[![build](https://github.com/pablopcdossantos2-sys/startup-message/actions/workflows/build.yml/badge.svg)](https://github.com/pablopcdossantos2-sys/startup-message/actions/workflows/build.yml)
![Windows](https://img.shields.io/badge/Windows-10%20%7C%2011-0078D4)
![Python](https://img.shields.io/badge/Python-3.12-3776AB)
![License](https://img.shields.io/badge/license-MIT-green)

Aplicativo **gratuito, planejado para distribuição pela Microsoft Store**, que exibe uma **mensagem personalizada quando o usuário entra no Windows**. Ela pode conter textos, imagens, checklists e exercícios obrigatórios de **digitar novamente**. A janela só poderá ser fechada quando o **tempo configurado** terminar **e** todas as verificações obrigatórias forem concluídas.

<!-- Adicione capturas de tela em docs/screenshots e referencie aqui -->
<!-- ![Configurações](docs/screenshots/settings.png) ![Mensagem](docs/screenshots/message.png) -->

## ✨ Recursos

- 🚀 **Inicia com o Windows** (opcional, liga/desliga com um clique)
- 🧱 **Mensagem em blocos**, na ordem que você quiser:
  - 📝 **Texto** — curto ou muito longo (até 20.000 caracteres por bloco e 30.000 no total), em estilo título, normal ou nota
  - 🖼️ **Imagem** — PNG, JPG, GIF (1º quadro), BMP ou WebP, com legenda opcional
  - ✅ **Checklist interativa** — itens que você marca ao abrir o computador; pode ser **obrigatória** para fechar a janela
  - ⌨️ **Digitar novamente — Regras** — cada regra aparece separadamente e exige sua própria transcrição, sem copiar e colar
  - 📜 **Digitar novamente — Texto longo** — transcrição integral de um texto multilinha, respeitando pontuação, maiúsculas e quebras de linha
- 🪟 **Janela flexível**: ajusta o tamanho ao conteúdo, pode ser redimensionada/maximizada, quebra o texto automaticamente, rola quando o conteúdo é grande e **nunca distorce as imagens**
- ⏳ **Tempo obrigatório** (3 a 600 s) com **contador regressivo** abaixo da mensagem
- 🔒 Enquanto a saída não é permitida, o **X** da janela e o botão **Ok** ficam **esmaecidos e inativos**; Alt+F4 e minimizar também são bloqueados
- 🎨 Visual moderno: tema **claro / escuro / sistema**, 4 cores de destaque, cantos arredondados
- 👀 Botão **Visualizar** para testar antes de salvar; a prévia tem um botão **Fechar prévia**, mesmo quando restam exercícios por concluir
- 🌎 Português (Brasil) e inglês
- 🔐 **Sem transmissão automática de dados** (links de suporte abrem o navegador somente quando clicados; [Privacidade](PRIVACY.md))

## 📥 Instalação

A versão de usuário será distribuída exclusivamente pela **Microsoft Store**. Não haverá ZIP portátil nem instalação manual.

A compilação automática disponibiliza **somente pacotes de validação**; não envie o artefato `VALIDATION-ONLY` à Microsoft Store. A geração de um pacote para submissão exige aprovação da arte, canal de suporte e testes Windows conforme [instruções de publicação](docs/STORE_PUBLISHING.md).

Para testar uma compilação de desenvolvimento, baixe o artefato **StartupMessage-MSIX-TEST-KIT** na execução do GitHub Actions e siga o [guia de instalação do pacote de teste](docs/INSTALL_TEST_PACKAGE.md). O kit inclui o certificado público de teste e o instalador que o registra no local correto do Windows.

## 🚀 Como usar

1. Abra o **StartupMessage**.
2. Defina o **título** e monte o conteúdo com **+ Texto**, **+ Imagem**, **+ Checklist**, **+ Digitar novamente: Regras** e **+ Digitar novamente: Texto longo**. Use ↑ ↓ para reordenar e ✕ para remover.
3. Para exigir uma **lista de regras**, adicione o bloco de regras e escreva **uma por linha**. Na mensagem inicial cada regra terá um campo de resposta separado (até 30 regras, 200 caracteres por regra).
4. Para exigir um **texto maior**, adicione o bloco de texto longo e escreva o conteúdo completo (até 20.000 caracteres). As quebras de linha devem ser reproduzidas.
5. Em uma checklist, escolha se os itens precisam estar marcados para permitir o fechamento.
6. Defina o **tempo obrigatório**, ative **Iniciar junto com o Windows**, teste com **Visualizar** (que pode ser fechada a qualquer momento) e clique em **Salvar**.

> As marcações e as respostas digitadas **não são salvas**: a cada inicialização, todos os itens começam pendentes. O texto de referência é salvo localmente, como os demais blocos.

## 🔒 Como funciona o bloqueio (e seus limites)

Na mensagem de inicialização, a janela só pode ser fechada quando **o tempo zerou E todos os itens obrigatórios estão marcados E todas as transcrições estão corretas**. Até lá ela fica visível, o **X** é desabilitado via API do Windows, o **Ok** permanece inativo e minimizar é impedido (redimensionar e maximizar continuam permitidos).

Nos blocos **Digitar novamente**, o texto de referência é exibido como rótulo não selecionável, e os campos de resposta rejeitam os eventos e atalhos de colagem usuais (Ctrl+V, Ctrl+Shift+V, Shift+Insert, eventos de colar e botão central do mouse). A comparação é exata, incluindo caixa, espaços, pontuação e linhas; apenas equivalências canônicas Unicode e CRLF/LF são aceitas. Essa restrição é uma medida de interface, **não uma proteção contra programas externos que simulem teclas**, macros ou ferramentas de acessibilidade. **A prévia não bloqueia o usuário**: pode ser encerrada mesmo com exercícios pendentes.

Por design — e por exigência das políticas da Microsoft Store — o app **não** interfere no sistema: você ainda pode usar o **Gerenciador de Tarefas**, **Ctrl+Alt+Del** e **desligar/reiniciar** o computador normalmente. O limite máximo de tempo é de 10 minutos.

## ⚙️ Inicialização automática

| Distribuição | Mecanismo |
|---|---|
| **Microsoft Store (MSIX)** | `windows.startupTask` (API `StartupTask`). Também gerenciável em *Configurações → Aplicativos → Inicialização*. |

`StartupMessageRunner.exe` exibe a mensagem no boot; `StartupMessage.exe` abre as configurações.

## 🛠️ Desenvolvimento

Requer **Windows 10/11** e **Python 3.12** para reproduzir exatamente o ambiente do CI.

```powershell
git clone https://github.com/pablopcdossantos2-sys/startup-message.git
cd startup-message
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-lock.txt  # ambiente reproduzível validado no CI para Windows/Python 3.12
python packaging/make_assets.py          # ícones placeholder
python launcher.py --settings            # abre as configurações
python launcher.py --startup --no-delay  # simula a mensagem de boot
python -m pytest -q                      # testes
```

Antes de considerar o aplicativo pronto para publicação, conclua o [roteiro de validação funcional no Windows](docs/WINDOWS_VALIDATION.md). O CI também instala uma cópia assinada temporariamente para validar o registro MSIX e as APIs WinRT; o artefato publicado pelo workflow é somente o MSIX não assinado.

## 📦 Gerar o pacote MSIX

O empacotamento requer Windows 10/11 SDK (makeappx.exe) e os valores de identidade fornecidos pelo Partner Center. Execute packaging/build.ps1 com IdentityName, Publisher, PublisherDisplayName e DisplayName. O MSIX será criado em release/. A versão destinada à Store não precisa ser assinada localmente; a Microsoft assina o pacote durante a publicação. Consulte docs/STORE_PUBLISHING.md.

## 🗂️ Estrutura

```
src/dailymessage/   código-fonte (GUI, blocos, mídia, autostart, config, i18n, Win32)
packaging/          PyInstaller (.spec), AppxManifest, build.ps1
tests/              testes automatizados
docs/               guia de publicação na Store
```

## 🗺️ Ideias futuras

Formatação rica (negrito/links), GIF animado, múltiplas mensagens por dia da semana, importar/exportar mensagens.

## 🤝 Contribuindo

Issues e PRs são bem-vindos! Rode `python -m pytest` antes de enviar.

## 📄 Licença

[MIT](LICENSE) © pablopcdossantos2-sys
