# Patches locais

## rexglue-gap-cleanup.patch

Base: `bd833a2ab69d305f99ddf57418fc38ffec8af93d`.
Contém duas otimizações de análise e logs de diagnóstico:

1. Um índice reverso registra quem aguarda cada destino de branch. A adição de
   uma função consulta somente esses chamadores, mantendo a resolução original.
   O algoritmo original e o indexado foram comparados após cada uma de 20.000
   operações, incluindo remoção, substituição e registros obsoletos. Os estados
   observados foram idênticos.
2. A limpeza de GAP_FILL procura somente entradas de gaps dentro dos limites de
   cada função e preserva o predicado containsAddress. Uma comparação contra o
   laço original em 300 grafos com sobreposições e blocos descontínuos passou.

O diagnóstico mostrou que a demora principal ocorria no registro, antes da
limpeza. Com ambas as alterações, a análise real passou de uma tentativa
interrompida após mais de 20 minutos de CPU para validação em 13,3 segundos.
A primeira validação encontrou quatro destinos ausentes, corrigidos por limites
baseados no código original. A emissão revelou mais dois limites incorretos,
também corrigidos em config/function-boundaries.toml.

Nenhum opcode ou comportamento de jogo é substituído por esse patch. Os testes
de equivalência cobrem as consultas alteradas; não provam a correção integral
do recompilador ou de todas as funções do título.

Fontes dos testes e do build: `tools/diagnostic/`. A referência original é obtida
com git show da revisão fixada durante o configure. O runtime permanece o pacote
binário oficial da mesma revisão; o CLI é recompilado localmente.

O patch também impede que a extensão inferida por metadados de exceção atravesse
o início de outra função declarada na PDATA. A extensão anterior incorporava
parcialmente funclets adjacentes em seis corpos C++, gerando gotos sem labels.
A leitura do PowerPC e da PDATA confirmou funções separadas. A nova análise
mantém o parsing dos metadados e as funções separadas; a auditoria de todas as
235.592 definições passou de seis funções com labels ausentes para zero.
Isso não certifica a execução de exceções C++/SEH no jogo, que permanece pendente.

## msvc-wine-required-sdk-only.patch

Base: `514f8ea34842cd6d831804d0e9658d3a32870ae1`.
Limita a extração administrativa dos MSI do Windows SDK aos headers, bibliotecas
e ferramentas necessários ao build x64, incluindo headers compartilhados
OnecoreUap. O SDK de certificação falhou com código 1603 e não era necessário.
Os payloads continuam vindo dos manifestos oficiais e são verificados pelo
downloader. Os arquivos Microsoft ficam exclusivamente locais.

## Integração CMake local

`generated/rexglue.cmake` recebeu uma opção REXGLUE_CODEGEN_EXECUTABLE para
selecionar o CLI diagnóstico. Sem ela, o build usaria o CLI oficial sem a
otimização. O módulo já gerado foi reconhecido pelo build em 0,2 segundo.

A aplicação usa HappyWars como OUTPUT_NAME. Para o primeiro build do jogo,
HAPPYWARS_RECOMP_OPT_LEVEL=0 desativa otimização apenas do C++ traduzido; o host
e o runtime permanecem Release. Isso reduz o tempo de compilação inicial.

A aplicação seleciona o plugin Xenos do SDK e o CMake o coloca junto ao EXE.
Esse componente traduz a GPU original; o PowerPC é C++ compilado previamente,
sem interpretar ou recompilar a CPU durante a execução.
# Descoberta após saltos indiretos

`rexglue-indirect-tail-branches.patch` aplica-se depois do patch de análise.
Acrescenta o `bctr` canônico aos terminadores de segmentação de lacunas; preserva
`bctrl`, descoberta de CFG e limpeza de regiões absorvidas. Os patches foram
conferidos contra o fonte que produziu o CLI local. As duas regressões do SDK
passaram; a validação do jogo encontrou cinco métodos adjacentes sem CONFIG.
A função com jump table 0x830FBEB8 precisou de limite completo de 0x188 bytes.
Veja `docs/PESQUISA_DESCOBERTA.md` e `logs/discovery-regression.json`.

