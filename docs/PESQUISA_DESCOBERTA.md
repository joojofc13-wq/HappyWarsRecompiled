# Descoberta de funções: pesquisa aplicada — 18/10/2026

O pipeline oficial combina PDATA, chamadas diretas, RTTI/vtables, análise de
blocos e preenchimento de lacunas. Uma execução não enumera todas as chamadas
virtuais que podem surgir depois de estados ou recursos ainda não percorridos.
[Pipeline do ReXGlue](https://github.com/rexglue/rexglue-sdk/wiki/Codegen-Pipeline-Overview).

O próprio projeto recomenda limites explícitos para funções não descobertas e
revisão dos limites de chamadas em cauda. Não recomenda forçar geração como
solução para chamadas não resolvidas.
[Estrutura gerada](https://github.com/rexglue/rexglue-sdk/wiki/Generated-Code-Structure).

Um relato no XenonRecomp foi resolvido identificando dados de tratamento de
exceção que tinham sido confundidos com instruções. Isso reforça a necessidade
de separar dados de código antes de transformar candidatos em funções.
[Discussão com o mantenedor](https://github.com/hedge-dev/XenonRecomp/issues/114).

Há também uma proposta de extração em lote de limites a partir de HTML exportado
do IDA. O autor relata recuperar 39 de 42 limites do exemplo Unleashed; a técnica
depende de análise externa e não certifica cobertura completa do nosso jogo.
[PR 98](https://github.com/hedge-dev/XenonRecomp/pull/98).

O port Unleashed mantém limites manuais para casos com jump tables ausentes de
PDATA. Seus endereços são específicos daquele jogo e não podem ser reaproveitados
como endereços de Happy Wars.
[Configuração original do port](https://github.com/hedge-dev/UnleashedRecomp/blob/main/UnleashedRecompLib/config/SWA.toml).

## Aplicação neste projeto

- As instruções e referências originais orientam as declarações de entrada em lote.
- As auditorias de labels e traps são gates de compilação, com cache por SHA-256.
- `py scripts/build.py --diagnostics` executa a validação e produz
  `logs/entry-diagnostics.json`, sem compilar o jogo nem abrir sua janela.
- O relatório enumera todas as entradas PDATA conhecidas ausentes da tabela,
  destinos observados em logs e referências especulativas em dados. Estas últimas
  incluem labels internos e não representam uma contagem de funções faltantes.
- A revisão do SDK encontrou que a segmentação de lacunas não tratava o `bctr`
  canônico como terminador. O patch acrescenta esse caso, conservando descoberta
  de CFG e limpeza de funções absorvidas; `bctrl` continua sendo uma chamada.
  A primeira geração encontrou 833 entradas adicionais. A auditoria identificou
  12 branches na mesma função com switch; seu corpo completo foi delimitado a
  partir do original. O resultado final tem 832 entradas a mais que a base,
  auditorias limpas e cinco métodos reais encontrados sem declaração manual.

## Outras pistas verificadas

O relato de compatibilidade da versão Xbox 360 descreve demora nos vídeos
iniciais e exigência de login após a tela de título. É uma observação de 2019
em outra execução; não comprova o estado deste port ou a equivalência da versão.
[Relato original do Xenia](https://github.com/xenia-project/game-compatibility/issues/1239).

Na discussão original do HappyWarsModTool, o autor explica a dependência de
perfil/inventário mesmo quando o combate Skirmish é local. Em 2023 informou
que os repositórios antigos foram removidos e que a ferramenta seguinte não era
aberta. Os endereços de ambos os repositórios retornaram 404 nesta pesquisa;
nenhum código deles foi obtido ou aplicado.
[Discussão do autor](https://steamcommunity.com/app/246280/discussions/0/2995421717747776122/),
[resposta sobre remoção do código](https://steamcommunity.com/app/246280/discussions/0/2995421717747776122/?ctp=5&l=finnish).

Não há execução de interpretador nem retorno fictício para atravessar funções
sem implementação. As gerações continuam exigindo validação sem `--force`.
