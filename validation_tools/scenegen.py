import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
from pathlib import Path


class xmltag:
    """A class to represent an XML tag."""

    def __init__(self, tagname, **kwargs):
        self.tagname = tagname
        if "children" not in kwargs:
            self.children = []
        else:
            self.children = kwargs["children"]
        self.kwargs = kwargs
        self.kwargs.pop("children", None)

    def contains_child(self, tagname):
        for child in self.children:
            if child.tagname == tagname:
                return True
        return False

    def remove_child(self, tagname):
        for child in self.children:
            if child.tagname == tagname:
                self.children.remove(child)
                return

    def add_child(self, tag):
        self.children.append(tag)

    def __str__(self) -> str:
        kwarg_str = " ".join([f"{attr}={value}" for attr, value in self.kwargs.items()])
        children_str = "\n".join([str(child) for child in self.children])
        return f"<{self.tagname} {kwarg_str}> {children_str} </{self.tagname}>"

    def __repr__(self) -> str:
        return self.__str__()

    def to_tag(self, root):
        tag = ET.Element(self.tagname)
        for k, v in self.kwargs.items():
            tag.set(k, v)
        for child in self.children:
            child.to_tag(tag)
        root.append(tag)
        return root


def to_xml(scene):
    root = ET.Element("scene")
    for _, value in scene.items():
        value.to_tag(root)
    return root


class Scene:
    def __init__(self, name, desc):
        self.name = name
        self.desc = desc

    def set_integrator(self, integrator):
        self.desc["integrator"].kwargs["type"] = integrator

    def set_spp(self, spp):
        self.desc["sampler"].children[0].kwargs["value"] = str(spp)

    def set_resolution(self, width, height):
        self.desc["camera"].children[2].kwargs["value"] = str(width)
        self.desc["camera"].children[3].kwargs["value"] = str(height)

    def set_fov(self, fov):
        self.desc["camera"].children[0].kwargs["value"] = str(fov)

    def set_quality(self, quality):
        """
        Configure the rendering quality using predefined presets.

        Parameters
        ----------
        quality : str
            One of the following options:

            - "l" (low): 256×256 at 16 spp.
            Fast preview with minimal detail.

            - "m" (medium): 512×512 at 32 spp.
            Balanced between speed and clarity.

            - "h" (high): 512×512 at 512 spp.
            High sampling for reduced noise at moderate resolution.

            - "final" or "report": resolution 1024×1024 at 1024 spp.
            High-quality output suitable for the final report.

        Raises
        ------
        ValueError
            If `quality` is not one of the recognized presets.
        """
        if quality == "l":
            self.set_spp(16)
            self.set_resolution(256, 256)
        elif quality == "m":
            self.set_spp(32)
            self.set_resolution(512, 512)
        elif quality == "h":
            self.set_spp(512)
            self.set_resolution(512, 512)
        elif quality == "final" or quality == "report":
            self.set_spp(1024)
            self.set_resolution(1024, 1024)
        else:
            raise ValueError(f"Quality {quality} not recognized.")

    def add_object(self, name, tag, **kwargs):
        if name in self.desc:
            raise ValueError(f"Object with name {name} already exists in the scene.")
        tag_ = xmltag(tag, **kwargs)
        self.desc[name] = tag_

    def remove_object(self, name):
        if name not in self.desc:
            raise ValueError(f"Object with name {name} does not exist in the scene.")
        del self.desc[name]

    def add_tag_object(self, name, obj):
        if name in self.desc:
            raise ValueError(f"Object with name {name} already exists in the scene.")
        self.desc[name] = obj

    def get_object(self, name):
        if name not in self.desc:
            raise ValueError(f"Object with name {name} does not exist in the scene.")
        return self.desc[name]

    def set_bsdf(self, object, bsdf):
        obj = self.get_object(object)
        obj.remove_child("bsdf")
        obj.add_child(bsdf)

    def set_emission(self, object, emission):
        obj = self.get_object(object)
        obj.remove_child("emitter")
        emitter_tag = xmltag(
            "emitter",
            type="area",
            children=[
                xmltag(
                    "color",
                    name="radiance",
                    value=f"{emission[0]} {emission[1]} {emission[2]}",
                )
            ],
        )
        obj.add_child(emitter_tag)

    def generate(self):
        """Generate the scene XML and return it as a string."""
        xml = to_xml(self.desc)
        return minidom.parseString(ET.tostring(xml)).toprettyxml(indent="\t")

    def copy(self):
        return Scene(self.name, self.desc.copy())


def tuple_to_str(t, commas=True):
    if commas:
        return ", ".join([str(x) for x in t])
    return " ".join([str(x) for x in t])


def make_material(shader, **kwargs):
    children = []
    for key, value in kwargs.items():
        type = "float"
        if isinstance(value, tuple):
            value = tuple_to_str(value, commas=False)
            type = "color"
        if isinstance(value, bool):
            type = "bool"
            value = "true" if value else "false"
        children.append(xmltag(type, name=key, value=str(value)))
    return xmltag("bsdf", type=shader, children=children)


def make_cbox_scene(
    name="cbox",
    main_wall_color=(1, 1, 1),
    left_wall_color=(0.9, 0.1, 0.1),
    right_wall_color=(0.1, 0.9, 0.1),
    emitter_color=(10, 10, 10),
    cuboid_color=(1, 1, 1),
    ball_color=(1, 1, 1),
):
    # Basic scene config
    scene_desc = {
        "integrator": xmltag("integrator", type="path_mis"),
        "sampler": xmltag(
            "sampler",
            type="independent",
            children=[xmltag("integer", name="sampleCount", value="32")],
        ),
        "camera": xmltag(
            "camera",
            type="perspective",
            children=[
                xmltag("float", name="fov", value="36.797756851565"),
                xmltag(
                    "transform",
                    name="toWorld",
                    children=[
                        xmltag("scale", value="1,1,-1"),
                        xmltag(
                            "matrix",
                            value="1.0,0.0,0.0,0.0,0.0,-1.6292068494294654e-07,-1.0,-4.0,0.0,1.0,-1.6292068494294654e-07,0.0,0.0,0.0,0.0,1.0",
                        ),
                    ],
                ),
                xmltag("integer", name="width", value="512"),
                xmltag("integer", name="height", value="512"),
                xmltag("rfilter", type="box"),
            ],
        ),
    }

    scene = Scene(name, scene_desc)

    resource_dir = "../../../validation_tools/meshes"

    scene.add_object(
        "main_walls",
        "mesh",
        type="obj",
        children=[
            xmltag("string", name="filename", value=f"{resource_dir}/main_walls.obj"),
            xmltag(
                "bsdf",
                type="diffuse",
                children=[
                    xmltag("color", name="albedo", value=tuple_to_str(main_wall_color))
                ],
            ),
        ],
    )

    scene.add_object(
        "left_wall",
        "mesh",
        type="obj",
        children=[
            xmltag("string", name="filename", value=f"{resource_dir}/left_wall.obj"),
            xmltag(
                "bsdf",
                type="diffuse",
                children=[
                    xmltag("color", name="albedo", value=tuple_to_str(left_wall_color))
                ],
            ),
        ],
    )

    scene.add_object(
        "right_wall",
        "mesh",
        type="obj",
        children=[
            xmltag("string", name="filename", value=f"{resource_dir}/right_wall.obj"),
            xmltag(
                "bsdf",
                type="diffuse",
                children=[
                    xmltag("color", name="albedo", value=tuple_to_str(right_wall_color))
                ],
            ),
        ],
    )

    scene.add_object(
        "emitter",
        "mesh",
        type="obj",
        children=[
            xmltag("string", name="filename", value=f"{resource_dir}/emitter.obj"),
            xmltag(
                "emitter",
                type="area",
                children=[
                    xmltag("color", name="radiance", value=tuple_to_str(emitter_color))
                ],
            ),
        ],
    )

    scene.add_object(
        "cuboid",
        "mesh",
        type="obj",
        children=[
            xmltag("string", name="filename", value=f"{resource_dir}/cuboid.obj"),
            xmltag(
                "bsdf",
                type="diffuse",
                children=[
                    xmltag("color", name="albedo", value=tuple_to_str(cuboid_color))
                ],
            ),
        ],
    )

    scene.add_object(
        "ball",
        "mesh",
        type="sphere",
        children=[
            xmltag("point", name="center", value="0.35 -0.3 -0.6"),
            xmltag("float", name="radius", value="0.4"),
            xmltag(
                "bsdf",
                type="diffuse",
                children=[
                    xmltag("color", name="albedo", value=tuple_to_str(ball_color))
                ],
            ),
        ],
    )

    return scene


def make_mat_prev_scene(name="mat_prev"):
    # Basic scene config
    scene_desc = {
        "integrator": xmltag("integrator", type="path_mis"),
        "sampler": xmltag(
            "sampler",
            type="independent",
            children=[xmltag("integer", name="sampleCount", value="32")],
        ),
        "camera": xmltag(
            "camera",
            type="perspective",
            children=[
                xmltag("float", name="fov", value="20"),
                xmltag(
                    "transform",
                    name="toWorld",
                    children=[
                        xmltag("scale", value="1,1,-1"),
                        xmltag(
                            "matrix",
                            value="1.0,0.0,0.0,0.0,0.0,-1.6292068494294654e-07,-1.0,-8.0,0.0,1.0,-1.6292068494294654e-07,0.0,0.0,0.0,0.0,1.0",
                        ),
                    ],
                ),
                xmltag("integer", name="width", value="512"),
                xmltag("integer", name="height", value="512"),
                xmltag("rfilter", type="box"),
            ],
        ),
    }

    scene = Scene(name, scene_desc)

    resource_dir = "../../../validation_tools/meshes"

    scene.add_object(
        "material_preview",
        "mesh",
        type="obj",
        children=[
            xmltag("string", name="filename", value=f"{resource_dir}/suzanne.obj"),
            xmltag(
                "bsdf",
                type="diffuse",
                children=[xmltag("color", name="albedo", value="1 1 1")],
            ),
        ],
    )

    scene.add_object(
        "keylight",
        "mesh",
        type="sphere",
        children=[
            xmltag("point", name="center", value="-3 -2 2"),
            xmltag("float", name="radius", value="1"),
            xmltag(
                "emitter",
                type="area",
                children=[xmltag("color", name="radiance", value="10 10 10")],
            ),
        ],
    )

    scene.add_object(
        "filllight",
        "mesh",
        type="sphere",
        children=[
            xmltag("point", name="center", value="0 50 0"),
            xmltag("float", name="radius", value="15"),
            xmltag(
                "emitter",
                type="area",
                children=[xmltag("color", name="radiance", value="0.4 0.6 0.8")],
            ),
        ],
    )

    scene.add_object(
        "rimlight",
        "mesh",
        type="sphere",
        children=[
            xmltag("point", name="center", value="7 0 -4"),
            xmltag("float", name="radius", value="1"),
            xmltag(
                "emitter",
                type="area",
                children=[xmltag("color", name="radiance", value="2 2 2")],
            ),
        ],
    )

    return scene
