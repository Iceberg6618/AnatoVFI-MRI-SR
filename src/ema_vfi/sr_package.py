import copy
import torch
import numpy as np
import nibabel as nib
from tqdm import tqdm

from .model import feature_extractor, flow_estimation
from .model.configs import CONFIGS

def forward(images, model, t):
    images = images.to(next(model.parameters()).device)
    with torch.no_grad():
        _, _, _, out = model(images, t)
    return out.detach().cpu().numpy()

def forward_small(images, model, t):
    target_shape = (256, 256)

    b, c, h, w = images.shape

    padded_input = torch.zeros((b, c, target_shape[0], target_shape[1]))
    padded_input[:, :, :h, :w] += images
    padded_input = padded_input.to(next(model.parameters()).device)

    with torch.no_grad():
        _, _, _, out = model(padded_input, t)
    
    out = out.detach().cpu().numpy().squeeze()
    out = out[:h, :w]
    return out

def forward_large(images, model, t, stride=256):
    _, _, h, w = images.shape
    output, cnt = torch.zeros((h, w)), torch.zeros((h, w))

    for x in range(0, w-stride-1, stride):
        for y in range(0, h-stride-1, stride):
            patch = images[:,:,y:y+stride,x:x+stride]
            patch = patch.to(next(model.parameters()).device)
            with torch.no_grad():
                _, _, _, out = model(patch, t)
            out = out.detach().cpu()
            output[y:y+stride,x:x+stride] += out.squeeze()
            cnt[y:y+stride,x:x+stride] += 1
    
    for x in range(0, w-stride-1, stride):
        patch = images[:,:,-stride:,x:x+stride]
        patch = patch.to(next(model.parameters()).device)
        with torch.no_grad():
            _, _, _, out = model(patch, t)
        out = out.detach().cpu()
        output[-stride:,x:x+stride] += out.squeeze()
        cnt[-stride:,x:x+stride] += 1

    for y in range(0, h-stride-1, stride):
        patch = images[:,:,y:y+stride,-stride:]
        patch = patch.to(next(model.parameters()).device)
        with torch.no_grad():
            _, _, _, out = model(patch, t)
        out = out.detach().cpu()
        output[y:y+stride,-stride:] += out.squeeze()
        cnt[y:y+stride,-stride:] += 1

    last_patch = images[:,:,-stride:,-stride:]
    last_patch = last_patch.to(next(model.parameters()).device)
    with torch.no_grad():
        _, _, _, out = model(last_patch, t)
    out = out.detach().cpu()
    output[-stride:,-stride:] += out.squeeze()
    cnt[-stride:,-stride:] += 1

    output/=cnt
    return output.numpy()

def forward_complex(images, model, t):
    b, c, h, w = images.shape
    if h < 256:
        padded_input = torch.zeros((b, c, 256, w))
    elif w < 256:
        padded_input = torch.zeros((b, c, h, 256))
    padded_input[:, :, :h, :w] += images
    out = forward_large(padded_input, model, t)
    out = out[:h, :w]
    return out


class SRPackage:
    def __init__(self, chkpnt_dir, device='cpu'):
        self.device = device
        chkpnt_path = chkpnt_dir

        ########## Do not change these codes ##########
        self.model = flow_estimation(feature_extractor(**CONFIGS), **CONFIGS)
        self.model.load_state_dict(torch.load(chkpnt_path, map_location=device), strict=False)
        self.model = self.model.to(device)
        self.model.eval()
        ###############################################
  
    def upsample_nii(self, nii:nib.Nifti1Image, upsample_factor=4, target_size=None, replace_orig_slice=False):
        # Getting axial plane's index.
        aff_code = np.array(nib.orientations.aff2axcodes(nii.affine))
        if 'S' in aff_code: idx = np.where(aff_code == 'S')[0][0]
        else: idx = np.where(aff_code == 'I')[0][0]

        # Setting slice thickness (or spacing).
        spacing = list(nii.header.get_zooms())
        new_spacing = spacing
        new_spacing[idx] /= upsample_factor

        arr = nii.get_fdata()
        orig_max = np.max(arr)
        arr /= orig_max

        arr = np.array_split(arr, arr.shape[idx], axis=idx)
        arr = self.upsample(arr, upsample_factor, target_size=target_size)

        upsampled_nii = self.arr2nii(copy.deepcopy(arr), orig_max, upsample_factor, idx, nii)

        if replace_orig_slice:
            arr2 = self.replace_orig_slice(arr, upsample_factor)
            upsampled_nii2 = self.arr2nii(copy.deepcopy(arr2), orig_max, upsample_factor, idx, nii)
            return upsampled_nii, upsampled_nii2

        return upsampled_nii
    
    def upsample(self, array, upsample_factor, target_size=None):
        result = [copy.deepcopy(array)[0].squeeze()]
        for i in tqdm(range(len(array)-1), total=len(array)-1):
            for j in range(1, upsample_factor):
                timestep = 1 / upsample_factor * j
                x0, x1 = copy.deepcopy(array[i]), copy.deepcopy(array[i+1])
                result.append(self._synthesize_intermediate_slice(x0, x1, timestep))
            result.append(x1.squeeze())
        
        if target_size is not None:
            while len(result) < target_size:
                result.append(np.zeros_like(result[-1]))
        
        return result
    
    def replace_orig_slice(self, array, upsample_factor):
        for i in tqdm(range(0+upsample_factor, len(array), upsample_factor)):
            array[i] = self._synthesize_intermediate_slice(array[i-1], array[i+1], t=0.5)
        return array
    
    def arr2nii(self, arr, scale, upsample_factor, axial_idx, orig_nii):
        arr = np.stack(arr, axis=axial_idx)
        arr *= scale
        arr = arr.astype(np.uint8)
        
        spacing = list(orig_nii.header.get_zooms())
        new_spacing = spacing
        new_spacing[axial_idx] /= upsample_factor

        nii = nib.Nifti1Image(arr, orig_nii.affine, orig_nii.header)
        nii.header.set_zooms(new_spacing)
        return nii

    def _synthesize_intermediate_slice(self, x0, x1, t):
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        if isinstance(x0, np.ndarray): x0 = torch.tensor(x0).squeeze()
        if isinstance(x1, np.ndarray): x1 = torch.tensor(x1).squeeze()

        h, w = x0.shape
        if h == 256 and w == 256:
            forward_call = forward
        elif h <= 256 and w <= 256:
            forward_call = forward_small
        elif h >= 256 and w >= 256:
            forward_call = forward_large
        else:
            forward_call = forward_complex
        
        x = torch.stack((x0, x0, x0, x1, x1, x1), dim=0).unsqueeze(0).to(self.device, dtype=torch.float32)
        return forward_call(x, self.model, t).squeeze()
