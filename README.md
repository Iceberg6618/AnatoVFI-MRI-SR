# Flexible Anatomical-Aware MRI Super-Resolution

Archived research code, draft manuscript, and intermediate quantitative results for an unfinished/deprecated project on anisotropic structural MRI super-resolution using EMA-VFI-style slice interpolation.

This repository is preserved for reference. It is not an actively maintained package, and the manuscript in `docs/draft_250206.pdf` was not completed or published.

## Project Status

- Status: archived / deprecated research prototype
- Draft manuscript: `docs/draft_250206.pdf`
- Main code: `src/ema_vfi/`
- Intermediate result summaries: `legacy_results/`
- Training code status: a complete standalone training pipeline was not present in the archived workspace. The public code focuses on EMA-VFI inference, preprocessing, and evaluation helpers.

## Research Background

High-resolution structural MRI is important for visual inspection, diagnosis, and downstream computational analyses such as segmentation, registration, and anomaly detection. However, acquiring high-resolution MRI can increase scan time and motion sensitivity. One practical alternative is to acquire lower-resolution scans and reconstruct high-resolution volumes computationally.

Many 3D medical images are anisotropic: the in-plane resolution is relatively high, while the through-plane slice spacing is coarse. A common strategy is therefore to reformulate 3D super-resolution as slice interpolation:

1. Split the anisotropic 3D volume into 2D slices along the low-resolution axis.
2. Synthesize missing intermediate slices.
3. Stack original and synthesized slices back into a higher-resolution 3D volume.

The draft argues that two limitations remain in many MRI-SR approaches:

- Fixed-scale behavior: models often target a specific upsampling factor and are less flexible for arbitrary through-plane spacing.
- Weak anatomical awareness: intensity similarity metrics alone do not guarantee preservation of tissue boundaries or clinically relevant structures.

## Core Idea

The project treats anisotropic MRI super-resolution as a video frame interpolation (VFI) problem. Adjacent MRI slices are analogous to neighboring video frames, and missing through-plane slices are analogous to intermediate frames.

The adopted backbone is EMA-VFI, a flow-based video frame interpolation model. The intuition is that optical-flow-style correspondence can model structural transitions between adjacent anatomical slices and synthesize intermediate slices at arbitrary fractional positions.

For an input slice pair `I_n` and `I_{n+1}`, the model generates an intermediate slice `I_{n+t}` for arbitrary `t` in `(0, 1)`. To upsample by factor `k`, it synthesizes `k - 1` intermediate slices between each adjacent slice pair and reconstructs the 3D super-resolved volume.

## Planned Contributions From The Draft

The draft manuscript proposed the following contributions:

- Reframe anisotropic structural MRI super-resolution as a VFI-based slice interpolation task.
- Adapt EMA-VFI for through-plane MRI slice synthesis and flexible upsampling factors.
- Use segmentation maps to make the reconstruction more anatomy-aware.
- Introduce a Label-Transition Flow (LTF) loss that encourages optical flow to focus on regions where anatomical labels change between slices.
- Evaluate not only image similarity metrics such as SSIM and PSNR, but also anatomical metrics such as Dice scores and hippocampal volume preservation.

Because the research was discontinued, these should be read as archived research aims and partial experimental evidence, not as final paper claims.

## Method Summary

### Downsampling

To create paired LR/HR data, the draft follows a thick-slice simulation procedure:

- Blur the original HR volume along the axial direction with a Gaussian filter.
- Set the full-width at half maximum (FWHM) to match the target slice thickness.
- Select every `k`-th slice to simulate larger through-plane spacing.

Training factors mentioned in the draft: `k in {2, 3, 4, 5, 6}`.

Evaluation factors mentioned in the draft: `k in {2, 4, 6}`.

### Segmentation

The draft used SynthSeg-style structural segmentation maps, simplified into five labels:

- Background
- Cerebrospinal fluid (CSF)
- Ventricle
- Gray matter (GM)
- White matter (WM)

These segmentation maps were used for skull stripping and for the proposed anatomy-aware loss.

### Model

The selected model family was EMA-VFI, based on motion estimation and appearance/feature refinement through inter-frame attention. In this project, adjacent MRI slices replace adjacent video frames.

### Objective

The draft describes a weighted loss:

```text
L = lambda_1 * L_MAE + lambda_2 * L_Grad + lambda_3 * L_LTF
```

- `L_MAE`: mean absolute error between synthesized and ground-truth HR slices.
- `L_Grad`: gradient loss for preserving edge sharpness and local structure.
- `L_LTF`: Label-Transition Flow loss, intended to emphasize regions where segmentation labels change between adjacent/intermediate slices.

The draft fixes `lambda_1 = 1` and `lambda_2 = 1`, then discusses `lambda_3` as an ablation parameter.

### Training Details From The Draft

- Dataset: 1,000 ADNI T1-weighted MRIs.
- Split: train/validation/test = 8:1:1.
- External evaluation plan: IXI T1-weighted MRI, 100 selected subjects, without additional fine-tuning.
- Optimizer: AdamW.
- Learning rate: `2e-4`.
- Betas: `beta_1 = 0.9`, `beta_2 = 0.999`.
- Weight decay: `1e-4`.
- Epochs: 30.
- Batch size: 32.
- GPU: single NVIDIA RTX A6000.
- Best model selection: highest validation SSIM.

## Repository Layout

```text
.
|-- README.md
|-- requirements.txt
|-- docs/
|   `-- draft_250206.pdf
|-- src/
|   `-- ema_vfi/
|       |-- inference.py
|       |-- sr_package.py
|       |-- downsampling.py
|       |-- upsampling.py
|       |-- similarity_scoring.py
|       |-- anatomy_scoring.py
|       |-- utils.py
|       `-- model/
`-- legacy_results/
    |-- 240627/
    |-- 240819/
    |-- 240902/
    |-- 240906/
    |-- 241011/
    |-- 241115/
    `-- 241122/
```

## Code Overview

- `src/ema_vfi/model/`: EMA-VFI model definition used for checkpoint loading and inference.
- `src/ema_vfi/sr_package.py`: NIfTI super-resolution wrapper around the EMA-VFI model.
- `src/ema_vfi/inference.py`: command-line inference entry point.
- `src/ema_vfi/downsampling.py`: thick-slice/downsampling helper for preparing low-resolution inputs.
- `src/ema_vfi/upsampling.py`: conventional interpolation baseline and EMA-VFI upsampling helper.
- `src/ema_vfi/similarity_scoring.py`: PSNR/SSIM scoring helpers.
- `src/ema_vfi/anatomy_scoring.py`: hippocampus/gray-matter Dice and volume scoring helpers.
- `legacy_results/`: dated result summaries, figures, CSV files, and presentation files.

## Quantitative Results

The tables below summarize every numeric score column preserved in the archived score CSVs. Values are reported as mean/min/max over the rows in each result file, so the main quantitative results can be read directly from this README without opening the CSV files.

Notes on duplicated score files:

- `legacy_results/240627/scores/psnr.csv` contains the same PSNR columns already included in the 2024-06-27 similarity table.
- `legacy_results/240819/PSNR2.csv` is the standalone version of the `current2` PSNR column in the 2024-08-19 PSNR comparison table.
- `legacy_results/240819/SSIM2.csv` is the standalone version of the `current2` SSIM column in the 2024-08-19 SSIM comparison table.
- `legacy_results/240627/information.csv` records image orientation, spacing, and shape metadata rather than model scores.

### 2024-06-27 Similarity Scores

Experiment size: 35 rows. Metrics compare the proposed reconstruction against linear interpolation across axial, coronal, and sagittal directions.

| Metric | Mean | Min | Max |
|---|---:|---:|---:|
| `ssim_2x_axial` | 0.9841 | 0.9674 | 0.9940 |
| `psnr_2x_axial` | 39.3333 | 35.5208 | 47.9553 |
| `ssim_4x_axial` | 0.9536 | 0.9100 | 0.9788 |
| `psnr_4x_axial` | 34.0568 | 30.5423 | 41.3320 |
| `ssim_2x_coronal` | 0.9854 | 0.9706 | 0.9947 |
| `psnr_2x_coronal` | 39.7616 | 36.1312 | 47.6009 |
| `ssim_4x_coronal` | 0.9495 | 0.9151 | 0.9785 |
| `psnr_4x_coronal` | 33.5993 | 30.7249 | 41.0002 |
| `ssim_2x_sagittal` | 0.9824 | 0.9684 | 0.9933 |
| `psnr_2x_sagittal` | 38.4019 | 34.9308 | 45.7534 |
| `ssim_4x_sagittal` | 0.9391 | 0.8965 | 0.9699 |
| `psnr_4x_sagittal` | 32.4709 | 28.8690 | 38.7170 |
| `ssim_2x_axial_linear` | 0.9756 | 0.9456 | 0.9904 |
| `psnr_2x_axial_linear` | 36.1389 | 31.5526 | 44.3574 |
| `ssim_4x_axial_linear` | 0.9173 | 0.8519 | 0.9546 |
| `psnr_4x_axial_linear` | 30.3973 | 28.1346 | 37.1751 |
| `ssim_2x_coronal_linear` | 0.9775 | 0.8944 | 0.9954 |
| `psnr_2x_coronal_linear` | 37.0026 | 33.2399 | 46.2176 |
| `ssim_4x_coronal_linear` | 0.9267 | 0.8555 | 0.9701 |
| `psnr_4x_coronal_linear` | 30.9141 | 27.9031 | 36.9336 |
| `ssim_2x_sagittal_linear` | 0.9730 | 0.8903 | 0.9941 |
| `psnr_2x_sagittal_linear` | 36.1813 | 32.9653 | 44.8316 |
| `ssim_4x_sagittal_linear` | 0.9141 | 0.8467 | 0.9657 |
| `psnr_4x_sagittal_linear` | 30.1562 | 27.4315 | 36.5583 |

### 2024-06-27 Dice Scores

Experiment size: 35 rows. Dice scores compare structural consistency for downsampled and upsampled volumes.

| Metric | Mean | Min | Max |
|---|---:|---:|---:|
| `2x_downsampled_axial` | 0.9503 | 0.9241 | 0.9674 |
| `4x_downsampled_axial` | 0.8449 | 0.7536 | 0.8827 |
| `2x_downsampled_coronal` | 0.9592 | 0.9340 | 0.9892 |
| `4x_downsampled_coronal` | 0.8743 | 0.8051 | 0.9557 |
| `2x_downsampled_sagittal` | 0.9517 | 0.9030 | 0.9889 |
| `4x_downsampled_sagittal` | 0.8428 | 0.7083 | 0.9572 |
| `2x_upsampled_axial` | 0.9627 | 0.8658 | 0.9759 |
| `4x_upsampled_axial` | 0.9274 | 0.7836 | 0.9496 |
| `2x_upsampled_coronal` | 0.9643 | 0.8708 | 0.9817 |
| `4x_upsampled_coronal` | 0.9212 | 0.8019 | 0.9664 |
| `2x_upsampled_sagittal` | 0.9618 | 0.8477 | 0.9818 |
| `4x_upsampled_sagittal` | 0.9125 | 0.7006 | 0.9657 |

### 2024-08-19 PSNR Comparison

Experiment size: 40 rows.

| Metric | Mean | Min | Max |
|---|---:|---:|---:|
| `current` | 36.3661 | 33.7377 | 39.6391 |
| `previous` | 37.5529 | 35.1847 | 39.5739 |
| `linear` | 34.0559 | 32.2049 | 36.4872 |
| `current2` | 38.1707 | 35.6387 | 40.2034 |

### 2024-08-19 SSIM Comparison

Experiment size: 40 rows.

| Metric | Mean | Min | Max |
|---|---:|---:|---:|
| `current` | 0.9844 | 0.9789 | 0.9890 |
| `previous` | 0.9847 | 0.9799 | 0.9884 |
| `linear` | 0.9670 | 0.9587 | 0.9738 |
| `current2` | 0.9866 | 0.9822 | 0.9897 |

### 2024-10-11 PSNR Ablation

Experiment size: 10 rows. This ablation compares segmentation-map variants, original-slice replacement variants, SynthSR, and B-spline interpolation.

| Metric | Mean | Min | Max |
|---|---:|---:|---:|
| `segmap_not_applied` | 33.1745 | 30.2734 | 37.0403 |
| `segmap_not_applied_replace_orig_slice` | 33.3202 | 30.4984 | 37.1570 |
| `segmap_applied_0.1` | 33.1659 | 30.2070 | 36.8417 |
| `segmap_applied_0.1_replace_orig_slice` | 33.3193 | 30.4138 | 36.9271 |
| `segmap_applied_0.5` | 33.2202 | 30.3281 | 36.9214 |
| `segmap_applied_0.5_replace_orig_slice` | 33.3079 | 30.5656 | 36.8992 |
| `SynthSR` | 23.4233 | 19.0847 | 30.1111 |
| `bspline` | 31.3340 | 28.4494 | 35.0482 |

### 2024-10-11 SSIM Ablation

Experiment size: 10 rows.

| Metric | Mean | Min | Max |
|---|---:|---:|---:|
| `segmap_not_applied` | 0.9610 | 0.9456 | 0.9820 |
| `segmap_not_applied_replace_orig_slice` | 0.9630 | 0.9486 | 0.9825 |
| `segmap_applied_0.1` | 0.9611 | 0.9451 | 0.9816 |
| `segmap_applied_0.1_replace_orig_slice` | 0.9632 | 0.9480 | 0.9819 |
| `segmap_applied_0.5` | 0.9621 | 0.9471 | 0.9817 |
| `segmap_applied_0.5_replace_orig_slice` | 0.9641 | 0.9506 | 0.9817 |
| `SynthSR` | 0.8812 | 0.8355 | 0.9571 |
| `bspline` | 0.9395 | 0.9181 | 0.9736 |

### 2024-10-11 Hippocampus Dice

Experiment size: 10 rows.

| Metric | Mean | Min | Max |
|---|---:|---:|---:|
| `segmap_applied_0.1` | 0.8750 | 0.8094 | 0.9090 |
| `segmap_applied_0.1_replace_orig_slice` | 0.8835 | 0.8401 | 0.9126 |
| `segmap_applied_0.5` | 0.8813 | 0.8468 | 0.9117 |
| `segmap_applied_0.5_replace_orig_slice` | 0.8919 | 0.8577 | 0.9141 |
| `segmap_not_applied` | 0.8640 | 0.6896 | 0.9071 |
| `segmap_not_applied_replace_orig_slice` | 0.8744 | 0.7402 | 0.9147 |
| `SynthSR` | 0.7899 | 0.6442 | 0.8614 |

### 2024-10-11 Gray Matter Dice

Experiment size: 10 rows.

| Metric | Mean | Min | Max |
|---|---:|---:|---:|
| `segmap_applied_0.1` | 0.8701 | 0.8432 | 0.8970 |
| `segmap_applied_0.1_replace_orig_slice` | 0.8709 | 0.8345 | 0.9004 |
| `segmap_applied_0.5` | 0.8714 | 0.8437 | 0.8975 |
| `segmap_applied_0.5_replace_orig_slice` | 0.8719 | 0.8421 | 0.8996 |
| `segmap_not_applied` | 0.8705 | 0.8378 | 0.8968 |
| `segmap_not_applied_replace_orig_slice` | 0.8710 | 0.8318 | 0.8990 |
| `SynthSR` | 0.7822 | 0.7627 | 0.8098 |

### 2024-10-11 Hippocampus Volume

Experiment size: 10 rows. Units follow the original archived result table.

| Metric | Mean | Min | Max |
|---|---:|---:|---:|
| `orig_hr` | 7147.5000 | 4688.0000 | 10824.0000 |
| `segmap_applied_0.1` | 7499.0000 | 5020.0000 | 11386.0000 |
| `segmap_applied_0.1_replace_orig_slice` | 7178.1000 | 4790.0000 | 10861.0000 |
| `segmap_applied_0.5` | 7375.2000 | 4809.0000 | 10408.0000 |
| `segmap_applied_0.5_replace_orig_slice` | 7041.4000 | 4829.0000 | 10246.0000 |
| `segmap_not_applied` | 7420.9000 | 4227.0000 | 10776.0000 |
| `segmap_not_applied_replace_orig_slice` | 7149.4000 | 4888.0000 | 10330.0000 |
| `SynthSR` | 8579.5000 | 4974.0000 | 11931.0000 |

## Result Takeaways

- The 2024-06-27 experiment showed consistently higher mean PSNR/SSIM for the proposed reconstruction than linear interpolation across all reported directions and factors.
- The 2024-08-19 experiment showed `current2` as the strongest variant among the archived labels, with mean PSNR 38.1707 and mean SSIM 0.9866.
- The 2024-10-11 ablation showed the strongest mean SSIM for `segmap_applied_0.5_replace_orig_slice` (0.9641), while the strongest mean PSNR was `segmap_not_applied_replace_orig_slice` (33.3202).
- For anatomy-aware metrics in the 2024-10-11 experiment, `segmap_applied_0.5_replace_orig_slice` had the best mean hippocampus Dice (0.8919) and best mean gray matter Dice (0.8719).

## Data and Privacy Notes

Raw medical images are not included. This archive contains code, small metric tables, figures, and presentation files only.

The following files from the original workspace were intentionally excluded from this Git-ready copy:

- Python caches: `__pycache__/`, `*.pyc`
- Model checkpoints: `*.pth`
- Large/local-data metadata table: `EMA-VFI_results/241108/demo.csv`
- Subject-list text file: `EMA-VFI_results/240906/ADNI_subject_lists.txt`

If the excluded checkpoint files are needed, store them outside Git or use Git LFS with access controls appropriate for the project.

## Environment

Install the approximate Python dependencies:

```bash
pip install -r requirements.txt
```

The trimmed code uses PyTorch, NumPy, Nibabel, SimpleITK, SciPy, scikit-image, pandas, matplotlib, timm, and tqdm.

## Minimal Usage Examples

Generate a downsampled NIfTI input:

```python
import nibabel as nib
from src.ema_vfi.downsampling import downsample

nii = nib.load("input_hr.nii.gz")
lr_nii = downsample(nii, k=4, blur=True)
nib.save(lr_nii, "input_lr_4x.nii.gz")
```

Run EMA-VFI inference:

```bash
python -m src.ema_vfi.inference \
  --input input_lr_4x.nii.gz \
  --output output_sr.nii.gz \
  --checkpoint checkpoints/model_epoch_segmap_0.5.pth \
  --factor 4 \
  --device cuda:0
```
