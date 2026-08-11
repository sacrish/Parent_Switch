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
    return data_path


def _is_pose_bone(owner):
    return hasattr(owner, "bone") and hasattr(owner, "constraints")


def evaluated_world_matrix(context, owner):
    depsgraph = context.evaluated_depsgraph_get()
    if _is_pose_bone(owner):
        armature = owner.id_data.evaluated_get(depsgraph)
        pose_bone = armature.pose.bones.get(owner.name)
        if pose_bone is None:
            raise ValueError(f"Pose bone '{owner.name}' is no longer available")
        return (armature.matrix_world @ pose_bone.matrix).copy()
    return owner.evaluated_get(depsgraph).matrix_world.copy()


def _matrix_error(first, second):
    return max(
        abs(first[row][column] - second[row][column])
        for row in range(4)
        for column in range(4)
    )


def restore_visual_transform(context, owner, world_matrix, *, tolerance=1.0e-5):
    """Solve owner transform channels so its evaluated world matrix is preserved."""
    if _is_pose_bone(owner):
        armature_world = owner.id_data.matrix_world.copy()
        owner.matrix = armature_world.inverted_safe() @ world_matrix

    # Constraints operate on the owner transform, so compensate its basis by
    # the remaining evaluated world-space error. A few iterations also cover
    # parented owners and mixed constraint stacks without special-case math.
    for _iteration in range(6):
        context.view_layer.update()
        current_world = evaluated_world_matrix(context, owner)
        if _matrix_error(current_world, world_matrix) <= tolerance:
            return
        correction = current_world.inverted_safe() @ world_matrix
        owner.matrix_basis = owner.matrix_basis @ correction

    context.view_layer.update()
    current_world = evaluated_world_matrix(context, owner)
    if _matrix_error(current_world, world_matrix) > tolerance:
        raise RuntimeError("Unable to preserve the visual transform with the current constraint stack")


def keyframe_owner_transform(owner, frame):
    id_owner = getattr(owner, "id_data", None)
    if id_owner is None or not hasattr(id_owner, "keyframe_insert"):
        raise TypeError("The active owner cannot store transform animation data")

    rotation_path = {
        "QUATERNION": "rotation_quaternion",
        "AXIS_ANGLE": "rotation_axis_angle",
    }.get(owner.rotation_mode, "rotation_euler")

    data_paths = []
    for property_name in ("location", rotation_path, "scale"):
        data_path = owner.path_from_id(property_name)
        id_owner.keyframe_insert(
            data_path=data_path,
            frame=frame,
            group="Parent Switch",
        )
        data_paths.append(data_path)
    return data_paths


def _action_fcurves(id_owner):
    animation_data = getattr(id_owner, "animation_data", None)
    action = getattr(animation_data, "action", None)
    if action is None:
        return []

    # Blender 4.2/4.3 use legacy Action.fcurves. Blender 4.4+ stores curves in
    # layered Action channel-bags, selected by the owner's action slot.
    if hasattr(action, "fcurves"):
        return list(action.fcurves)

    slot = getattr(animation_data, "action_slot", None)
    if slot is None and len(action.slots):
        slot = action.slots[0]
    if slot is None:
        return []

    fcurves = []
    for layer in action.layers:
        for strip in layer.strips:
            if not hasattr(strip, "channelbag"):
                continue
            channelbag = strip.channelbag(slot)
            if channelbag is not None:
                fcurves.extend(channelbag.fcurves)
    return fcurves


def set_key_interpolation(id_owner, data_paths, frame, interpolation="CONSTANT"):
    paths = set(data_paths)
    for fcurve in _action_fcurves(id_owner):
        if fcurve.data_path not in paths:
            continue
        for keyframe_point in fcurve.keyframe_points:
            if abs(keyframe_point.co.x - frame) <= 1.0e-4:
                keyframe_point.interpolation = interpolation


def insert_guard_keys(context, owner, constraints, frame, *, key_transform):
    """Key the old space one frame before a switch.

    Constant outgoing interpolation prevents the new-space local transform at
    the switch frame from being interpolated backward into the old space.
    """
    guard_frame = frame - 1
    id_owner = owner.id_data

    constraint_paths = [
        keyframe_constraint_enabled(owner, constraint, guard_frame)
        for constraint in constraints
    ]
    set_key_interpolation(id_owner, constraint_paths, guard_frame)

    if not key_transform:
        return

    scene = context.scene
    scene.frame_set(guard_frame)
    transform_paths = keyframe_owner_transform(owner, guard_frame)
    set_key_interpolation(id_owner, transform_paths, guard_frame)
    scene.frame_set(frame)


def switch_child_of(
    context,
    owner,
    constraint_name,
    *,
    keyframe=False,
    frame=None,
    keep_transform=False,
):
    constraints = child_of_constraints(owner)
    selected = next((c for c in constraints if c.name == constraint_name), None)
    if selected is None:
        raise ValueError(f"Child Of constraint '{constraint_name}' was not found")

    visual_matrix = evaluated_world_matrix(context, owner) if keep_transform else None
    previous_states = [(constraint, constraint.enabled) for constraint in constraints]

    if keyframe:
        insert_guard_keys(
            context,
            owner,
            constraints,
            frame,
            key_transform=keep_transform,
        )
        # Moving to the guard frame evaluates animation. Restore the exact
        # constraint state that was active at the requested switch frame.
        for constraint, enabled in previous_states:
            constraint.enabled = enabled
        context.view_layer.update()

    for constraint in constraints:
        constraint.enabled = constraint is selected

    context.view_layer.update()
    if visual_matrix is not None:
        restore_visual_transform(context, owner, visual_matrix)

    if keyframe:
        for constraint in constraints:
            keyframe_constraint_enabled(owner, constraint, frame)
        if visual_matrix is not None:
            keyframe_owner_transform(owner, frame)
    return selected


def target_label(constraint):
    if constraint.target is None:
        return "No Target"
    if constraint.subtarget:
        return f"{constraint.target.name} / {constraint.subtarget}"
    return constraint.target.name
