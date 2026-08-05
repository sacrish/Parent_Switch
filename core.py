"""Constraint operations independent from Blender UI layout code."""

from dataclasses import dataclass


@dataclass(frozen=True)
class TargetSpec:
    target: object
    bone_name: str = ""


def active_constraint_owner(context):
    """Return the active pose bone in Pose Mode, otherwise the active object."""
    if context.mode == "POSE" and context.active_pose_bone is not None:
        return context.active_pose_bone
    return context.active_object


def owner_display_name(context, owner):
    if owner is None:
        return "None"
    if context.mode == "POSE" and context.active_pose_bone is owner:
        return f"Bone: {owner.name}"
    return f"Object: {owner.name}"


def child_of_constraints(owner):
    if owner is None or not hasattr(owner, "constraints"):
        return []
    return [constraint for constraint in owner.constraints if constraint.type == "CHILD_OF"]


def collect_target_specs(settings):
    """Validate UI entries and return TargetSpec values.

    Raises ValueError before modifying the owner, keeping Add Constraints atomic.
    """
    specs = []
    errors = []
    seen = set()

    if settings.bones_only:
        armature = settings.bones_armature
        if armature is None or armature.type != "ARMATURE":
            raise ValueError("Choose an armature for Bones Only mode")

        for index, item in enumerate(settings.targets, start=1):
            bone_name = item.bone_name.strip()
            if not bone_name:
                errors.append(f"Target {index}: choose a bone")
                continue
            if armature.data.bones.get(bone_name) is None:
                errors.append(f"Target {index}: bone '{bone_name}' no longer exists")
                continue
            key = (armature.as_pointer(), bone_name)
            if key in seen:
                errors.append(f"Target {index}: duplicate bone '{bone_name}'")
                continue
            seen.add(key)
            specs.append(TargetSpec(armature, bone_name))
    else:
        for index, item in enumerate(settings.targets, start=1):
            target = item.target
            if target is None:
                errors.append(f"Target {index}: choose an object")
                continue

            bone_name = item.bone_name.strip() if target.type == "ARMATURE" else ""
            if bone_name and target.data.bones.get(bone_name) is None:
                errors.append(f"Target {index}: bone '{bone_name}' no longer exists")
                continue

            key = (target.as_pointer(), bone_name)
            if key in seen:
                label = bone_name or target.name
                errors.append(f"Target {index}: duplicate target '{label}'")
                continue
            seen.add(key)
            specs.append(TargetSpec(target, bone_name))

    if not settings.targets:
        errors.append("Add at least one target")
    if errors:
        raise ValueError("; ".join(errors))
    return specs


def constraint_name_for(spec):
    target_name = spec.target.name
    return f"Parent: {target_name} / {spec.bone_name}" if spec.bone_name else f"Parent: {target_name}"


def _same_rna_value(first, second):
    if first is None or second is None:
        return False
    try:
        return first.as_pointer() == second.as_pointer()
    except AttributeError:
        return first is second


def validate_owner_targets(owner, specs):
    for spec in specs:
        if _same_rna_value(owner, spec.target):
            raise ValueError("An object cannot use itself as a parent target")

        owner_object = getattr(owner, "id_data", None)
        if (
            hasattr(owner, "bone")
            and _same_rna_value(owner_object, spec.target)
            and spec.bone_name == owner.name
        ):
            raise ValueError("A pose bone cannot use itself as a parent target")


def add_child_of_constraints(owner, specs):
    validate_owner_targets(owner, specs)
    created = []
    try:
        for spec in specs:
            constraint = owner.constraints.new(type="CHILD_OF")
            constraint.name = constraint_name_for(spec)
            constraint.target = spec.target
            constraint.subtarget = spec.bone_name
            constraint.enabled = False
            created.append(constraint)
    except Exception:
        for constraint in reversed(created):
            owner.constraints.remove(constraint)
        raise
    return created


def keyframe_constraint_enabled(owner, constraint, frame):
    """Key the constraint header's Enable/Disable (eye) property.

    Constraints are nested RNA data. Inserting the key through the owner ID and
    the constraint's full path lets Blender associate the F-Curve with the
    actual enabled button for evaluation and manual editing.
    """
    id_owner = getattr(owner, "id_data", None)
    if id_owner is None or not hasattr(id_owner, "keyframe_insert"):
        raise TypeError("The active constraint owner cannot store animation data")

    data_path = constraint.path_from_id("enabled")
    id_owner.keyframe_insert(data_path=data_path, frame=frame, group="Parent Switch")


def switch_child_of(owner, constraint_name, *, keyframe=False, frame=None):
    constraints = child_of_constraints(owner)
    selected = next((c for c in constraints if c.name == constraint_name), None)
    if selected is None:
        raise ValueError(f"Child Of constraint '{constraint_name}' was not found")

    for constraint in constraints:
        constraint.enabled = constraint is selected

    if keyframe:
        for constraint in constraints:
            keyframe_constraint_enabled(owner, constraint, frame)
    return selected


def target_label(constraint):
    if constraint.target is None:
        return "No Target"
    if constraint.subtarget:
        return f"{constraint.target.name} / {constraint.subtarget}"
    return constraint.target.name
