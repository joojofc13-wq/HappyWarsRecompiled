import subprocess,sys
indexed=subprocess.check_output([sys.argv[1]])
reference=subprocess.check_output([sys.argv[2]])
if indexed!=reference:
    raise SystemExit(f'Behavior mismatch: indexed={indexed!r}, reference={reference!r}')
print('PASS 20,000 operations; indexed and original notifications have identical state digests')
