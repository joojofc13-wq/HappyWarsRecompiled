# Perfil local: pesquisa Xenia e Netplay

Fontes primárias consultadas em 18/10/2026:

- [Happy Wars no rastreador oficial do Xenia](https://github.com/xenia-project/game-compatibility/issues/1239):
  o relato de 2019 chega ao título após intros lentas e para na exigência de LIVE.
  É evidência histórica, não validação da nossa build.
- [XAM do Xenia original](https://github.com/xenia-project/xenia/blob/master/src/xenia/kernel/xam/xam_user.cc):
  a consulta de privilégios retorna a permissão negada. O runtime ReXGlue
  consultado mantém esse comportamento.
- [XAM do Netplay](https://github.com/Nexia360/xenia-canary/blob/netplay_canary_experimental/src/xenia/kernel/xam/xam_user.cc):
  consulta perfil e estado de login antes de liberar privilégios para perfis
  habilitados para LIVE. Estados e permissões precisam ser coerentes.
- [API de sessões do Netplay](https://github.com/Nexia360/xenia-canary/blob/netplay_canary_experimental/src/xenia/kernel/XLiveAPI.cpp):
  usa operações HTTP de registro e sessões. Sua existência não prova suporte ao
  backend particular de Happy Wars nem fornece uma implementação offline.

## Aplicação no port

O objetivo continua sendo execução local. Nenhum serviço Netplay foi conectado.
Não se importam credenciais nem perfis reais. Por solicitação do usuário, o
estado XAM agora representa uma conexão LIVE virtual (2) atendida inteiramente
em processo, sem conexão a serviços reais.

Foram identificados dois gates no código do título: um rejeita o estado local
em cache antes da consulta de privilégios; outro consulta a permissão 254.
O primeiro conjunto de hooks do jogo não removeu o bloqueio e foi substituído
por implementações XAM coerentes: estado 2, identidades online/offline, flag
LIVE, nome e permissões. MembershipTierFromXUID era um stub no runtime consultado;
agora responde tier 6 apenas para as identidades virtuais. Os testes validam
consistência entre APIs, usuários ausentes e ponteiros inválidos.

Os logs confirmam uso real dessas consultas e restrição zero no gate do título.
A captura seguinte apresenta outro aviso: serviço de save de rede indisponível.

A ABI mínima de XAuth foi comparada ao Netplay: Startup valida estrutura de oito
bytes, Shutdown escreve conclusão e GetTitleBuffer retorna zero quando não há
buffer. Stubs que deixavam o argumento antigo em r3 causavam leitura inválida.
Oito testes CTest passaram após a correção. O adaptador do serviço de save do
Happy Wars continua pendente; essa API de perfil não substitui o servidor do jogo.
