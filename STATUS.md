# Estado verificável — 18/10/2026

**Ainda não jogável. Não foi demonstrada entrada em partida.**

## Último resultado

O usuário confirmou intro e tela de título com cenário 3D. Após implementar um
perfil LIVE virtual inteiramente local, o log registra estado 2, informações de
perfil coerentes e verificação de privilégios sem restrição. O bloqueio anterior
por perfil/Gold foi ultrapassado. A captura seguinte mostra falha no serviço de
save de rede: essa é a fronteira que precisa ser substituída por armazenamento local.

O primeiro avanço após o perfil encontrou um acesso inválido provocado pelos
stubs de XAuth. Foram implementados tamanho de estrutura, conclusão de shutdown e
retorno nulo explícito para o buffer ausente, conforme a ABI observada no Netplay.
O teste seguinte chegou ao aviso de save sem esse crash. Não há ainda servidor
local do jogo funcional, embora o perfil virtual já responda às consultas XAM.

| Requisito | Estado e evidência |
|---|---|
| Pacote original | LIVE 58410AE9 localizado; original preservado |
| Extração | 402 arquivos e 34 diretórios; tamanhos, SHA-256 e 113.431 blocos SHA-1 verificados |
| Autenticidade RSA/árvore STFS superior | Não implementada; hashes não provam autenticidade |
| Recursos | 362 ZRES decodificados, 102 JSON e 1.516 definições de itens analisados |
| Recompilação estática | 326 C++ gerados sem --force; nenhum JIT PowerPC |
| Descoberta de funções | Patch bctr corrigiu centenas de entradas; 237.086 registros conferidos, sem inícios PDATA ausentes |
| Auditorias de tradução | Sem labels ausentes ou placeholders explícitos no escopo dos verificadores |
| Windows x64 | Executável nativo compilado com Clang ABI MSVC; dados e código traduzido ficam locais |
| Gráficos/áudio/input | D3D12, áudio e SDL inicializados; título 3D observado pelo usuário |
| Desempenho | Tradução compilada com -O1; ganho de FPS ainda não medido |
| Perfil | Identidade virtual LIVE, nome, XUID, tier e permissões coerentes; logs confirmam uso real |
| Autenticação XAuth | ABI mínima implementada e testada; não produz tokens de serviços reais |
| Rede | Sockets e HTTP selecionados falham explicitamente; não existe servidor remoto necessário ao projeto |
| Save | Backend SQLite com transações/revisões/backup testado; ainda não integrado ao serviço de save do jogo |
| Testes | Oito testes CTest e cinco testes Python passaram; gameplay não coberto por eles |
| Menu/Skirmish | Ainda não demonstrados |
| Mapas e modos | Recursos e identificadores encontrados; desbloqueio/fluxos ainda não implementados |
| Happy Cards/equipamentos/progressão | Dados originais analisados; criação, alterações e persistência no jogo pendentes |

## Próximas tarefas

1. Rastrear chamadas e formatos do serviço de save na inicialização.
2. Implementar seu adaptador local com criação/restauração de dados válidos.
3. Entrar no menu de modos e criar uma partida usando IA e recursos originais.
4. Validar vitória/derrota, recompensas, equipamentos e reinício do processo.
5. Ampliar para mapas/modos presentes; medir desempenho antes de afirmar melhora.

Releases seguem marcos verificáveis documentados em docs/RELEASES.md.
Arquivos proprietários, código traduzido, executável e perfis não são publicados.
