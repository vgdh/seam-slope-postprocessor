# Seam-slope postprocessor
Post processor for G-code files for hiding a FDM seam.

This post processor modifies the G-code commands to hide the seam. The post processor enhances the surface quality and toughness of the printed part by concealing the seam.
Works with gcode produced by any slicer.

[Download the script](postprocessor_seam_slope.py)

### Requariements:
- Python 3.12

### Running the script
**--path to python folder--**\python.exe "**--path to python script--**\postprocessor_seam_slope.py" "**--path to gcode file--**\slicer_x.gcode" --first_layer=0.3 --other_layers=0.3 --slope_min_length=10 --slope_steps=8;

### Running the postprocessor from prusa slicer
**--path to python folder--**\python.exe "**--path to python script--**\postprocessor_seam_slope.py" --first_layer=0.3 --other_layers=0.3 -slope_min_length=10 --slope_steps=8;

### Recommended settings
- Line width = 0.6-0.8mm
- Line height = 0.3
- Slope steps = 6-15steps (Many steps over a short distance may cause unusual behavior of the extruder if use LA)
- **Don't use any dynamic speed control**
- Use dynamic acceleration control with min acceleration for external perimeter (like 500)

### Macro photos of printed parts
![photo_2023-12-27_00-13-31](https://github.com/vgdh/seam-slope-postprocessor/assets/15322782/3e670575-2c52-479a-ad1e-e1534dae0c72)
![botom 2](https://github.com/vgdh/seam-hiding-whitepaper/assets/15322782/a429c68b-1711-44fb-9c97-4f046763b9d3)
![botom 3](https://github.com/vgdh/seam-hiding-whitepaper/assets/15322782/f1ebe624-44af-4e7e-a7a7-aa55142d8ca1)
![photo_1_2023-12-20_16-13-32](https://github.com/vgdh/seam-hiding-whitepaper/assets/15322782/e4982fe6-1fb4-4d81-90e3-9ea5f6d95e3b)
![top 1](https://github.com/vgdh/seam-hiding-whitepaper/assets/15322782/fbca6b12-d2ec-416c-ae08-4e37baf869fd)
![side 1](https://github.com/vgdh/seam-hiding-whitepaper/assets/15322782/dd3a2900-39af-4baa-b638-91ef0328c86e)
![botom 1](https://github.com/vgdh/seam-hiding-whitepaper/assets/15322782/a96b0b4b-1658-4c4a-a8d8-b70bbde8845e)
![center 1](https://github.com/vgdh/seam-hiding-whitepaper/assets/15322782/2989402c-cd03-430e-9bf3-4ee902ee383f)
![top 2](https://github.com/vgdh/seam-hiding-whitepaper/assets/15322782/bdfca30b-73c2-4045-b297-a6454080ec01)


### Screnshots of my settings
![post](https://github.com/vgdh/seam-slope-postprocessor/assets/15322782/0754c5f9-e129-43e3-ba6c-4a50a13d1c70)
![line width](https://github.com/vgdh/seam-slope-postprocessor/assets/15322782/815964ec-44c0-4854-8aab-6751fbfa1167)
![layer height](https://github.com/vgdh/seam-slope-postprocessor/assets/15322782/832873c5-f7b7-4826-a2d8-89219c82a22b)
![lift](https://github.com/vgdh/seam-slope-postprocessor/assets/15322782/610a1689-aad4-4379-9818-b9a61942c0a3)
