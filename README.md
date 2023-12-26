# Seam-slope postprocessor
Post processor for G-code files for hiding a FDM seam.

This post processor modifies the G-code commands to hide the seam. The post processor enhances the surface quality and toughness of the printed part by concealing the seam.

### Requariements:
- Python 3.12

### Running the script
**--path to python folder--**\python.exe "**--path to python script--**\postprocessor_seam_slope.py" "**--path to gcode file--**\slicer_x.gcode" --first_layer=0.3 --other_layers=0.3 --slope_length=20 --slope_steps=10;

### Running the postprocessor from prusa slicer
**--path to python folder--**\python.exe "**--path to python script--**\postprocessor_seam_slope.py" --first_layer=0.3 --other_layers=0.3 --slope_length=20 --slope_steps=10;

### Recommended settings
- Line width = 0.6-0.8mm
- Line height = 0.3
- Slope lenght = >10mm
- Slope steps = 10-20steps
- Don't use any dynamic speed control
- Use dynamic acceleration control with min acceleration for external perimeter
- 
### Screnshots of a printed part


### Screnshots of my settings
![postprocessor](https://github.com/vgdh/seam-slope-postprocessor/assets/15322782/950390c4-cd86-4dfc-8f58-d2cd4132007f)

![line width](https://github.com/vgdh/seam-slope-postprocessor/assets/15322782/815964ec-44c0-4854-8aab-6751fbfa1167)

![layer height](https://github.com/vgdh/seam-slope-postprocessor/assets/15322782/832873c5-f7b7-4826-a2d8-89219c82a22b)

![lift](https://github.com/vgdh/seam-slope-postprocessor/assets/15322782/610a1689-aad4-4379-9818-b9a61942c0a3)
