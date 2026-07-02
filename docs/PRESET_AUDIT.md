# Preset Audit

This document records how bundled journal-style presets were checked.

Primary source used for the current audit:

- `ggsci` palette source, `R/palettes.R`  
  https://github.com/nanxstats/ggsci/blob/master/R/palettes.R

The journal-style presets in Paper Palette are descriptive palette styles. They
do not imply endorsement by, affiliation with, or trademark permission from the
named journals or publishers.

## Verified Presets

| Paper Palette preset | Source palette | Status |
| --- | --- | --- |
| `npg` | `ggsci_db$"npg"$"nrc"` | Matches source values. |
| `science` | `ggsci_db$"aaas"$"default"` | Matches source values. |
| `nejm` | `ggsci_db$"nejm"$"default"` | Matches source values. |
| `lancet` | `ggsci_db$"lancet"$"lanonc"` | Matches source values. |
| `jama` | `ggsci_db$"jama"$"default"` | Added from source values. |
| `bmj` | `ggsci_db$"bmj"$"default"` | Matches source values. |
| `jco` | `ggsci_db$"jco"$"default"` | Fixed to include the 10th source color, `#4A6990`. |
| `frontiers` | `ggsci_db$"frontiers"$"default"` | Added from source values. |

## Exact Values

```text
npg:
  #E64B35 #4DBBD5 #00A087 #3C5488 #F39B7F
  #8491B4 #91D1C2 #DC0000 #7E6148 #B09C85

science / aaas:
  #3B4992 #EE0000 #008B45 #631879 #008280
  #BB0021 #5F559B #A20056 #808180 #1B1919

nejm:
  #BC3C29 #0072B5 #E18727 #20854E
  #7876B1 #6F99AD #FFDC91 #EE4C97

lancet:
  #00468B #ED0000 #42B540 #0099B4 #925E9F
  #FDAF91 #AD002A #ADB6B6 #1B1919

jama:
  #374E55 #DF8F44 #00A1D5 #B24745
  #79AF97 #6A6599 #80796B

bmj:
  #2A6EBB #F0AB00 #C50084 #7D5CC6 #E37222
  #69BE28 #00B2A9 #CD202C #747678

jco:
  #0073C2 #EFC000 #868686 #CD534C #7AA6DC
  #003C67 #8F7700 #3B3B3B #A73030 #4A6990

frontiers:
  #D51317 #F39200 #EFD500 #95C11F #007B3D
  #31B7BC #0094CD #164194 #6F286A #706F6F
```

## Notes

- `science` is kept as the public preset name for compatibility, with `aaas`
  available as an alias.
- `lancet` follows the `lanonc` palette in `ggsci`.
- `jco` previously exposed the alias `jco10` but only included 9 colors. The
  missing 10th color was restored.
- `jama` and `frontiers` were added because they are journal/publisher palettes
  present in the same source family as the existing journal presets.
