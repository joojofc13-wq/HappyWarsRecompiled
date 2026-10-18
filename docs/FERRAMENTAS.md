# Pesquisa das ferramentas

Repositórios consultados pelo navegador e clonados para examinar README,
CMake, código e licenças. Commits e metadados de releases estão fixados em
`config/upstream-lock.json`, com consulta em 17/10/2026.

| Projeto | Papel e conclusão |
|---|---|
| [ReXGlue SDK](https://github.com/rexglue/rexglue-sdk) | Escolha inicial: tradutor estático junto de runtime, memória, kernel, filesystem, input, áudio e GPU. CLI oficial executado, sem Xenia launcher/JIT. Versão usada 0.10.0.24-dev.gbd833a2, release nightly de 02/10/2026. Continua experimental; suporte ao Happy Wars não foi estabelecido. |
| [XenonRecomp](https://github.com/hedge-dev/XenonRecomp) | Traduz PowerPC para C++, mas seu README afirma que não fornece runtime. Análise de jump tables pode exigir adaptação por jogo; há limitações de exceções e MMIO. Seria alternativa de tradutor, sem eliminar o trabalho do runtime. Não foi alegado que seu runtime já execute Happy Wars. Nenhuma release apareceu na consulta do repositório. |
| [Xenia](https://github.com/xenia-project/xenia) | Usado como referência de XEX, STFS e nomes de ordinais do kernel. Não foi iniciado para executar o jogo. O repositório consultado remete builds a outro repositório; ausência de release nele não significa ausência de builds do Xenia. |
| [XBLA-Extract](https://github.com/ryzendew/XBLA-Extract) | Tem GUI PyQt6 e CLI Python. O código examinado infere início da file table por uma heurística de offsets e lê arquivos consecutivamente. Foi revisado, mas a extração efetiva usou Extract-STFS e verificação independente. |
| [Extract-STFS](https://github.com/jasonulbright/Extract-STFS) | PowerShell 5.1+, sem dependências adicionais. Release consultada v1.0.0. API real: -Path, -OutputDir, -ListOnly. MIT. O próprio projeto não verifica SHA-1: a validação adicional foi implementada neste projeto. Funcionou com o pacote real e preservou diretórios. |
| [Unleashed Recompiled](https://github.com/hedge-dev/UnleashedRecomp) | Referência de integração completa, CMake, runtime e patches específicos de um título. Release listada v1.0.3. Não foi tratado como runtime genérico pronto para Happy Wars nem copiado como jogo substituto. |

## APIs e divergências verificadas

A wiki Getting Started do ReXGlue consultada ainda mostra `--app_name` e
`--app_root`. O binário efetivamente usado exige `--project-name`, `--xex-path`,
`--game-root` e `--project-root`. Foi usado o `--help` do binário, e não copiado
o exemplo desatualizado.

O CMake da revisão inicialmente consultada tinha um mínimo Clang 18, enquanto
a documentação recomendava Clang 20+. A versão efetivamente usada foi 23.1.3,
com C++23, CMake 4.4.4 e Ninja 1.13.2. O SDK distribuído utiliza ABI MSVC.
Foi necessário preparar headers/libs MSVC e Windows SDK, em vez de vincular
seus tipos C++ com a ABI GNU do LLVM-MinGW.

O CLI gerou o nome normalizado `happywars`, apesar de receber `happy_wars`.
O caminho do XEX no init é resolvido a partir do diretório da chamada;
a primeira chamada foi corrigida ao executar dentro da pasta do projeto.
Os logs de ambas as tentativas foram mantidos.

## Licenças e redistribuição

O script Extract-STFS foi incluído com sua licença MIT. As alterações do
ReXGlue são distribuídas como patch sobre a revisão BSD-3-Clause, com a licença
original incluída. A montagem diagnóstica utiliza o runtime pré-compilado local,
sem incorporar seus binários ao pacote de fontes.

O SDK traz dependências com licenças próprias. O projeto não presume uma licença
única para todos os seus componentes. Os SDKs Microsoft, instaladores e headers
ficam locais e não devem ser incluídos em um repositório público deste trabalho.
O mesmo vale para os recursos, executável original e C++ derivado do jogo.
