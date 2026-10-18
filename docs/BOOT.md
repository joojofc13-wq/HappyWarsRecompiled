# Diagnóstico incremental do boot nativo

## Teste manual e otimização de 18/10/2026

O usuário relatou intro lenta e uma cena 3D antes do fechamento. O log manual
identificou `0x82D1D0A0`, adaptador original que define r5=6 e salta para
`0x82D1B380`. A varredura de argumentos constantes elevou as declarações
automáticas de 235 para 238. Cinco casos nativos da tradução original desse
adaptador passaram dentro da suíte de seis testes.

A build foi recompilada com `-O1` em vez de `-O0`. O PE passou de 210.965.504
para 118.457.856 bytes. Isso verifica a otimização aplicada, sem medir FPS.
O teste seguinte avançou até outro destino não registrado, `0x82BA52B8`,
em 21,06 segundos; foi falha real, sem encerramento pelo limite do teste.
Esse destino é um adaptador de cinco instruções que carrega função e argumentos
do objeto e termina em bctr. O corpo original está documentado em
`logs/closure-adapter-disassembly.log` e ganhou limite explícito de 0x14 bytes.
Menu e Skirmish ainda não foram confirmados.

Os testes usam o executável Windows x64 compilado, com os recursos locais do
usuário. O encerramento após um erro fatal é uma falha de boot, não uma partida
bem-sucedida. Não há confirmação de menu, renderização correta ou Skirmish.

## Destinos observados e correções baseadas no original

| Destino | Evidência e ação |
|---|---|
| 0x83393258 | Quatro instruções: cmpwi, retorno condicional, tail branch, blr. Entrada explicitada, com registradores compartilhados. |
| 0x8342DA20 | Comparador leaf de 0x88 bytes; último blr em 0x8342DAA4. Entrada explicitada. |
| 0x83353380 | Exatamente blr. Varredura encontrou 17 destinos semelhantes referenciados em dados e ausentes da tabela; lista gerada antes do build e opcode verificado no boot. |
| 0x830613E0 | Função leaf chamada na thread de áudio; leitura de campos do objeto, retornos condicionais e chamadas virtuais em cauda. Corpo de 0x100 bytes, último blr em 0x830614DC; próxima função com prólogo e PDATA começa em 0x830614E0. Entrada explicitada. |
| 0x83066CA0 | Seis instruções terminando em chamada virtual em cauda, bctr em 0x83066CB4. Entrada de 0x18 bytes explicitada; teste seguinte passou desse ponto. |
| 0x830697E8 | Ajusta r3 em -36 e salta para 0x83069388. Incluído com outros 97 adaptadores pequenos derivados das instruções originais; teste seguinte passou desse ponto. |
| 0x8327D108 | Um de sete adaptadores virtuais consecutivos de 0x20 bytes. Corpos completos inspecionados; cópia de argumentos, seleção de flags e bctr. Entradas da família explicitadas. |
| 0x83329250 | Duas leituras da tabela virtual, mtctr e bctr; corpo completo de 0x10 bytes inspecionado. Entrada observada em boot e explicitada. |
| 0x82B67950 | Sete instruções, encerrando em bctr em 0x82B67968. Carrega o índice do objeto e escolhe da tabela 0x820BAF2C. Os dois destinos observados, 0x82B67940 e 0x82B67930, já estão registrados. Entrada explicitada. |

O corpo de retorno imediato preserva os registradores. Não fabrica resultado
positivo de autenticação, perfil, inventário ou partida, e não serve como fallback
para qualquer função desconhecida.

`prepare_thunk_boundaries.py` verifica padrões curtos `b` ou `addi r3,r3,imm; b`
em endereços referenciados junto a outros ponteiros de código. Exige salto
relativo incondicional sem link para uma entrada já registrada. Produz somente
limites explícitos no TOML; o SDK continua traduzindo as instruções originais.
Os 98 casos encontrados não incluem protocolos de servidor simulados.

A segunda varredura acrescentou nove entradas com o padrão exato de quatro
instruções: carregar a tabela virtual a partir de r3, carregar seu destino em
r11, mtctr r11, bctr. São 107 declarações automáticas no total. As chamadas
virtuais continuam usando os destinos originais do objeto em memória.

A varredura seguinte também examina o padrão completo de quatro instruções na
seção .text. Isso cobre adaptadores cujos endereços são montados em código, sem
ponteiros em .rdata. Exclui os intervalos de funções declarados manualmente e os
intervalos originais PDATA; não transforma seus blocos internos em funções.
Essa primeira ampliação encontrou 992 candidatos, mas a auditoria detectou dez
branches condicionais que ficaram com destinos não resolvidos após a separação
de blocos internos. Essa versão não foi usada no teste de boot. A seleção final
também exige um terminador incondicional ou padding antes do adaptador.
O conjunto corrigido contém 228 entradas automáticas, com zero placeholders e
zero labels ausentes na auditoria. Esses números são declarações
de entrada verificadas, não modos jogáveis nem uma estimativa de trabalho restante.
Uma primeira seleção sem essa exclusão foi rejeitada por limites sobrepostos;
a configuração corrigida passou na validação normal do SDK, sem --force.

O preflight agora bloqueia a compilação se as auditorias encontrarem labels
ausentes ou traps explícitos de tradução. Os resultados só são reaproveitados
quando o SHA-256 de todos os arquivos C++ gerados e dos scripts de auditoria
coincide. Um build sem alteração exige apenas a conferência dos hashes.

Um teste nativo executa o corpo traduzido original de 0x830697E8 sem editar suas
instruções, usando um observador como destino apenas no teste. Cinco entradas
verificam ajuste de ponteiro, chamada em cauda e preservação dos registradores
conferidos. Isso não testa a funcionalidade do destino real nem gameplay.

Outro teste executa a tradução original de 0x8327D108 com páginas de memória
sintéticas, uma tabela virtual e um observador na tabela de dispatch do SDK.
Quatro casos verificam cópia dos argumentos, flags, destino virtual e LR. A
reserva de 4 GiB é apenas de endereços; somente três páginas são comprometidas.
O teste não simula inicialização de partidas.

O corpo original de quatro instruções em 0x82C3DD30 também participa desse teste:
mais quatro casos conferem os argumentos preservados, destino, LR e pilha.

O dispatcher indexado 0x82B67950 também foi copiado sem alterar instruções para
um teste nativo. Quatro casos percorrem índices 0 e 1, usando os endereços de
destino da tabela original e observadores somente no teste. Verificam seleção,
argumentos, LR e registrador de pilha. Os seis testes CTest passam; ainda não
demonstram menu ou partidas.

O SDK também emite uma função com mais de 236 mil chamadas `SetFunction`, além
da tabela ordenada com os mesmos pares endereço/ponteiro. A compilação local usa
um loop sobre essa tabela com o mesmo sentinela. Antes de cada build, depois do
codegen, `verify_registration.py` exige igualdade completa e na mesma ordem entre
as duas saídas originais. A mudança reduz o custo de compilação sem remover
entradas ou inventar destinos.

A escolha do CLI diagnóstico fica no CMake do projeto, alterando a localização
do alvo importado `rex::rexglue` em todas as configurações. Uma edição anterior
no CMake gerado era sobrescrita pelo próprio codegen, permitindo que o build
voltasse a usar o CLI oficial lento. O comando do Ninja e o caminho do processo
foram conferidos depois da correção persistente. As bibliotecas do runtime
continuam vindo do SDK oficial fixado.

## Reproduzir e inspecionar

```powershell
py scripts/recompile.py
py scripts/audit_labels.py
py scripts/audit_codegen.py
py scripts/build.py --game --jobs 6
py scripts/runtime_smoke.py --seconds 20 --log-level debug
```

Para repetir a descoberta restrita de adaptadores após uma nova análise:

```powershell
py scripts/prepare_thunk_boundaries.py
py scripts/recompile.py
py scripts/prepare_thunk_test.py
py scripts/build.py --translation-test
```

O script de boot arquiva o log anterior e registra hash do executável, exit code,
limite de tempo e marcos encontrados no log. Esses marcos indicam inicialização
do runtime, não funcionamento de gameplay. O teste pode abrir uma janela e causar
uma piscada na tela durante a inicialização da GPU.

`audit_indirect_targets.py` relata referências em .rdata/.data para endereços de
código ausentes da tabela. A saída é uma lista de candidatos: inclui labels
internos e estruturas de exceção. Não deve virar uma configuração de funções sem
inspecionar o fluxo de controle e os limites originais.
