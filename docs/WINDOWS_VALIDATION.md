# Roteiro de validação funcional no Windows

Este roteiro complementa os testes automatizados e o teste de instalação executados pelo GitHub Actions. Ele deve ser repetido com a versão instalada pela Microsoft Store antes da submissão final.

## O que o CI já verifica

O pipeline para Windows:

1. instala as dependências;
2. importa as APIs WinRT usadas para armazenamento e StartupTask;
3. executa os testes automatizados;
4. cria o pacote MSIX;
5. assina uma cópia separada com certificado temporário;
6. instala a cópia de teste no Windows;
7. confirma que o pacote tem os dois executáveis e que a extensão DailyMessageTask aponta para StartupMessageRunner.exe, desativada por padrão;
8. executa o modo de diagnóstico dentro da identidade MSIX, consultando a StartupTask e gravando/removendo um arquivo no espaço LocalState;
9. abre a GUI em modo de inicialização usando `StartupMessage.exe --startup --gui-smoke-test` e confirma que fecha automaticamente. O CI verifica a existência e o manifesto do Runner, mas **não simula o login real do Windows**;
10. abre a janela real de Configurações com `StartupMessage.exe --settings --gui-smoke-test`, verifica que o processo encerra sem erro e não substitui instalações preexistentes;
11. publica um kit de instalação de teste e o MSIX não assinado **como validação apenas**. A arte final e o contato real de suporte ainda precisam ser aprovados antes da Store.

A cópia assinada e o certificado temporário servem exclusivamente ao teste automático. Não os envie à Store.

## Testes manuais obrigatórios

Faça os testes em uma conta Windows comum, sem privilégios administrativos, após instalar o aplicativo pela Store.

### 1. Primeira execução e configurações

Para validar o kit de testes, abra a execução mais recente aprovada de [GitHub Actions](https://github.com/pablopcdossantos2-sys/startup-message/actions/workflows/build.yml), baixe o artefato **StartupMessage-MSIX-TEST-KIT**, extraia o ZIP e execute `Install-StartupMessage-Test.cmd`. A conta Windows usada para testar deve ser a mesma que iniciou o instalador; a autorização de administrador serve apenas para confiar o certificado do pacote de teste. Não substitua uma instalação existente sem salvar seus dados.

- [ ] Abrir o StartupMessage pelo menu Iniciar.
- [ ] Confirmar que o aplicativo foi instalado na conta Windows correta (não apenas na conta usada para autorizar a UAC).
- [ ] Abrir uma segunda vez o ícone do StartupMessage; confirmar que a janela existente vem para frente e permanece maximizada.
- [ ] Confirmar que a janela abre maximizada, sem encobrir indevidamente a barra de tarefas.
- [ ] Confirmar que a janela de configurações abre sem console ou erro.
- [ ] Adicionar blocos de texto, imagem, checklist, **Digitar novamente — Regras** e **Digitar novamente — Texto longo**.
- [ ] Cadastrar duas regras diferentes e um texto com dois parágrafos; salvar, reabrir e confirmar que conteúdo, ordem e títulos foram preservados.
- [ ] Reordenar blocos, remover um bloco e salvar.
- [ ] Fechar e abrir novamente; confirmar título, ordem, conteúdo e imagens.
- [ ] Alternar tema, cor de destaque e idioma; confirmar que o conteúdo digitado não se perde.
- [ ] Confirmar que as imagens importadas continuam disponíveis após reiniciar o computador.

### 2. Inicialização com Windows

- [ ] Na primeira execução, ativar **Iniciar junto com o Windows**.
- [ ] Confirmar que o Windows registra StartupMessage em Configurações → Aplicativos → Inicialização e no Gerenciador de Tarefas → Aplicativos de inicialização.
- [ ] Sair da sessão e entrar novamente (ou reiniciar); confirmar que StartupMessageRunner.exe apresenta a mensagem.
- [ ] Desativar a opção dentro do StartupMessage; entrar novamente e confirmar que a mensagem não aparece.
- [ ] Ativar novamente e desativar pelo painel de Inicialização do Windows; confirmar que o aplicativo reflete o estado bloqueado pelo usuário.
- [ ] Confirmar que o usuário consegue abrir as configurações manualmente mesmo com a inicialização automática desligada.

Observação: o usuário precisa abrir o aplicativo pelo menos uma vez para registrar a tarefa de inicialização. O controle final também fica disponível nas configurações do Windows.

### 3. Contador e bloqueio de fechamento

- [ ] Definir 5 segundos e abrir a prévia; verificar contador regressivo.
- [ ] Enquanto o contador estiver ativo, confirmar X e OK desabilitados e minimização impedida.
- [ ] Após zerar o contador, confirmar que OK e X liberam o fechamento quando não houver checklist obrigatória.
- [ ] Com checklist obrigatória, confirmar que a janela continua bloqueada após zerar o tempo enquanto houver itens pendentes.
- [ ] Marcar todos os itens; confirmar liberação.
- [ ] Desmarcar um item; confirmar que o bloqueio volta.
- [ ] Confirmar que checklist não obrigatória não bloqueia a saída.
- [ ] Com duas regras obrigatórias, digitar uma corretamente e confirmar que a outra continua pendente.
- [ ] Confirmar que uma letra, acento, pontuação, espaço ou maiúscula diferente não valida a resposta.
- [ ] Confirmar que o texto longo só valida quando todo o conteúdo, inclusive as quebras de linha, é digitado.
- [ ] Testar Ctrl+V, Ctrl+Shift+V, Shift+Insert, botão central do mouse e tentativa de copiar o rótulo de referência; confirmar que os campos de transcrição não aceitam a colagem usual.
- [ ] Confirmar que o contador zerado não libera a janela com regras ou texto longo ainda pendentes.
- [ ] Confirmar que as transcrições completas não liberam a janela enquanto o contador estiver ativo.
- [ ] Após liberar o fechamento, alterar uma resposta para torná-la incorreta e confirmar que a saída é bloqueada novamente.
- [ ] Com checklist, regras e texto longo simultâneos, confirmar que **todos** precisam estar concluídos para liberar o fechamento.
- [ ] Abrir a prévia com uma transcrição muito longa e confirmar que **Fechar prévia** e o X permitem encerrá-la sem concluir o exercício.
- [ ] Reiniciar a sessão e confirmar que todas as respostas retornam vazias, embora os textos de referência persistam.
- [ ] Em uma versão de teste instrumentada, simular falha do temporizador e confirmar que a janela se libera definitivamente, mesmo após clicar em itens de checklist.
- [ ] Confirmar que uma falha ao reabilitar o botão OK provoca encerramento seguro da janela em vez de bloqueio permanente.

### 4. Texto, imagens e dimensões

- [ ] Testar mensagem curta e texto próximo de 20.000 caracteres.
- [ ] Confirmar rolagem do conteúdo e permanência do rodapé com contador e OK visíveis.
- [ ] Redimensionar e maximizar a janela; confirmar quebra automática de texto sem cortes.
- [ ] Adicionar imagem panorâmica, imagem vertical e imagem pequena; confirmar proporção preservada e que a imagem pequena não é ampliada.
- [ ] Testar tema claro, escuro e sistema.
- [ ] Testar escala de tela 100%, 125% e 150%, além de monitor secundário quando disponível.
- [ ] Confirmar que GIF mostra o primeiro quadro, conforme limite documentado.

### 5. Limites de segurança do sistema

- [ ] Confirmar que a janela não impede abrir Gerenciador de Tarefas ou Ctrl+Alt+Del.
- [ ] Confirmar que o Windows permite desligar/reiniciar normalmente.
- [ ] Confirmar que não são necessários privilégios administrativos para o uso normal do aplicativo.

## Dados a registrar

Use `winver` (Win + R → digite `winver`) para identificar a edição e a versão do Windows. Use Configurações → Sistema → Tela para consultar a escala de exibição.

Anote versão do Windows, arquitetura, escala de tela, resultado de cada teste e qualquer mensagem de erro. Se houver falha, anexe o arquivo de log local do StartupMessage e uma captura de tela, removendo informações privadas da mensagem antes de compartilhar.

## Conclusão

O build e o teste de instalação no CI são validações automatizadas; não substituem os testes de interface e de reinicialização feitos em uma sessão real de usuário. Só considere a versão pronta para submissão depois de concluir os testes manuais acima em Windows 10 e Windows 11.
