import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import sys

integrator_map = {
    "path_mis": "path",
    "path_mats": "path",
    "direct_mis": "direct",
    "direct_mats": "direct",
    "direct_ems": "direct",
}

tag_map = {
    "mesh": "shape",
    "color": "rgb",
}

# This is suboptimal, but it's by far the easiest way to map the tags
# Ideally, it should be context-aware
attrib_map = {
    "type": {
        # BSDFs
        "disney": "principled",
        "transparent": "null",
        "blended": "blendbsdf",
        "mirror": "conductor",
        # Textures
        "image_color": "bitmap",
        "image_float": "bitmap",
    },
    "name": {
        # Diffuse BRDF
        "albedo": "reflectance",
        # Disney BRDF
        "specularTint": "spec_tint",
        "sheenTint": "sheen_tint",
        "clearcoatGloss": "clearcoat_gloss",
        "subsurface": "flatness",
        # Texture Modes
        "interpolation": "filter_type",
        "extension": "wrap_mode",
        # Emitters
        "power": "intensity",
    },
}


def get_scene_info(root):
    """Get the general scene information such as integrator, sampler, camera, etc."""
    # Integrator
    integrator = root.find("integrator").attrib["type"]

    # Sampler
    sampler_tag = root.find("sampler")
    sampler = sampler_tag.attrib["type"]
    sample_count = sampler_tag.find("integer").attrib["value"]

    # Camera
    camera_tag = root.find("camera")
    cam_fov = camera_tag.find("float").attrib["value"]
    cam_int_tags = camera_tag.findall("integer")
    for tag in cam_int_tags:
        if tag.attrib["name"] == "width":
            cam_width = tag.attrib["value"]
        elif tag.attrib["name"] == "height":
            cam_height = tag.attrib["value"]
    rfilter_tag = camera_tag.find("rfilter")
    cam_rfilter = rfilter_tag.attrib["type"] if rfilter_tag is not None else None
    transform_tag = camera_tag.find("transform")
    cam_transform = {t.tag: t.attrib for t in transform_tag}

    scene = {
        "integrator": integrator,
        "sampler": sampler,
        "sample_count": sample_count,
        "camera": {
            "fov": cam_fov,
            "resolution": (cam_width, cam_height),
            "rfilter": cam_rfilter,
            "transform": cam_transform,
        },
    }

    return scene


def lookup(word, dict):
    return dict.get(word, word)


def xml_tag(root, tag, **kwargs):
    element = ET.SubElement(root, tag)
    for key, value in kwargs.items():
        element.set(key, value)
    return element


def save_xml(root, filename):
    xml_string = minidom.parseString(ET.tostring(root)).toprettyxml(indent="\t")
    xml_string = "\n".join([line for line in xml_string.split("\n") if line.strip()])
    with open(filename, "w") as f:
        f.write(xml_string)


def translate_tags(root):
    """Recursively translate Nori tags like mesh, bsdf, etc. to Mitsuba tags."""

    for child in root:
        child.tag = lookup(child.tag, tag_map)
        for attrib in child.attrib:
            if attrib in attrib_map:
                child.set(attrib, lookup(child.attrib[attrib], attrib_map[attrib]))

        translate_tags(child)


def translate_scene(scene_file):
    """Convert a Nori scene file into a Mitsuba scene file."""
    nori_tree = ET.parse(scene_file)
    nori_root = nori_tree.getroot()

    scene_info = get_scene_info(nori_root)

    mitsuba_root = ET.Element("scene")
    mitsuba_root.set("version", "0.5.0")

    # Integrator
    integrator_tag = xml_tag(
        mitsuba_root,
        "integrator",
        type=lookup(scene_info["integrator"], integrator_map),
    )

    # Camera
    camera = scene_info["camera"]
    camera_tag = xml_tag(mitsuba_root, "sensor", type="perspective")
    fov_tag = xml_tag(camera_tag, "float", name="fov", value=camera["fov"])

    # Camera Transform
    transform = camera["transform"]
    transform_tag = xml_tag(camera_tag, "transform", name="to_world")
    scale_value = None
    if scale := transform.get("scale"):
        scale_value = [float(v) for v in scale["value"].split(",")]
        scale_value[0] *= -1
        transform.pop("scale")
    else:
        scale_value = [-1, 1, 1]

    scale_tag = xml_tag(
        transform_tag, "scale", value=",".join(str(v) for v in scale_value)
    )

    for key, value in transform.items():
        subtag = xml_tag(transform_tag, key)
        for k, v in value.items():
            subtag.set(k, v)

    # Film
    film_tag = xml_tag(camera_tag, "film", type="hdrfilm")
    width_tag = xml_tag(
        film_tag, "integer", name="width", value=camera["resolution"][0]
    )
    height_tag = xml_tag(
        film_tag, "integer", name="height", value=camera["resolution"][1]
    )
    if rfilter := camera["rfilter"]:
        rfilter_tag = xml_tag(film_tag, "rfilter", type=rfilter)

    # Sampler
    sampler_tag = xml_tag(camera_tag, "sampler", type=scene_info["sampler"])
    num_samples_tag = xml_tag(
        sampler_tag, "integer", name="sample_count", value=scene_info["sample_count"]
    )

    # Translate the rest of the tags (mesh, bsdf, etc.)
    remove_tags = ["integrator", "sampler", "camera"]

    for tag in remove_tags:
        tag_ = nori_root.find(tag)
        if tag_ is not None:
            nori_root.remove(tag_)

    translate_tags(nori_root)
    mitsuba_root.extend(nori_root)

    return mitsuba_root


def convert_scene(nori_file, mitsuba_file=None, verbose=True):
    if mitsuba_file is None:
        if "nori" in nori_file:
            mitsuba_file = nori_file.replace("nori", "mitsuba")
        else:
            mitsuba_file = nori_file.replace(".xml", "_mitsuba.xml")

    mitsuba_root = translate_scene(nori_file)
    save_xml(mitsuba_root, mitsuba_file)

    if verbose:
        print(f"Saved Mitsuba scene to {mitsuba_file}")


if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python nori_to_mitsuba.py <nori_file> [<mitsuba_file>]")
        sys.exit(1)

    convert_scene(*sys.argv[1:])
