import argparse
import os

import nibabel as nib

from .sr_package import SRPackage


def parse_args():
    parser = argparse.ArgumentParser(description="Run EMA-VFI MRI slice super-resolution inference.")
    parser.add_argument("--input", required=True, help="Input low-resolution NIfTI path.")
    parser.add_argument("--output", required=True, help="Output super-resolved NIfTI path.")
    parser.add_argument("--checkpoint", required=True, help="EMA-VFI checkpoint path.")
    parser.add_argument("--factor", type=int, default=4, help="Upsampling factor along the axial direction.")
    parser.add_argument("--target-size", type=int, default=None, help="Optional target slice count.")
    parser.add_argument("--device", default="cpu", help="Torch device, e.g. cpu or cuda:0.")
    parser.add_argument("--replace-orig-slice", action="store_true", help="Also synthesize replacement original-slice volume.")
    return parser.parse_args()


def main():
    args = parse_args()
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)

    sr = SRPackage(chkpnt_dir=args.checkpoint, device=args.device)
    nii = nib.load(args.input)
    result = sr.upsample_nii(
        nii,
        upsample_factor=args.factor,
        target_size=args.target_size,
        replace_orig_slice=args.replace_orig_slice,
    )

    if args.replace_orig_slice:
        upsampled, replaced = result
        nib.save(upsampled, args.output)
        root, ext = os.path.splitext(args.output)
        if root.endswith(".nii"):
            root, ext2 = os.path.splitext(root)
            ext = ext2 + ext
        nib.save(replaced, f"{root}_orig_slice_replaced{ext}")
    else:
        nib.save(result, args.output)


if __name__ == "__main__":
    main()
