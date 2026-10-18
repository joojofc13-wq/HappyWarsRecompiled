# Happy Wars: evidências da versão disponível

## Identidade e extração

- Contêiner: LIVE, 467.415.040 bytes; título interno Happy Wars; Title ID 58410AE9.
- SHA-256 do pacote: `c70f6f0b979dad72cd54c0d912163686bcebd09ba114aa4bd35495825e2bee33`.
- Arquivos extraídos: 402, totalizando 463.663.802 bytes; mais 34 diretórios.
- Executável: `Default.xex`, 7.258.112 bytes.
- SHA-256 XEX: `0e4dde7ac8c1e81d6f7ec5dee62cc623e693e905a471232d1b0b28d6f0e8f548`.

Extract-STFS foi executado e uma implementação independente conferiu os blocos
referenciados e comparou cada arquivo extraído ao fluxo de bytes do pacote.
O manifesto completo está em `logs/extraction.json`. Os hashes não substituem a
verificação da assinatura RSA nem autenticam a procedência do pacote.
O wrapper recusa formatos resilientes com cópias alternadas de tabelas STFS,
cuja seleção ainda não implementa. Este pacote usa o formato somente leitura.

## XEX e PE

O XEX2 declara entrada `0x830F23C8`, base `0x82000000`, imagem de 38.469.632
bytes, header de `0x6000`, versão/base `0.0.0.2`, Media ID `061F2D01`.
O CLI do SDK informou timestamp 2012-09-20 18:11:53 UTC. Os tipos do formato
são encryption=1 e compression=2, conforme os enums do SDK consultado.

A imagem carregada pelo SDK foi lida via ReadProcessMemory, sem alterar o
processo, e preservada apenas em `private/loaded-image.bin`. Isso é análise do
loader do SDK, não execução do jogo. O procedimento reproduzível está em
`scripts/capture_image.py`; a origem e o endereço observado estão no log.

O PE declara Machine `0x01F2`, PowerPC big-endian. Seções observadas:

| Seção | RVA | Tamanho virtual |
|---|---|---:|
| .rdata | 0x400 | 2.036.628 |
| .pdata | 0x1F1800 | 614.200 |
| .text | 0x290000 | 20.948.316 |
| .data | 0x1690000 | 14.434.172 |
| .tls | 0x2454000 | 9 |
| .XBMOVIE | 0x2454200 | 12 |
| .idata | 0x2460000 | 1.828 |
| .XBLD | 0x2470000 | 336 |
| .reloc | 0x2470200 | 1.940.164 |

A .pdata contém 76.775 entradas, não uma certificação de igual quantidade de
funções corretamente traduzidas. O PE declara SizeOfImage 41.224.704, superior
à imagem XEX carregada. A seção .reloc se estende além do snapshot; não foi
analisada integralmente. Nenhuma conclusão de relocations corretas foi emitida.
Não há tabela de exports declarada no campo de segurança XEX nem no diretório
de exports PE examinado.

TLS: 64 slots, endereço bruto informado no relatório JSON, 8 bytes de dados;
stack padrão 524.288 bytes. O código de inicialização e seus efeitos ainda
precisam ser rastreados durante execução nativa.

## Imports e dependências críticas

Foram lidas duas bibliotecas: xboxkrnl.exe, com 365 registros, e xam.xex, com 474.
As entradas de thunk type=1 revelaram 412 funções: 175 kernel e 237 XAM.
Variáveis podem ter sido alteradas pelo loader do SDK; não foram reinterpretadas
como ordinais originais depois dessa alteração.

| Subsistema | Exemplos realmente importados | Situação |
|---|---|---|
| Memória | NtAllocateVirtualMemory, MmAllocatePhysicalMemoryEx, ExAllocatePool | Runtime disponível; comportamento do jogo não testado |
| Threads e tempo | ExCreateThread, NtSetTimerEx, NtCreateTimer, KeDelayExecutionThread | Exige validação na inicialização real |
| Gráficos | Família Vd, D3D9/XGRAPHC nas bibliotecas estáticas | Backend Xenos/D3D12 do SDK ainda não testado com este título |
| Áudio | XAudioRegisterRenderDriverClient, XAudioSubmitRenderDriverFrame | Recursos XWB/XSB/XGS presentes; há stubs na família de áudio |
| Input | XamInputGetState, XamInputSetState, XamInputGetCapabilities | Implementação do SDK; sem teste de controle no jogo |
| Conteúdo/perfil | XamContentCreateEx, XamContentFlush, XamUserReadProfileSettings, XamUserWriteProfileSettings | Formato de inventário do jogo não estabelecido |
| Rede/autenticação | XampXAuthStartup, XamGetToken, NetDll_XHttpSendRequest, NetDll_XNetStartup | Stubs e dependências a substituir localmente |

As bibliotecas estáticas registram XAUTH, XHTTP, XPARTY, XNET, XONLINE, XHV2,
XGRAPHC, XBOXKRNL, XAUDIO2, XACT3, D3D9 e outras. A presença não demonstra que
todos os seus caminhos sejam necessários ao Skirmish.

Busca de macros no código do SDK: 270 declarações com implementação, 137 stubs,
5 sem correspondência. Uma declaração de implementação também pode conter
comportamentos incompletos. Ver `logs/import-coverage.json`.

## Recursos reais e pistas offline

362 arquivos ZRES foram descomprimidos com zlib e tamanho declarado little-endian;
nenhuma falha foi encontrada nesse conjunto. Os originais não foram alterados.
102 arquivos JSON, com comentários de exportação, foram interpretados. Foram
encontradas 1.516 definições de itens, excluindo marcadores de versão. Os campos
incluem IDs, classes, raridade, slots, níveis, atributos e referências a buffs.
Isso não equivale a 1.516 instâncias de inventário criadas ou reconhecidas pelo jogo.

`ItemSpinner.json` contém seções de categorias, referências de loteria, sorteios
múltiplos, pontos e custos. Não foi demonstrado que essas seções determinem
sozinhas os resultados das Happy Cards; não foram inventadas probabilidades.

Há dados de bots, Warrior/Mage/Cleric, co-op e campanha. A lista de mapas
`media/stage/stageFileList.nut` cita 12 nomes de recursos, incluindo dois com
nomes de teste. No binário existem OFFLINE_NORMAL, OFFLINE_HANDICAP_MATCH,
OFFLINE_REPEL, OFFLINE_SUBJUGATION, OFFLINE_RELIEF e OFFLINE_TREASURE_HUNT.
Esses identificadores são pistas, não uma lista de modos jogáveis certificados.

O export de progressão contém OfflineExp, OfflineBoxRankUpRate e
OfflineBoxRankUpLimit. Isso sustenta investigar a lógica offline existente antes
de reimplementar progressão ou IA.

## Endereços para investigação

`scripts/xrefs.py` encontrou 2.199 branches diretos para thunks importados e 12
referências candidatas curtas lis/addi ou lis/ori a strings selecionadas.
Não é um analisador completo de fluxo de dados. Chamadas indiretas e loads via
r2 não estão incluídos.

| Endereço de função/código | Pista |
|---|---|
| 0x8269A5C8, 0x8269A648, 0x8269A6C8, 0x8269A740 | Referências a savedata/%s.txt; podem ser utilitários de desenvolvimento |
| 0x829245D8 | Referência a unlock_; significado exato pendente |
| 0x8292AEA0 | Referência a RewardBuffLotteryTable |
| 0x82932C78 | Referência a OfflineBoxRankUpLimit |
| 0x82BC2AD8, 0x82BC2B50 | Invocações da interface equipItem/deleteItem |
| 0x82E67228, 0x82E6723C | Branches para XHttpSendRequest/ReceiveResponse |
| 0x82E6C238, 0x82E6C2A0, 0x82E6C310 | Referências a APIs de perfil XAM |

Nenhum desses endereços foi modificado. Identificar o papel de uma string não
estabelece o layout de objetos nem autoriza assumir um protocolo completo.

## Tradução e testes nativos desta etapa

O gerador diagnóstico concluiu validação e emissão sem --force, produzindo 326
arquivos C++ e 235.592 definições de funções, além dos 412 imports. Foram
configurados seis limites baseados em instruções e PDATA. Uma auditoria posterior
encontrou seis corpos com labels ausentes: o parser de exceções estendia o corpo
do pai através de outro início de função declarado na PDATA. O patch preserva
esse limite sem eliminar o parsing dos metadados. Após nova emissão, todas as
235.592 definições passaram na auditoria de labels.

O teste nativo extraiu, sem editar suas instruções traduzidas, a rotina
0x82E0AE08 do C++ gerado. Ela executou buscas com entradas presentes, ausentes e
tabela vazia em 12 casos de memória de teste. Esse teste comprova apenas a
tradução e execução dessa rotina. Não valida a IA, o menu ou uma partida.

O backend SQLite também foi compilado para Windows x64 e testado em processos
separados. O código emitido ainda exige validação das exceções C++/SEH e dos
imports usados durante o boot. O manifesto inicial não habilita wrappers de
exceção automaticamente; não se presume equivalência integral do comportamento.
