# Boot nativo e tela de título

Primeiro marco público de preservação: recompilação estática PowerPC → C++ →
Windows x64. O executável local inicializa GPU D3D12, áudio e controles. O usuário
confirmou intro e tela de título com cenário 3D.
O perfil LIVE virtual passou pelo gate do título; o aviso seguinte é do serviço
de save de rede, ainda não substituído pelo armazenamento local.

## Validação

- Geração sem `--force`, com auditorias de labels e placeholders sem achados.
- Correção da descoberta de destinos indiretos terminados em bctr.
- 237.086 registros conferidos na última geração e nenhum início PDATA ausente.
- Oito testes CTest nativos passaram; cinco testes Python passaram.
- Build com `-O1`; desempenho ainda sem medição comparativa de FPS.

## Limitações

Ainda não jogável: o título apresenta erro de save de rede. Não foi demonstrada
entrada no menu de modos ou em partida. Skirmish, todos os mapas/modos,
Happy Cards e inventário persistente no jogo continuam pendentes. O backend
SQLite passou testes isolados, mas não está integrado ao inventário original.

Esta pre-release distribui fontes próprios e patches. O usuário precisa fornecer
sua cópia local do jogo e executar o pipeline descrito no README. Executável
recompilado, recursos, imagem carregada, código traduzido e perfis ficam locais.
