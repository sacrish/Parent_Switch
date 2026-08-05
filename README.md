# Parent Switch

Parent Switch is a Blender add-on for creating several disabled **Child Of**
constraints on an object or pose bone, then switching and keying those parents
from one compact panel.

## Compatibility

- Primary target: Blender 5.2 LTS
- Compatible extension API: Blender 4.2 and newer

## Install

1. Build or download `parent_switch-1.0.2.zip`.
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

Other constraint types are never modified.

## Uninstall behavior

Draft UI state is stored on Blender's transient `WindowManager`, not in the
`.blend` file. Disabling or uninstalling the extension unregisters its panels,
operators, lists, and properties. Child Of constraints intentionally created by
the user remain part of the scene, like any other scene edit.

## Build from source

From the repository root:

```powershell
& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" `
  --command extension build `
  --source-dir ".\parent_switch_addon" `
  --output-filepath ".\parent_switch-1.0.2.zip"
```
