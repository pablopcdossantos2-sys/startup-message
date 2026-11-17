# Política de Privacidade — StartupMessage

**Última atualização:** 2026-11-17

O StartupMessage **não coleta, transmite nem compartilha nenhum dado pessoal**.

- O app **não envia dados automaticamente pela internet** e não possui telemetria, anúncios ou contas. O link de suporte no rodapé pode abrir o navegador, somente quando acionado pelo usuário.
- O título, os textos, as checklists, o tempo e as preferências visuais ficam salvos **somente no seu computador**
  (na área `LocalState` privada do pacote MSIX; durante o desenvolvimento, em `%LOCALAPPDATA%\DailyMessage\config.json`).
- As **imagens** que você adiciona são **copiadas** para a pasta local `media` (junto das configurações) e
  nunca saem do seu computador. As marcações das checklists não são salvas.
- Os blocos **Digitar novamente** (lista de regras ou texto longo) guardam apenas o **conteúdo de referência** na configuração local. As respostas digitadas na mensagem inicial são mantidas somente enquanto a janela está aberta: **não são gravadas em disco, histórico ou logs**. A cada novo login, os campos de transcrição começam vazios.
- Os campos de transcrição restringem as funções usuais de colar; o aplicativo não lê o conteúdo da área de transferência para conferir as respostas.
- Um pequeno arquivo de log local (`dailymessage.log`) pode registrar erros técnicos; ele nunca é enviado a ninguém.
- Para remover tudo, desative "Iniciar junto com o Windows", desinstale o app e apague a pasta local de configurações, se desejar remover os dados restantes.

Contato e solicitações de privacidade: https://github.com/pablopcdossantos2-sys/startup-message/issues

Para questões privadas, use um canal de contato publicado pelo responsável antes da submissão à Microsoft Store.
