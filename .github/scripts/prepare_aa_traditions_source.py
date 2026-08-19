from __future__ import annotations

from pathlib import Path
import base64, bz2, hashlib, io, shutil, subprocess, tarfile

STAGE = Path('.webbook-upload/aa-traditions-detailed')
EXPECTED = 'f924aacf39ebf5b78002a4a24921997483b93d3227cc0ea43606bd99a74c2b5a'
PARTS = [f'part-{i:02d}.b64' for i in range(9)]
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

def md_digest_from_encoded(chunks: list[str], label: str) -> bool:
    joined = ''.join(''.join(c.split()) for c in chunks)
    print(f'{label}: chars={len(joined)} mod4={len(joined)%4}')
    try:
        raw = base64.b64decode(joined, validate=True)
        tar_bytes = bz2.decompress(raw)
    except Exception as exc:
        print(f'{label}: decode/decompress rejected: {exc}')
        return False
    work = Path('/tmp/aa-source-probe')
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    try:
        with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode='r:') as tf:
            tf.extractall(work, filter='data')
    except Exception as exc:
        print(f'{label}: tar rejected: {exc}')
        return False
    files = sorted(work.rglob('*.md'), key=lambda p: p.name.encode('utf-8'))
    if len(files) != 75:
        print(f'{label}: md count={len(files)}')
        return False
    payload = b''.join(hashlib.sha256(p.read_bytes()).hexdigest().encode()+b'\n' for p in files)
    got = hashlib.sha256(payload).hexdigest()
    print(f'{label}: md digest={got}')
    return got == EXPECTED

def save_standard(chunks: list[str]) -> None:
    if len(chunks) != 9:
        raise SystemExit('validated source did not have nine standard chunks')
    for name, data in zip(PARTS, chunks):
        (STAGE/name).write_text(data, encoding='ascii')

# First try every historical repository snapshot as an internally consistent nine-part archive.
for commit in COMMITS:
    chunks = [show(commit, name) for name in PARTS]
    if all(x is not None for x in chunks) and md_digest_from_encoded(chunks, f'snapshot {commit}'):
        print(f'VALIDATED SNAPSHOT: {commit}')
        save_standard(chunks)
        raise SystemExit(0)

# Then try the later staged replacement files in plausible ordered combinations.
# A match is accepted only if it reconstructs the exact current 75-MD digest.
prefix_names = ['part-00.b64','part-01.b64','part-02.b64','part-03.b64']
for commit in COMMITS:
    prefix = [show(commit,n) for n in prefix_names]
    if not all(x is not None for x in prefix):
        continue
    variants4 = ['part-04.b64','part-04-new.b64']
    variants5 = ['part-05.b64','part-05-new.b64']
    tails = [
        ['part-06.b64','part-07.b64','part-08.b64'],
        ['part-06-new.b64','part-07.b64','part-08.b64'],
    ]
    for n4 in variants4:
        for n5 in variants5:
            for tail in tails:
                names = prefix_names + [n4,n5] + tail
                chunks = [show(commit,n) for n in names]
                if not all(x is not None for x in chunks):
                    continue
                label = f'variant {commit} ' + ','.join(names[4:])
                if md_digest_from_encoded(chunks,label):
                    print(f'VALIDATED VARIANT: {label}')
                    save_standard(chunks)
                    raise SystemExit(0)

raise SystemExit('No historical source snapshot/variant matches the current uploaded 75-MD digest.')
