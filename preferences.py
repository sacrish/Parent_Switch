"""Add-on preferences shown in Blender Preferences."""

import bpy
from bpy.props import BoolProperty
from bpy.types import AddonPreferences


class PARENTSWITCH_AP_preferences(AddonPreferences):
    bl_idname = __package__

    skip_guard_at_scene_start: BoolProperty(
        name="Skip Guard Key at Scene Start",
        description=(
            "Do not insert a guard key before Scene Frame Start when keying "
            "on the first frame"
        ),
        default=True,
    )

    def draw(self, _context):
        self.layout.prop(self, "skip_guard_at_scene_start")


def should_skip_guard_at_scene_start(context):
    addon = context.preferences.addons.get(__package__)
    if addon is None:
        # Source-tree tests register classes directly instead of enabling the
        # extension through Preferences. Match the user-facing default.
        return True
    return addon.preferences.skip_guard_at_scene_start


CLASSES = (PARENTSWITCH_AP_preferences,)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
