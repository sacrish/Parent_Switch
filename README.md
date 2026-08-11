# Parent Switch

Parent Switch is a Blender add-on for creating several disabled **Child Of**
constraints on an object or pose bone, then switching and keying those parents
from one compact panel.

## Compatibility

Blender 4.2 and newer

## Install

1. Download the latest version from Release section.
2. In Blender, open **Edit > Preferences > Get Extensions**.
3. Use the menu in the top-right and choose **Install from Disk**.
4. Select the ZIP and enable **Parent Switch** if necessary.

The UI is in **3D Viewport > Sidebar (`N`) > Item > Parent Switch**. It does
not create a new Sidebar tab.

## Add Parents

1. Select the object to constrain, or select a pose bone in Pose Mode.
2. Add target rows with `+`.
3. In normal mode, choose an object in each row. If it is an armature, an
   optional bone picker appears.
4. For several bones from one rig, enable **Bones Only**, choose the armature,
   and select a bone in every row.
5. Click **Add Constraints**.

All created Child Of constraints start disabled. The draft target list is
cleared after successful creation.

## Switch Parents

The panel automatically shows every Child Of constraint belonging to the active
object or active pose bone.

- **Set** enables that constraint and disables the other Child Of constraints.
- **Key** performs Set and inserts a keyframe on every Child Of constraint's
  header Enable/Disable (eye) state at the current frame.
- **Keep Transform** preserves the active object or pose bone's visual
  location, rotation, and scale while switching. With **Key**, those transform
  channels are keyed as well so the no-jump result plays back correctly.

**Key** also inserts guard keys one frame before the switch. The old parent and
old-space transform are held with constant outgoing interpolation until the
switch frame, preventing the new local transform from interpolating backward
into the preceding animation.

Other constraint types are never modified.
