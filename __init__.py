"""Parent Switch Blender add-on."""

bl_info = {
    "name": "Parent Switch",
    "author": "Parent Switch Contributors",
    "version": (1, 0, 2),
    "blender": (4, 2, 0),
    "location": "3D Viewport > Sidebar > Item > Parent Switch",
    "description": "Create and switch between multiple Child Of constraints",
    "category": "Animation",
}

from . import operators, properties, ui


MODULES = (properties, operators, ui)


def register():
    for module in MODULES:
        module.register()


def unregister():
    for module in reversed(MODULES):
        module.unregister()


if __name__ == "__main__":
    register()
