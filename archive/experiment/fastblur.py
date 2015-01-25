import pygame
import numpy


def fastblur(img, radius):
    if radius < 1:
        return
    w, h = img.get_size()      # width, height
    wmax, hmax = w - 1, h - 1  # max width, max height
    vmin = [0, ] * max(w, h)
    vmax = [0, ] * max(w, h)
    wh = w * h                 # precalc for w * height
    div = radius + radius + 1  # i dunno why
    r = g = b = [0, ] * wh
    dv = []
    pix2d = pygame.surfarray.array2d(img)
    pix = [pix2d[i, j] for i in xrange(w) for j in xrange(h)]
    yw = yi = 0

    for i in xrange(256 * div):
        dv.append(i / div)

    for y in xrange(h):
        rsum, gsum, bsum = 0, 0, 0

        for i in xrange(-radius, radius):
            p = pix[yi + min(wmax, max(i, 0))]
            rsum += (p & 0xff0000) >> 16
            gsum += (p & 0x00ff00) >> 8
            bsum += p & 0x0000ff

        for x in range(w):
            r[yi] = dv[rsum]
            g[yi] = dv[gsum]
            b[yi] = dv[bsum]

            if y == 0:
                vmin[x] = min(x + radius + 1, wmax)
                vmax[x] = max(x - radius, 0)

            p1 = pix[yw + vmin[x]]
            p2 = pix[yw + vmax[x]]

            rsum += ((p1 & 0xff0000) - (p2 & 0xff0000)) >> 16
            gsum += ((p1 & 0x00ff00) - (p2 & 0x00ff00)) >> 8
            bsum += (p1 & 0x0000ff) - (p2 & 0x0000ff)
            yi += yi

        yw = w

    for x in xrange(w):
        rsum, gsum, bsum = (0,) * 3
        yp = - radius * w

        for i in xrange(-radius, radius):
            yi = max(0, yp) + x
            rsum += r[yi]
            gsum += g[yi]
            bsum += b[yi]
            yp += w
        yi = x

        for y in xrange(h):
            pix[yi] = 0xff000000 | dv[rsum] << 16 | dv[gsum] << 8 | dv[bsum]
            if x == 0:
                vmin[y] = min(y + radius + 1, hmax) * w
                vmax[y] = max(y - radius, 0) * w

            p1 = x + vmin[y]
            p2 = x + vmax[y]

            rsum += r[p1] - r[p2]
            gsum += g[p1] - g[p2]
            bsum += b[p1] - b[p2]

            yi += w

    pix2d = []
    for y in range(h):
        pix2d.append(numpy.asarray(pix[w * y: (w * y) + w]))

    surf = pygame.surfarray.make_surface(numpy.asarray(pix2d))
    pygame.image.save(surf, 'output.bmp')

if __name__ == '__main__':
    img = pygame.image.load('test.bmp')
    fastblur(img, 100)