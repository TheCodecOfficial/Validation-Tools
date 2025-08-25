def color_range(start, end, n, use_oklab=False):
    """
    Generate n colors linearly interpolated between start and end.

    Args:
        start (tuple): RGB (or RGBA) tuple for the start color.
        end (tuple): RGB (or RGBA) tuple for the end color.
        n (int): Number of colors to generate.
        use_oklab (bool): Whether to interpolate in Oklab color space.

    Yields:
        tuple: Interpolated color.
    """
    if use_oklab:
        start = rgb_to_oklab(start)
        end = rgb_to_oklab(end)
        for i in range(n):
            t = i / (n - 1) if n > 1 else 0
            yield oklab_to_rgb(
                tuple(start[j] * (1 - t) + end[j] * t for j in range(len(start)))
            )
    else:
        for i in range(n):
            t = i / (n - 1) if n > 1 else 0
            yield tuple(start[j] * (1 - t) + end[j] * t for j in range(len(start)))


def rgb_to_oklab(rgb):
    r, g, b = rgb

    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b

    l_ = l ** (1 / 3)
    m_ = m ** (1 / 3)
    s_ = s ** (1 / 3)

    L = 0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_
    a = 1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_
    b = 0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_
    return (L, a, b)


def oklab_to_rgb(Lab):
    L, a, b = Lab

    l_ = L + 0.3963377774 * a + 0.2158037573 * b
    m_ = L - 0.1055613458 * a - 0.0638541728 * b
    s_ = L - 0.0894841775 * a - 1.2914855480 * b

    l = l_**3
    m = m_**3
    s = s_**3

    r = +4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
    g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
    b = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s

    r = max(0, min(1, r))
    g = max(0, min(1, g))
    b = max(0, min(1, b))

    return (r, g, b)


def color_to_str(color):
    return f"({color[0]:.2f}, {color[1]:.2f}, {color[2]:.2f})"
