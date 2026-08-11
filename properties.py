"""Transient UI state for Parent Switch.

The state lives on WindowManager so target drafts are not saved into .blend files.
"""

import bpy
from bpy.props import BoolProperty, CollectionProperty, IntProperty, PointerProperty, StringProperty
from bpy.types import PropertyGroup


def _clear_targets(settings):
    settings.targets.clear()
    settings.active_index = 0


def _target_changed(self, _context):
    self.bone_name = ""


def _mode_changed(self, _context):
    _clear_targets(self)


def _bones_armature_changed(self, _context):
    _clear_targets(self)


def _armature_object_poll(_self, obj):
    return obj is not None and obj.type == "ARMATURE"


class PARENTSWITCH_PG_target(PropertyGroup):
    target: PointerProperty(
        name="Target",
        description="Object used as the Child Of target",
        type=bpy.types.Object,
        update=_target_changed,
    )
    bone_name: StringProperty(
        name="Bone",
        description="Optional target bone when the target is an armature",
    )


class PARENTSWITCH_PG_settings(PropertyGroup):
    keep_transform: BoolProperty(
        name="Keep Transform",
        description="Preserve the visual transform when switching parents",
        default=True,
    )
    bones_only: BoolProperty(
        name="Bones Only",
        description="Use multiple bones from one armature as targets",
        default=False,
        update=_mode_changed,
    )
    bones_armature: PointerProperty(
        name="Armature",
        description="Armature whose bones are available as targets",
        type=bpy.types.Object,
        poll=_armature_object_poll,
        update=_bones_armature_changed,
    )
    targets: CollectionProperty(type=PARENTSWITCH_PG_target)
    active_index: IntProperty(default=0, min=0)


CLASSES = (
    PARENTSWITCH_PG_target,
    PARENTSWITCH_PG_settings,
)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.WindowManager.parent_switch_settings = PointerProperty(
        type=PARENTSWITCH_PG_settings
    )


def unregister():
    if hasattr(bpy.types.WindowManager, "parent_switch_settings"):
        del bpy.types.WindowManager.parent_switch_settings
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
