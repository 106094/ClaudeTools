"""Run this once to generate extension icons: python make_icons.py"""
import struct, zlib, math, os

def make_png(size, bg, fg):
    pixels = []
    cx = cy = size // 2
    r_out = size // 2 - 1
    r_in  = size // 2 - max(2, size // 6)

    for y in range(size):
        row = []
        for x in range(size):
            dx, dy   = x - cx, y - cy
            dist     = math.sqrt(dx*dx + dy*dy)
            angle    = math.degrees(math.atan2(dy, dx))
            in_ring  = r_in <= dist <= r_out
            in_gap   = -38 <= angle <= 38
            if in_ring and not in_gap:
                row += list(fg) + [255]
            else:
                row += list(bg) + [0]
        pixels.append(row)

    def chunk(name, data):
        c = name + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)

    raw        = b''.join(b'\x00' + bytes(r) for r in pixels)
    compressed = zlib.compress(raw, 9)
    ihdr       = struct.pack('>IIBBBBB', size, size, 8, 6, 0, 0, 0)
    return (b'\x89PNG\r\n\x1a\n'
            + chunk(b'IHDR', ihdr)
            + chunk(b'IDAT', compressed)
            + chunk(b'IEND', b''))

bg = (30, 30, 46)      # #1e1e2e dark background
fg = (137, 180, 250)   # #89b4fa accent blue

here = os.path.dirname(os.path.abspath(__file__))
for size in [16, 48, 128]:
    path = os.path.join(here, f"icon{size}.png")
    with open(path, "wb") as f:
        f.write(make_png(size, bg, fg))
    print(f"Created {path}")
