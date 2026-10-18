# Caminho para Skirmish e modos locais

O pedido adicional de 17/10 inclui fazer o jogo funcionar com respostas locais,
desbloquear mapas e investigar todos os modos. O escopo viável depende dos
recursos e caminhos presentes nesta versão de 2012. Não se presume que contenha
mapas, modos ou conteúdo de atualizações posteriores ausentes dos arquivos.

## Evidência atual

Existem recursos de bots, classes e mapas; tabelas de progressão com parâmetros
offline; identificadores de modos offline; código de menu/tutorial/campanha em
Squirrel; parâmetros e definições extensas de itens. Isso favorece reutilizar
comportamentos locais originais. Nenhuma partida foi executada para comprová-los.

Também existem referências a Sentient, bibliotecas XAUTH/XHTTP/XONLINE e imports
de comunicação cujas implementações no SDK são stubs. Responder sucesso a toda
chamada não garante um objeto de perfil válido nem uma partida inicializada.

O protótipo inclui `offline_network_guard.cpp`, que substitui entradas de socket,
connect, send/sendto, accept e XHTTP selecionadas por falhas explícitas, com
WSAENETDOWN. Os testes do ABI passaram e os símbolos substituídos não constam
como imports de DLL no executável. Isso permite investigar falhas de boot sem
fornecer respostas fictícias de servidores. Não é um adaptador funcional do
backend do Happy Wars e não demonstra funcionamento com a rede física desligada.

## Integração proposta, ainda não implementada

1. Obter boot e rastreamento do menu. Registrar as transições e chamadas que
   impedem criar um perfil local e selecionar Skirmish.
2. Localizar a fronteira do serviço do jogo em processo. Investigar requisições,
   callbacks assíncronos, tamanhos e layouts por caminhos de código observáveis.
3. Fornecer identidade estritamente local e respostas locais somente para os
   contratos necessários. Não acessar contas, autenticação ou servidores ativos.
4. Reutilizar os objetos e validadores originais para instanciar equipamentos,
   atributos, buffs, upgrades e seleções. Manter IDs e referências consistentes.
5. Serializar esses objetos completos em snapshots versionados no SQLite e
   restaurá-los antes de o menu consultar perfil/inventário. Testar item a item
   dentro do jogo; uma lista de nomes não satisfaz esse requisito.
6. Identificar a criação original de partida, escolher recursos presentes,
   inicializar times e IA original, encerrar partida e aplicar recompensas locais.
7. Ampliar o desbloqueio para mapas/modos presentes e compatíveis com jogadores
   locais/bots, depois de cada fluxo funcionar. Testar as condições de vitória.

## Backend de armazenamento implementado

`OfflineStore` usa SQLite do Windows e schema 1. Um perfil local aleatório é
criado na primeira abertura. Cada record contém chave, versão do codec e BLOB;
o BLOB preserva bytes arbitrários, incluindo zeros e atributos binários.

Cada snapshot completo usa BEGIN IMMEDIATE/COMMIT, WAL e synchronous=FULL.
Uma revisão evita sobrescrever silenciosamente outro escritor. Erros durante
a atualização fazem rollback. Backup e restauração usam a API sqlite3_backup,
com verificação quick_check na abertura e rejeição de schemas futuros.

O backend foi compilado e testado em processos separados, inclusive uma saída
abrupta antes do COMMIT. **Não há ainda serializer do inventário original, hook
de criação/restauração dos objetos ou geração funcional de Happy Cards.**

As referências de loteria disponíveis são material de investigação. Não foi
inferida uma distribuição completa de raridades nem vendida como original uma
probabilidade escolhida para substituir o servidor.

## Critério de aceitação

Perfil local → menu → Skirmish → bots/objetivos → partida completa → recompensa
→ equipar/melhorar → fechar processo → reabrir → restaurar item e todos os seus
atributos. Repetir sem conexão de rede e validar mapas/modos um a um.
Todas essas etapas de gameplay continuam sem teste nesta entrega.
