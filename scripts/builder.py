"""Small Windows builder for an owned, extracted Happy Wars TU46 copy."""
import hashlib
import json
import os
from pathlib import Path
import queue
import re
import shutil
import subprocess
import sys
import threading
import zipfile
from build import environment as build_environment

ROOT = Path(__file__).resolve().parents[1]
TU46_SHA = '14e0474a881bad5ef32bdf663651a8fb564bfd63fc23729aa50556739354e917'


def python_command():
    if not getattr(sys, 'frozen', False):
        return [sys.executable]
    launcher = shutil.which('py')
    if launcher:
        return [launcher, '-3']
    executable = shutil.which('python')
    if executable:
        return [executable]
    raise RuntimeError('Install Python 3.11 or newer from python.org, then reopen the builder.')


def validate_game(folder):
    folder = Path(folder).resolve()
    executable = folder/'Default.xex'
    if not executable.is_file() or not (folder/'media').is_dir():
        raise ValueError('Select an extracted game folder containing Default.xex and media.')
    with executable.open('rb') as source:
        digest = hashlib.file_digest(source, 'sha256').hexdigest()
    if digest != TU46_SHA:
        raise ValueError('This builder supports TU46 version 0.0.46.7, Media ID 5CEC066D. The selected executable does not match.')
    if any(p.is_symlink() for p in folder.rglob('*')):
        raise ValueError('Game input must not contain symbolic links.')
    return folder


def prepare_sources(destination):
    destination = Path(destination).resolve()
    if destination.exists() and any(destination.iterdir()):
        raise ValueError('Choose a new or empty build folder. Existing files will not be overwritten.')
    destination.mkdir(parents=True, exist_ok=True)
    bundle = Path(getattr(sys, '_MEIPASS', ROOT))/'source.zip'
    if bundle.exists():
        with zipfile.ZipFile(bundle) as archive:
            for entry in archive.infolist():
                target = (destination/entry.filename).resolve()
                if not target.is_relative_to(destination):
                    raise ValueError('Unsafe source archive path')
            archive.extractall(destination)
    else:
        names = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
        for name in filter(None, names):
            source = ROOT/name
            target = destination/name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    profile = destination/'ports/tu46'
    for name in ('CMakeLists.txt', 'happywars_manifest.toml', 'config/function-boundaries.toml',
                 'config/verified-thunks.toml', 'runtime/boot_diagnostics.cpp',
                 'runtime/local_service_directory.cpp', 'runtime/local_stats.cpp'):
        shutil.copy2(profile/name, destination/name)
    (destination/'logs').mkdir(exist_ok=True)
    return destination


def compile_game(game, destination, llvm='', msvc='', font='', accept_license=False, emit=print, local_settings=None, progress=None):
    def advance(percent, stage):
        if progress: progress(percent, stage)
    advance(0, "Validating game files")
    game = validate_game(game)
    if getattr(sys,'frozen',False) and sys.platform=='win32':
        import ctypes
        ctypes.windll.kernel32.SetDllDirectoryW(None)
    if font and not Path(font).is_file():
        raise ValueError('The optional FPS font file does not exist.')
    destination = Path(destination).resolve()
    if destination == game or destination.is_relative_to(game) or game.is_relative_to(destination):
        raise ValueError('Build folder and original game folder must be separate.')
    automatic = not local_settings and not llvm
    if automatic and not accept_license:
        raise ValueError('Accept the Microsoft build-tools license to download the required headers and SDK.')
    advance(1, 'Preparing project sources')
    emit('Preparing project sources')
    port = prepare_sources(destination)
    flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
    if automatic:
        from bootstrap_tools import bootstrap
        advance(2, 'Downloading portable tools')
        tools = bootstrap(port, emit)
        python = tools['python']; llvm = tools['llvm']
    else:
        python = python_command()
        if not shutil.which('git'):
            raise RuntimeError('Git is missing from the manual toolchain.')
    check = subprocess.run(python+['-c', 'import sys; assert sys.version_info >= (3,11)'],
                           capture_output=True, creationflags=flags)
    if check.returncode:
        raise RuntimeError('The build Python runtime could not start.')
    advance(10, 'Copying game files')
    emit('Copying your game files; the original folder is unchanged')
    shutil.copytree(game, port/'private/game')
    log_path = port/'logs/builder.log'
    def run(arguments, native_progress=False):
        emit('Running '+str(arguments[0]))
        command = python+['-u',str(port/arguments[0])]+[str(x) for x in arguments[1:]]
        environment = os.environ.copy()
        environment['PYTHONPATH'] = str(port/'tools/python')
        with log_path.open('a', encoding='utf-8') as log:
            process = subprocess.Popen(command, cwd=port, env=environment, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, text=True, errors='replace', creationflags=flags)
            recent = []
            for line in process.stdout:
                log.write(line); log.flush()
                recent = (recent+[line.rstrip()])[-12:]
                if native_progress:
                    counts = re.match(r'^\[(\d+)/(\d+)\]', line)
                    if counts and 0 < int(counts[1]) <= int(counts[2]):
                        advance(60 + 38 * int(counts[1]) / int(counts[2]),
                                'Compiling game: '+counts[1]+'/'+counts[2])
                if line.strip(): emit(line.rstrip())
            if process.wait():
                raise RuntimeError('Build step failed. See '+str(log_path)+'\n'+'\n'.join(recent))
    advance(15, 'Preparing Microsoft SDK and dependencies')
    if local_settings:
        (port/'config/local-tools.json').write_text(json.dumps(local_settings, indent=2), encoding='utf-8')
        fonttools = json.loads((port/'config/upstream-lock.json').read_text())['python_packages']['fonttools']
        subprocess.run(python+['-m','pip','install','--target',str(port/'tools/python'),'fonttools=='+fonttools],
                       cwd=port,check=True,creationflags=flags)
    else:
        if not msvc:
            emit('Downloading Microsoft headers and Windows SDK')
            run(['scripts/install_msvc.py', '--accept-license'])
            msvc = port/'tools/msvc'
        runtime_folder=next((Path(msvc)/'VC/Redist/MSVC').glob('*/x64/Microsoft.VC143.CRT'),None)
        if runtime_folder:
            os.environ['PATH']=str(runtime_folder)+os.pathsep+os.environ.get('PATH','')
        advance(25, 'Preparing recompiler sources')
        run(['scripts/setup.py', '--llvm-bin', llvm, '--msvc', msvc, '--diagnostic-source'])
        advance(30, 'Building recompiler tools')
        run(['scripts/build_diagnostic.py', '--jobs', '4'])
    settings_path = port/'config/local-tools.json'
    settings = json.loads(settings_path.read_text())
    if font:
        settings['fps_font_source'] = str(Path(font).resolve())
        settings_path.write_text(json.dumps(settings, indent=2), encoding='utf-8')
    advance(40, 'Analyzing game executable')
    run(['scripts/analyze.py'])
    # The mapped image is required by callback verification during native build.
    advance(45, 'Mapping game image')
    environment = build_environment(settings)
    tool_build = port/'build/title-update-tool'
    cmake = settings['cmake']
    commands = [[cmake, '-S', str(port/'tools/title-update'), '-B', str(tool_build), '-G', 'Ninja',
        '-DCMAKE_BUILD_TYPE=Release', '-DCMAKE_CXX_COMPILER='+settings['clang'],
        '-DCMAKE_CXX_FLAGS=--target=x86_64-pc-windows-msvc -fms-runtime-lib=dll',
        '-DCMAKE_MAKE_PROGRAM='+settings['ninja'], '-DCMAKE_PREFIX_PATH='+settings['sdk']],
        [cmake, '--build', str(tool_build), '--parallel', '2']]
    with log_path.open('a', encoding='utf-8') as log:
        for command in commands:
            subprocess.run(command, cwd=port, env=environment, stdout=log, stderr=log,
                           check=True, creationflags=flags)
        empty_update = port/'private/empty-update'; empty_update.mkdir()
        probe = tool_build/'title_update_probe.exe'
        shutil.copy2(Path(settings['sdk'])/'bin/rexruntime.dll', tool_build/'rexruntime.dll')
        output = port/'private/probe'
        subprocess.run([str(probe), str(port/'private/game'), str(empty_update),
            str(port/'private/probe-user'), str(output), '--base-image'], cwd=port,
            env=environment, stdout=log, stderr=log, check=True, creationflags=flags)
    shutil.copy2(output/'loaded-image.bin', port/'private/loaded-image.bin')
    advance(50, 'Generating native game code')
    run(['scripts/recompile.py'])
    advance(60, 'Configuring native game build')
    run(['scripts/build.py', '--game', '--opt-level', '1', '--jobs', '4'], native_progress=True)
    advance(99, 'Staging runtime files')
    runtime_folder=next((Path(settings['msvc'])/'VC/Redist/MSVC').glob('*/x64/Microsoft.VC143.CRT'),None)
    if runtime_folder:
        for library in runtime_folder.glob('*.dll'):
            shutil.copy2(library,port/'build/game'/library.name)
    for name in ('ResetSaves.cmd', 'scripts/reset_saves.ps1'):
        shutil.copy2(port/name, port/'build/game'/Path(name).name)
    advance(100, 'Build complete')
    emit('Build complete: '+str(port/'build/game/HappyWars.exe'))
    return port/'build/game/HappyWars.exe'


def main():
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    window = tk.Tk(); window.title('Happy Wars Recompiled Builder')
    self_test = '--self-test-report' in sys.argv
    if self_test: window.withdraw()
    style = ttk.Style(window)
    if 'vista' in style.theme_names(): style.theme_use('vista')
    frame = ttk.Frame(window, padding=12); frame.grid(sticky='nsew')
    window.columnconfigure(0, weight=1); frame.columnconfigure(1, weight=1)
    fields = {}
    labels = [('game', 'Game folder'), ('destination', 'Output folder')]
    for row,(key,label) in enumerate(labels):
        ttk.Label(frame,text=label).grid(row=row,column=0,sticky='w',padx=(0,8),pady=4)
        value=tk.StringVar(); fields[key]=value
        ttk.Entry(frame,textvariable=value,width=48).grid(row=row,column=1,sticky='ew')
        def browse(key=key):
            selected = filedialog.askopenfilename(parent=window, filetypes=[('Game font','*.bres')]) if key=='font' else filedialog.askdirectory(parent=window)
            if selected: fields[key].set(selected)
        ttk.Button(frame,text='Browse...',command=browse).grid(row=row,column=2,padx=(8,0))
    consent=tk.BooleanVar(value=False)
    ttk.Checkbutton(frame,text='Accept Microsoft build-tools license',
        variable=consent).grid(row=2,columnspan=2,sticky='w',pady=8)
    def license_terms():
        import webbrowser
        webbrowser.open('https://go.microsoft.com/fwlink/?LinkId=2179911')
    ttk.Button(frame,text='License',command=license_terms).grid(row=2,column=2,padx=(8,0))
    ttk.Label(frame,text='TU46 0.0.46.7 only. Build tools are downloaded automatically.\nGame content is never downloaded. Gameplay remains experimental.',
        justify='left').grid(row=3,columnspan=3,sticky='w')
    status=tk.StringVar(value='Select your game and an empty build folder.')
    ttk.Label(frame,textvariable=status,wraplength=600).grid(row=4,columnspan=3,sticky='w',pady=10)
    percentage=tk.DoubleVar(value=0)
    progress_text=tk.StringVar(value='0%')
    stage_text=tk.StringVar(value='Overall progress (estimated)')
    bar=ttk.Progressbar(frame,maximum=100,variable=percentage,mode='determinate')
    bar.grid(row=5,column=0,columnspan=2,sticky='ew',pady=(0,6))
    ttk.Label(frame,textvariable=progress_text).grid(row=5,column=2)
    ttk.Label(frame,textvariable=stage_text).grid(row=6,columnspan=3,sticky='w',pady=(0,10))
    events=queue.Queue(); result={'path':None,'busy':False}
    def worker(values,accepted):
        try:
            path=compile_game(**values,accept_license=accepted,emit=lambda s:events.put(('status',s)),
                progress=lambda n,s:events.put(('progress',(n,s))))
            events.put(('done',path))
        except Exception as error: events.put(('error',str(error)))
    def build():
        if result['busy']: return
        result['busy']=True; button.state(['disabled'])
        percentage.set(0); progress_text.set('0%'); open_button.state(['disabled'])
        threading.Thread(target=worker,args=({k:v.get() for k,v in fields.items()},consent.get()),daemon=True).start()
    def poll():
        try:
            while True:
                kind,value=events.get_nowait()
                if kind=='status': status.set(value[-260:])
                elif kind=='progress':
                    percentage.set(max(percentage.get(),value[0]))
                    progress_text.set(str(int(percentage.get()))+'%')
                    stage_text.set(value[1])
                else:
                    result['busy']=False; button.state(['!disabled'])
                    if kind=='error':
                        status.set('Build failed. See the log in the build folder.')
                        messagebox.showerror('Build failed',str(value),parent=window)
                    else:
                        result['path']=value; status.set('Complete. Open the folder and run HappyWars.exe.')
                        open_button.state(['!disabled'])
        except queue.Empty: pass
        window.after(100,poll)
    def close():
        if result['busy']:
            messagebox.showinfo('Build running','Wait for the build to finish before closing.',parent=window)
        else: window.destroy()
    button=ttk.Button(frame,text='Build',command=build); button.grid(row=7,column=2,sticky='e')
    open_button=ttk.Button(frame,text='Open game folder',command=lambda:os.startfile(result['path'].parent))
    open_button.grid(row=7,column=0,columnspan=2,sticky='w'); open_button.state(['disabled'])
    window.protocol('WM_DELETE_WINDOW',close); window.after(100,poll)
    window.resizable(True,False)
    if self_test:
        window.update_idletasks()
        report = {'title':window.title(),'theme':style.theme_use(),
            'width':window.winfo_reqwidth(),'height':window.winfo_reqheight(),'inputs':list(fields),
            'progress_maximum':float(bar['maximum']),'progress_mode':str(bar['mode']),
            'bundled_sources':(Path(getattr(sys,'_MEIPASS',ROOT))/'source.zip').is_file()}
        output=Path(sys.argv[sys.argv.index('--self-test-report')+1])
        output.write_text(json.dumps(report,indent=2),encoding='utf-8')
        window.destroy()
    else: window.mainloop()

if __name__=='__main__':
    main()
