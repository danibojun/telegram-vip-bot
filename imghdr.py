# Copiado de https://github.com/python/cpython/blob/3.12/Lib/imghdr.py
# Módulo removido no Python 3.13, necessário para compatibilidade

def what(file, h=None):
    """Determine the type of an image file."""
    if h is None:
        if isinstance(file, str):
            f = open(file, 'rb')
            h = f.read(32)
            f.close()
        else:
            pos = file.tell()
            h = file.read(32)
            file.seek(pos)
    for tf in tests:
        res = tf(h, file)
        if res:
            return res
    return None

def test_jpeg(h, f):
    if h[6:10] in (b'JFIF', b'Exif'):
        return 'jpeg'

def test_png(h, f):
    if h[:8] == b'\211PNG\r\n\032\n':
        return 'png'

def test_gif(h, f):
    if h[:6] in (b'GIF87a', b'GIF89a'):
        return 'gif'

def test_tiff(h, f):
    if h[:2] in (b'MM', b'II'):
        return 'tiff'

def test_rgb(h, f):
    if h[:2] == b'\001d':
        return 'rgb'

def test_pbm(h, f):
    if h[:2] == b'P4':
        return 'pbm'

def test_pgm(h, f):
    if h[:2] == b'P5':
        return 'pgm'

def test_ppm(h, f):
    if h[:2] == b'P6':
        return 'ppm'

def test_rast(h, f):
    if h[:4] == b'\x59\xA6\x6A\x95':
        return 'rast'

def test_xbm(h, f):
    if h[:6] == b'#define':
        return 'xbm'

def test_bmp(h, f):
    if h[:2] == b'BM':
        return 'bmp'

def test_webp(h, f):
    if h[:4] == b'RIFF' and h[8:12] == b'WEBP':
        return 'webp'

def test_exr(h, f):
    if h[:4] == b'\x76\x2f\x31\x01':
        return 'exr'

tests = [
    test_jpeg,
    test_png,
    test_gif,
    test_tiff,
    test_rgb,
    test_pbm,
    test_pgm,
    test_ppm,
    test_rast,
    test_xbm,
    test_bmp,
    test_webp,
    test_exr,
] 