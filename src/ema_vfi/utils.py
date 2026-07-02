import numpy as np
import nibabel as nib
import SimpleITK as sitk

def get_axial_idx(nii:nib.Nifti1Image):
    aff_code = np.array(nib.orientations.aff2axcodes(nii.affine))
    if 'S' in aff_code: return  np.where(aff_code == 'S')[0][0]
    else: return np.where(aff_code == 'I')[0][0]

def get_axial_idx_sitk(nii:sitk.Image):
    direction = np.array(nii.GetDirection()).reshape(3, 3)
    axial_direction = np.abs(direction[:, 2])
    idx = np.argmax(axial_direction)
    return idx

