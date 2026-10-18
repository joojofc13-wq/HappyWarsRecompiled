"""Extract the owned TU46 CRT routines for native fast-path comparison tests."""
from pathlib import Path
from prepare_translation_test import extract_function, ROOT


def prepare():
    bodies = [extract_function('DEFINE_REX_FUNC(sub_'+address+') {')[1]
              for address in ('83998350', '83999390')]
    output = ROOT/'private/tests/native_memory_original.cpp'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text('#include "generated/default/happywars_pch.h"\n'+'\n'.join(bodies)+'\n')
    print('Prepared original CRT comparison routines from the owned executable')


if __name__ == '__main__':
    prepare()
