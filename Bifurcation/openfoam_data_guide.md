## Reading OpenFOAM Simulation Data

### Directory Structure

```
openFoam(1e-5)/
└── bifurcation_angle{30,45,60}_{500,750,1000}_ascii/
    ├── Re100/
    │   ├── 0/                      # Initial/boundary conditions
    │   ├── <final_timestep>/       # Converged solution fields
    │   │   └── wallShearStress     # WSS vectors on wall faces
    │   ├── constant/
    │   │   └── polyMesh/           # Mesh geometry (shared across all Re)
    │   │       ├── points          # (x, y, z) coordinates of every vertex
    │   │       ├── faces           # Face-to-point connectivity
    │   │       └── boundary        # Patch definitions (walls, inlet, outlet)
    │   ├── system/                 # Solver configuration
    │   └── log.run                 # Convergence log
    ├── Re200/
    │   ├── <final_timestep>/
    │   │   └── wallShearStress
    │   └── ...                     # No constant/ — use Re100's mesh
    └── ...
```

> **Note:** The mesh (`constant/polyMesh/`) is only stored in `Re100/` for each geometry. It is identical across all Reynolds numbers for a given geometry — the same wall faces, points, and numbering apply to every Re case.

### Naming Convention

Each geometry folder encodes the bifurcation angle and mesh element count:
- `bifurcation_angle45_750_ascii` → 45° bifurcation angle, 750-element mesh

Reynolds numbers range from `Re100` to `Re2100` in increments of 100.

### Reading the Mesh

The mesh lives in `Re100/constant/polyMesh/`. Key files:

**`points`** — Vertex coordinates, one per line:
```
(x y z)
(x y z)
...
```

**`faces`** — Each face is a list of point indices:
```
4(0 1 5 4)     # face with 4 points: indices 0, 1, 5, 4
```

**`boundary`** — Defines which faces belong to which patch:
```
walls
{
    type            wall;
    nFaces          3000;
    startFace       181000;
}
```

This means face indices `181000` to `183999` are wall faces.

### Reading wallShearStress

The `wallShearStress` file in the final timestep directory contains WSS vectors for all wall boundary faces:

```
(wx wy wz)
(wx wy wz)
...
```

The values are ordered by patch, matching the face ranges defined in `boundary`.

### Python Parsing Example

```python
import numpy as np
import re
import os


def parse_openfoam_vector_field(filepath):
    """Parse an OpenFOAM vector field file (e.g. wallShearStress, points)."""
    with open(filepath, 'r') as f:
        content = f.read()

    # Find the data block between parentheses after the count
    match = re.search(r'(\d+)\s*\n\s*\(\s*\n(.*?)\n\s*\)', content, re.DOTALL)
    if not match:
        raise ValueError(f"Could not parse {filepath}")

    n = int(match.group(1))
    block = match.group(2)

    vectors = re.findall(r'\(\s*([^\)]+)\)', block)
    data = np.array([[float(x) for x in v.split()] for v in vectors])

    assert len(data) == n, f"Expected {n} entries, got {len(data)}"
    return data


def parse_openfoam_faces(filepath):
    """Parse the faces file into a list of point index arrays."""
    with open(filepath, 'r') as f:
        content = f.read()

    match = re.search(r'(\d+)\s*\n\s*\(\s*\n(.*?)\n\s*\)', content, re.DOTALL)
    block = match.group(2)

    faces = []
    for line in block.strip().split('\n'):
        idx_match = re.search(r'\d+\(([^)]+)\)', line.strip())
        if idx_match:
            indices = [int(x) for x in idx_match.group(1).split()]
            faces.append(indices)
    return faces


def parse_boundary(filepath):
    """Parse the boundary file to get patch names, types, and face ranges."""
    with open(filepath, 'r') as f:
        content = f.read()

    patches = {}
    pattern = r'(\w+)\s*\{[^}]*type\s+(\w+);\s*nFaces\s+(\d+);\s*startFace\s+(\d+);'
    for match in re.finditer(pattern, content):
        name = match.group(1)
        patches[name] = {
            'type': match.group(2),
            'nFaces': int(match.group(3)),
            'startFace': int(match.group(4)),
        }
    return patches


def get_wall_wss(case_path, mesh_path=None):
    """
    Extract WSS vectors and their spatial coordinates on wall patches.

    Parameters
    ----------
    case_path : str
        Path to a specific Re case (e.g. .../Re1600/)
    mesh_path : str, optional
        Path to the Re case containing constant/polyMesh/.
        Defaults to case_path. Use this when mesh is stored in Re100 only.

    Returns
    -------
    dict with keys:
        'coords'  : (N, 3) array of wall face centre coordinates
        'wss'     : (N, 3) array of wall shear stress vectors
        'patches' : dict mapping patch name -> slice of the arrays
    """
    if mesh_path is None:
        mesh_path = case_path

    # Find the final timestep directory (highest numbered folder)
    timesteps = [d for d in os.listdir(case_path)
                 if d.isdigit() and int(d) > 0]
    final_time = max(timesteps, key=int)

    # Parse mesh
    poly = os.path.join(mesh_path, 'constant', 'polyMesh')
    points = parse_openfoam_vector_field(os.path.join(poly, 'points'))
    faces = parse_openfoam_faces(os.path.join(poly, 'faces'))
    boundary = parse_boundary(os.path.join(poly, 'boundary'))

    # Parse WSS
    wss_path = os.path.join(case_path, final_time, 'wallShearStress')
    wss = parse_openfoam_vector_field(wss_path)

    # Get wall patches and compute face centres
    wall_patches = {k: v for k, v in boundary.items() if v['type'] == 'wall'}

    all_coords = []
    all_wss = []
    patch_slices = {}
    offset = 0

    # WSS field only contains values for wall faces, ordered by patch
    wss_offset = 0
    for name, info in wall_patches.items():
        n = info['nFaces']
        start = info['startFace']

        # Compute face centres
        centres = []
        for i in range(start, start + n):
            face_points = points[faces[i]]
            centres.append(face_points.mean(axis=0))
        centres = np.array(centres)

        patch_wss = wss[wss_offset:wss_offset + n]
        wss_offset += n

        all_coords.append(centres)
        all_wss.append(patch_wss)
        patch_slices[name] = slice(offset, offset + n)
        offset += n

    return {
        'coords': np.vstack(all_coords),
        'wss': np.vstack(all_wss),
        'patches': patch_slices,
    }


# --- Usage ---
base = 'Bifurcation/results/openFoam(1e-5)/bifurcation_angle45_750_ascii'
mesh_re = os.path.join(base, 'Re100')  # mesh is stored here

result = get_wall_wss(
    case_path=os.path.join(base, 'Re1600'),
    mesh_path=mesh_re,
)

print(f"Wall face count: {result['coords'].shape[0]}")
print(f"WSS shape: {result['wss'].shape}")
print(f"Wall patches: {list(result['patches'].keys())}")

# Compute WSS magnitude
wss_mag = np.linalg.norm(result['wss'], axis=1)
print(f"Mean WSS magnitude: {wss_mag.mean():.6f}")
print(f"Max WSS magnitude: {wss_mag.max():.6f}")
```

### WSS Magnitude

The `wallShearStress` field contains vectors `(τx, τy, τz)`. To get scalar WSS magnitude:

```python
wss_magnitude = np.linalg.norm(wss_vectors, axis=1)
```

Note: OpenFOAM reports kinematic WSS (divided by density, units m²/s²). To convert to physical WSS (Pa), multiply by fluid density ρ.
