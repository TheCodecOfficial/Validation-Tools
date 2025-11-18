import numpy as np
import OpenEXR
import Imath

def read_exr(file_path):
    exr_file = OpenEXR.InputFile(file_path)
    header = exr_file.header()
    dw = header["dataWindow"]
    size = (dw.max.x - dw.min.x + 1, dw.max.y - dw.min.y + 1)

    FLOAT = Imath.PixelType(Imath.PixelType.FLOAT)
    rgb = [
        np.frombuffer(exr_file.channel(c, FLOAT), dtype=np.float32)
        for c in ("R", "G", "B")
    ]
    rgb = np.dstack(rgb)[0]
    rgb = np.reshape(rgb, (size[1], size[0], 3))
    return rgb


def write_exr(file_path, data):
    if data.dtype != np.float32:
        data = data.astype(np.float32)

    height, width, channels = data.shape
    assert channels == 3, "Data must have 3 channels (RGB)."

    header = OpenEXR.Header(width, height)
    half_chan = Imath.Channel(Imath.PixelType(Imath.PixelType.FLOAT))
    header["channels"] = {"R": half_chan, "G": half_chan, "B": half_chan}

    exr = OpenEXR.OutputFile(file_path, header)

    # Split into channels and write
    r = data[:, :, 0].tobytes()
    g = data[:, :, 1].tobytes()
    b = data[:, :, 2].tobytes()
    exr.writePixels({"R": r, "G": g, "B": b})
    exr.close()
