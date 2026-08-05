"""3D Viewport Item-tab interface."""

import bpy
from bpy.types import Panel, UIList

from . import core


OBJECT_ICONS = {
    "ARMATURE": "OUTLINER_OB_ARMATURE",
    "CAMERA": "OUTLINER_OB_CAMERA",
    "CURVE": "OUTLINER_OB_CURVE",
    "EMPTY": "OUTLINER_OB_EMPTY",
    "FONT": "OUTLINER_OB_FONT",
    "LATTICE": "OUTLINER_OB_LATTICE",
    "LIGHT": "OUTLINER_OB_LIGHT",
    "MESH": "OUTLINER_OB_MESH",
    "META": "OUTLINER_OB_META",
    "SPEAKER": "OUTLINER_OB_SPEAKER",
    "SURFACE": "OUTLINER_OB_SURFACE",
}


def _settings(context):
    return context.window_manager.parent_switch_settings


def _target_icon(constraint):
    if constraint.subtarget:
        return "BONE_DATA"
    if constraint.target is None:
        return "ERROR"
    return OBJECT_ICONS.get(constraint.target.type, "OBJECT_DATA")


class PARENTSWITCH_UL_targets(UIList):
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        settings = _settings(context)
        row = layout.row(align=True)
        if settings.bones_only:
            armature = settings.bones_armature
            if armature is not None:
                row.prop_search(item, "bone_name", armature.data, "bones", text="", icon="BONE_DATA")
            else:
                row.label(text="Choose an armature", icon="ERROR")
            return

        row.prop(item, "target", text="")
        if item.target is not None and item.target.type == "ARMATURE":
            row.prop_search(item, "bone_name", item.target.data, "bones", text="", icon="BONE_DATA")


class PARENTSWITCH_PT_main(Panel):
    bl_label = "Parent Switch"
    bl_idname = "PARENTSWITCH_PT_main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Item"

    def draw(self, context):
        owner = core.active_constraint_owner(context)
        self.layout.label(text=core.owner_display_name(context, owner), icon="CONSTRAINT")


class PARENTSWITCH_PT_add(Panel):
    bl_label = "Add Parents"
    bl_idname = "PARENTSWITCH_PT_add"
    bl_parent_id = "PARENTSWITCH_PT_main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Item"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        settings = _settings(context)

        layout.prop(settings, "bones_only")
        if settings.bones_only:
            layout.prop(settings, "bones_armature")

        row = layout.row()
        row.template_list(
            "PARENTSWITCH_UL_targets",
            "",
            settings,
            "targets",
            settings,
            "active_index",
            rows=4,
        )
        buttons = row.column(align=True)
        buttons.operator("parent_switch.target_add", text="", icon="ADD")
        buttons.operator("parent_switch.target_remove", text="", icon="REMOVE")

        owner = core.active_constraint_owner(context)
        button = layout.row()
        button.enabled = owner is not None and hasattr(owner, "constraints")
        button.operator("parent_switch.add_constraints", icon="CONSTRAINT")


class PARENTSWITCH_PT_switch(Panel):
    bl_label = "Switch Parents"
    bl_idname = "PARENTSWITCH_PT_switch"
    bl_parent_id = "PARENTSWITCH_PT_main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Item"

    def draw(self, context):
        layout = self.layout
        owner = core.active_constraint_owner(context)
        constraints = core.child_of_constraints(owner)

        if not constraints:
            layout.label(text="No Child Of constraints", icon="INFO")
            return

        for constraint in constraints:
            card = layout.box()
            title_row = card.row()
            title_row.label(
                text=core.target_label(constraint),
                icon=_target_icon(constraint),
            )

            button_row = card.row(align=True)
            set_op = button_row.operator(
                "parent_switch.switch",
                text="Set",
                depress=constraint.enabled,
            )
            set_op.constraint_name = constraint.name
            set_op.insert_keyframe = False
            key_op = button_row.operator(
                "parent_switch.switch",
                text="Key",
                icon="KEY_HLT",
            )
            key_op.constraint_name = constraint.name
            key_op.insert_keyframe = True


CLASSES = (
    PARENTSWITCH_UL_targets,
    PARENTSWITCH_PT_main,
    PARENTSWITCH_PT_add,
    PARENTSWITCH_PT_switch,
)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
