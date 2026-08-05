"""Operators for editing target drafts and Child Of constraints."""

import bpy
from bpy.props import BoolProperty, StringProperty
from bpy.types import Operator

from . import core


def _settings(context):
    return context.window_manager.parent_switch_settings


class PARENTSWITCH_OT_target_add(Operator):
    bl_idname = "parent_switch.target_add"
    bl_label = "Add Target"
    bl_description = "Add a target to the draft list"
    bl_options = {"INTERNAL"}

    def execute(self, context):
        settings = _settings(context)
        settings.targets.add()
        settings.active_index = len(settings.targets) - 1
        return {"FINISHED"}


class PARENTSWITCH_OT_target_remove(Operator):
    bl_idname = "parent_switch.target_remove"
    bl_label = "Remove Target"
    bl_description = "Remove the selected target from the draft list"
    bl_options = {"INTERNAL"}

    @classmethod
    def poll(cls, context):
        return len(_settings(context).targets) > 0

    def execute(self, context):
        settings = _settings(context)
        index = min(settings.active_index, len(settings.targets) - 1)
        settings.targets.remove(index)
        settings.active_index = min(index, max(0, len(settings.targets) - 1))
        return {"FINISHED"}


class PARENTSWITCH_OT_add_constraints(Operator):
    bl_idname = "parent_switch.add_constraints"
    bl_label = "Add Constraints"
    bl_description = "Add disabled Child Of constraints to the active object or pose bone"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        owner = core.active_constraint_owner(context)
        return owner is not None and hasattr(owner, "constraints")

    def execute(self, context):
        settings = _settings(context)
        owner = core.active_constraint_owner(context)
        try:
            specs = core.collect_target_specs(settings)
            created = core.add_child_of_constraints(owner, specs)
        except (ValueError, RuntimeError, TypeError) as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

        settings.targets.clear()
        settings.active_index = 0
        self.report({"INFO"}, f"Added {len(created)} disabled Child Of constraint(s)")
        return {"FINISHED"}


class PARENTSWITCH_OT_switch(Operator):
    bl_idname = "parent_switch.switch"
    bl_label = "Switch Parent"
    bl_description = "Enable this Child Of constraint and disable the others"
    bl_options = {"REGISTER", "UNDO"}

    constraint_name: StringProperty(options={"HIDDEN"})
    insert_keyframe: BoolProperty(default=False, options={"HIDDEN"})

    @classmethod
    def poll(cls, context):
        return bool(core.child_of_constraints(core.active_constraint_owner(context)))

    def execute(self, context):
        owner = core.active_constraint_owner(context)
        try:
            core.switch_child_of(
                owner,
                self.constraint_name,
                keyframe=self.insert_keyframe,
                frame=context.scene.frame_current,
            )
        except (ValueError, RuntimeError, TypeError) as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

        action = "Switched and keyed" if self.insert_keyframe else "Switched"
        self.report({"INFO"}, f"{action} parent at frame {context.scene.frame_current}")
        return {"FINISHED"}


CLASSES = (
    PARENTSWITCH_OT_target_add,
    PARENTSWITCH_OT_target_remove,
    PARENTSWITCH_OT_add_constraints,
    PARENTSWITCH_OT_switch,
)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
