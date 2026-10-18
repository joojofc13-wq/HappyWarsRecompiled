import pathlib
import subprocess
import sys
import tempfile
import sqlite3
with tempfile.TemporaryDirectory(prefix='happywars-save-test-') as folder:
    database=pathlib.Path(folder)/'profile.sqlite'
    for phase in ('write','crash','read','restore'):
        subprocess.run([sys.argv[1],phase,str(database)],check=True)
    corrupt=pathlib.Path(folder)/'corrupt.sqlite'
    corrupt.write_bytes(b'This is a corrupt save fixture, not game data.'*100)
    subprocess.run([sys.argv[1],'corrupt',str(corrupt)],check=True)
    future=pathlib.Path(folder)/'future.sqlite'
    with sqlite3.connect(future) as connection:
        connection.execute('PRAGMA user_version=999')
    connection.close()
    subprocess.run([sys.argv[1],'future',str(future)],check=True)
