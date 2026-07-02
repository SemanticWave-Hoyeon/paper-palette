# References

Palette is an original implementation, but the design follows established work
in perceptual color spaces, color harmony, categorical palette construction,
and color vision deficiency simulation.

## Perceptual Color Space

- Bjorn Ottosson, "A perceptual color space for image processing"  
  https://bottosson.github.io/posts/oklab/

Palette uses OKLab and OKLCH internally for color conversion, candidate
sampling, perceptual distance scoring, and hue/lightness/chroma-based
constraints. The implementation does not copy code from Ottosson's article; it
implements the published conversion equations.

## Aesthetic Palette Scoring

- Peter O'Donovan, Aseem Agarwala, and Aaron Hertzmann, "Color Compatibility
  From Large Datasets," ACM Transactions on Graphics, 2011  
  https://www.dgp.toronto.edu/~donovan/color/

- Daniel Cohen-Or, Olga Sorkine, Ran Gal, Tommer Leyvand, and Ying-Qing Xu,
  "Color Harmonization," ACM Transactions on Graphics, 2006  
  https://igl.ethz.ch/projects/color-harmonization/harmonization.pdf

Palette's `aesthetic` mode is inspired by this line of work: instead of using a
single hue rotation formula, it samples many candidate palettes and scores the
whole palette for hue cohesion, lightness contrast, chroma balance,
neutral/accent balance, duplicate avoidance, and muddy/neon penalties.

## Categorical Palette Generation

- Chris A. Glasbey, Gerie W. A. M. van der Heijden, Vivian F. K. Toh, and
  Alison Gray, "Colour Displays for Categorical Images," Colour Research &
  Application, 2007  
  https://pureportal.strath.ac.uk/en/publications/colour-displays-for-categorical-images

Palette's `categorical` mode uses a Glasbey-style greedy farthest-point
selection strategy in perceptual color space: each added color is selected to
remain visually distinct from the colors already chosen.

## Colorblind-Aware Generation

- Gustavo M. Machado, Manuel M. Oliveira, and Leandro A. F. Fernandes, "A
  Physiologically-based Model for Simulation of Color Vision Deficiency," IEEE
  Transactions on Visualization and Computer Graphics, 2009  
  https://www.inf.ufrgs.br/~oliveira/pubs_files/CVD_Simulation/CVD_Simulation.html

- ColorBrewer 2.0, color advice for cartography  
  https://colorbrewer2.org/

Palette simulates protanopia, deuteranopia, and tritanopia with
Machado-style matrices and uses the simulated colors as a distance constraint.
The ColorBrewer reference informs the practical UI/API idea that palettes used
for charts should offer colorblind-aware options.

## Presets

The bundled journal-style presets are manually curated color lists entered as
static data. Presets that originated in `#RRGGBBAA` form are normalized to
`#RRGGBB` because Palette's public API returns opaque HEX colors.
