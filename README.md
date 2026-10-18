# Happy Wars Recompiled — trabalho de preservação

Projeto real iniciado em 17/10/2026 para Windows x64, com recompilação estática
PowerPC → C++ usando ReXGlue. **Ainda não é um port jogável.** Consulte STATUS.md
antes de interpretar qualquer build ou teste como execução do jogo.

Um protótipo nativo já foi compilado em `build/game/HappyWars.exe`. O usuário
confirmou intro e tela de título em 3D; o avanço ainda depende da substituição
das verificações de perfil e dos serviços online por implementações locais.
O build usa `-O1`; ainda não há medição de FPS. Não usa JIT de PowerPC:
o código PowerPC foi convertido antes do build.

O pacote original do usuário foi localizado em Downloads, identificado como
LIVE pelo cabeçalho e extraído em `private/game/`. Não é necessário baixar o jogo.
Todos os recursos proprietários, imagens de memória e código traduzido permanecem
locais. Não publique `private/`, `generated/default/`, saves ou binários do jogo.

## Executar as ferramentas neste computador

Abra PowerShell na pasta deste README. Python 3.14 está instalado.
`config/local-tools.json` aponta para as dependências já preparadas no computador.

```powershell
py scripts/extract.py "C:\caminho\para\seu\pacote-LIVE"
py scripts/analyze.py
py scripts/resources.py
py scripts/data_audit.py
py -m unittest discover -s tests -p test_tools.py -v
py scripts/build.py
```

`build.py` compila e testa somente o backend de armazenamento por padrão. O teste
é um programa de verificação sem menu, combate ou simulação do Happy Wars.

Para gerar o código do jogo e tentar seu build:

```powershell
py scripts/recompile.py
py scripts/audit_labels.py
py scripts/audit_codegen.py
py scripts/prepare_blr_callbacks.py
py scripts/build.py --game --opt-level 1 --jobs 2
```

Depois da geração, os testes das rotinas traduzidas podem ser preparados e
executados separadamente:

```powershell
py scripts/prepare_translation_test.py
py scripts/prepare_thunk_test.py
py scripts/prepare_indexed_dispatch_test.py
py scripts/build.py --translation-test
```

Não execute dois geradores sobre a mesma pasta de saída. O gerador normal não usa
`--force`. Verifique o resultado e os erros antes de compilar ou executar.
Depois de alterar o próprio gerador, use `py scripts/recompile.py --regenerate`:
isso invalida o cache e continua exigindo que a validação passe.

O build também prepara automaticamente a lista de callbacks originais que
consistem exatamente em uma instrução `blr`. A lista é derivada da imagem local,
e o opcode é conferido novamente no boot. Essa tradução estática preserva os
registradores; não substitui funções ausentes por retornos de sucesso.

O CLI oficial criou `happywars_manifest.toml`, `src/main.cpp`,
`src/happywars_app.h` e `generated/rexglue.cmake`. O alvo real de jogo terá o nome
`HappyWars.exe` quando houver tradução e link bem-sucedidos.

## Preparação em outro ambiente Windows

São necessários Python, Git, LLVM/Clang e headers/bibliotecas MSVC/Windows SDK.
O compilador deve usar a ABI MSVC para vincular ao SDK oficial; a ABI GNU padrão
do LLVM-MinGW não é compatível com as interfaces C++ desse pacote.

```powershell
py scripts/install_msvc.py --accept-license
py scripts/setup.py --llvm-bin "C:\caminho\llvm\bin" --msvc tools/msvc --diagnostic-source
py scripts/build_diagnostic.py
py scripts/build.py
```

O instalador MSVC usa downloads oficiais da Microsoft por meio do projeto
msvc-wine, mantidos locais. O SDK ReXGlue é fixado por versão e SHA-256 em
`config/upstream-lock.json`; CMake e Ninja também têm versões fixadas.
O LLVM utilizado nesta execução foi Clang 23.1.3 de uma instalação LLVM-MinGW
já disponível. A instalação de uma nova distribuição LLVM não é automatizada.

## Conteúdo

- `scripts/`: extração validada, leitura XEX/PE, ZRES, auditoria e builds.
- `runtime/`, `include/`: backend SQLite C++ com transações e backup.
- `src/`: aplicação real criada pelo SDK; sem interfaces fictícias.
- `patches/`: alterações isoladas nas ferramentas, com testes e justificativas.
- `docs/`: evidências técnicas, pesquisa das ferramentas e plano offline.
- `logs/`: resultados reais; incluem falhas e suas correções.
- `private/`: arquivos originais e derivados locais; fora do Git.

O backend de save armazena bytes completos e versões de codec. **O codec e os
hooks do inventário original ainda precisam ser implementados e testados no
jogo.** Os testes do backend não demonstram persistência de equipamentos no jogo.

As chamadas de socket e partes de XHTTP têm guards locais para o teste offline:
retornam erro, não sucesso fictício. Esses guards não implementam perfil,
inventário, recompensas ou inicialização de partidas. O teste limitado de boot é
`py scripts/runtime_smoke.py --seconds 20`; os resultados ficam em logs/.
