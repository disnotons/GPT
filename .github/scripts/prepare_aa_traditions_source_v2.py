from __future__ import annotations

from pathlib import Path
import base64, bz2, hashlib, io, shutil, subprocess, tarfile

STAGE = Path('.webbook-upload/aa-traditions-detailed')
EXPECTED = 'f924aacf39ebf5b78002a4a24921997483b93d3227cc0ea43606bd99a74c2b5a'
STD = [f'part-{i:02d}.b64' for i in range(9)]
COMMITS = [
    '2c0b79e866b54f9a52fe963cf7e071fa3062e3fb',
    'dffbf60374bc1efaf0ef3eedcacecfe26cf063c0',
    '464c41bfb2679058ada9dfbd0b282419fdae79e2',
    'eef281586654bf2353a85d0db205754418f91ae2',
    '86d54385b82b690bd939febef0d1e8dbece080c2',
    '2bfae17d0e4dc0b0d8412704386e4d4777663531',
    'e449ae06458f251958af21ee08126702e291ed78',
    'd64e9b5311e5b6f6afa0e24d8aa238afca8d01ef',
    'd3d38793cb31cb97bc064b6627ab9ee91be453fd',
    'bf8b9ab8fb5d1aa94a4b777350390bfcb7689bf7',
    '43c4de1930648f9b4510ecf9275717b1b6b8ec4f',
    'e368f212266413f4a74a5dbea51a848fd5fda8fd',
    'HEAD',
]

def show(commit: str, name: str) -> str | None:
    path = f'{STAGE.as_posix()}/{name}'
    try:
        return subprocess.check_output(['git','show',f'{commit}:{path}'], text=True, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return None

def clean(s: str) -> str:
    return ''.join(s.split())

def extract_and_check(raw: bytes, label: str) -> Path | None:
    try:
        data = bz2.decompress(raw)
    except Exception as exc:
        print(f'{label}: bzip2 rejected: {exc}')
        return None
    out = Path('/tmp/aa-v2-probe')
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)
    try:
        with tarfile.open(fileobj=io.BytesIO(data), mode='r:') as tf:
            tf.extractall(out, filter='data')
    except Exception as exc:
        print(f'{label}: tar rejected: {exc}')
        return None
    files = sorted(out.rglob('*.md'), key=lambda p:p.name.encode('utf-8'))
    print(f'{label}: md count={len(files)}')
    if len(files) != 75:
        return None
    payload = b''.join(hashlib.sha256(p.read_bytes()).hexdigest().encode()+b'\n' for p in files)
    got = hashlib.sha256(payload).hexdigest()
    print(f'{label}: digest={got}')
    if got != EXPECTED:
        return None
    return out

def try_chunks(chunks: list[str], label: str) -> Path | None:
    # Mode 1: chunks are slices of one Base64 stream.
    try:
        raw = base64.b64decode(''.join(clean(c) for c in chunks), validate=True)
        out = extract_and_check(raw, label+' / concatenated-base64')
        if out:
            return out
    except Exception as exc:
        print(f'{label} / concatenated-base64 rejected: {exc}')

    # Mode 2: each chunk was Base64-encoded independently; decode each first.
    try:
        decoded=[]
        for i,c in enumerate(chunks):
            t=clean(c)
            decoded.append(base64.b64decode(t, validate=True))
        raw=b''.join(decoded)
        out=extract_and_check(raw,label+' / per-part-base64')
        if out:
            return out
    except Exception as exc:
        print(f'{label} / per-part-base64 rejected: {exc}')
    return None

def canonicalize(source: Path) -> None:
    buf=io.BytesIO()
    with tarfile.open(fileobj=buf, mode='w:bz2') as tf:
        for p in sorted(source.rglob('*'), key=lambda p:str(p.relative_to(source)).encode('utf-8')):
            tf.add(p, arcname=str(p.relative_to(source)))
    encoded=base64.b64encode(buf.getvalue()).decode('ascii')
    # Builder expects nine textual slices of one Base64 stream.
    q,r=divmod(len(encoded),9)
    sizes=[q+(1 if i<r else 0) for i in range(9)]
    pos=0
    for name,size in zip(STD,sizes):
        (STAGE/name).write_text(encoded[pos:pos+size],encoding='ascii')
        pos+=size
    print(f'Canonicalized validated source into 9 slices, total chars={len(encoded)}')

# Try internally consistent standard-part snapshots.
for commit in COMMITS:
    chunks=[show(commit,n) for n in STD]
    if all(x is not None for x in chunks):
        out=try_chunks(chunks,f'snapshot {commit}')
        if out:
            print(f'VALIDATED SNAPSHOT: {commit}')
            canonicalize(out)
            raise SystemExit(0)

# Try later replacement files 04-new/05-new/06-new where present.
for commit in COMMITS:
    prefix=[show(commit,n) for n in STD[:4]]
    if not all(x is not None for x in prefix):
        continue
    for n4 in ['part-04.b64','part-04-new.b64']:
        for n5 in ['part-05.b64','part-05-new.b64']:
            for n6 in ['part-06.b64','part-06-new.b64']:
                names=STD[:4]+[n4,n5,n6,'part-07.b64','part-08.b64']
                chunks=[show(commit,n) for n in names]
                if not all(x is not None for x in chunks):
                    continue
                out=try_chunks(chunks,f'variant {commit} {n4},{n5},{n6}')
                if out:
                    print(f'VALIDATED VARIANT: {commit} {n4},{n5},{n6}')
                    canonicalize(out)
                    raise SystemExit(0)

raise SystemExit('No historical AA transfer reconstructs the current 75-MD source.')
