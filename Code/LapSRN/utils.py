from PIL import Image
import os
from torch.utils.data.dataset import Dataset
from torchvision.transforms import ToTensor
import random
import torch
import numpy as np
import scipy.io as io
import torch.nn.functional as F

def is_image_file(filename):
    return any(filename.endswith(extension) for extension in ['.png', '.jpg', '.jpeg', '.PNG', '.JPG', '.JPEG','.bmp'])

class TrainSetLoader(Dataset):
    def __init__(self, dataset_dir):
        super(TrainSetLoader, self).__init__()
        self.dataset_dir = dataset_dir
        self.file_list = os.listdir(dataset_dir + '/patch_dataset_x4')
        # self.upscale_factor = upscale_factor
        self.tranform = Compose([
            augumentation(),
        ])
    def __getitem__(self, index):
        hr_image_left = Image.open(self.dataset_dir + '/patch_dataset_x4/' + self.file_list[index] + '/hr0.png')
        hr_image_right = Image.open(self.dataset_dir + '/patch_dataset_x4/' + self.file_list[index] + '/hr1.png')
        lr_image_left = Image.open(self.dataset_dir + '/patch_dataset_x4/' + self.file_list[index] +  '/lr0.png')
        lr_image_right = Image.open(self.dataset_dir + '/patch_dataset_x4/' + self.file_list[index] + '/lr1.png')
        hr = np.array(hr_image_left, dtype=np.float32)
        w, h, c = hr.shape
        lr2_image_left = np.array(hr_image_left.resize((int(h/2),int(w/2)),Image.BICUBIC), dtype=np.float32)
        lr2_image_right = np.array(hr_image_right.resize((int(h/2),int(w/2)),Image.BICUBIC), dtype=np.float32)
        hr_image_left = np.array(hr_image_left, dtype=np.float32)
        hr_image_right = np.array(hr_image_right, dtype=np.float32)
        lr_image_left = np.array(lr_image_left, dtype=np.float32)
        lr_image_right = np.array(lr_image_right, dtype=np.float32)

        hr_image_left, hr_image_right, lr_image_left, lr_image_right, lr2_image_left, lr2_image_right = self.tranform(hr_image_left, hr_image_right,
                                                                                     lr_image_left, lr_image_right,
                                                                                     lr2_image_left, lr2_image_right)
        hr_image_left, hr_image_right, lr_image_left, lr_image_right, lr2_image_left, lr2_image_right = ndarray2tensor()(hr_image_left, hr_image_right,
                                                                                                                         lr_image_left, lr_image_right,
                                                                                                                         lr2_image_left, lr2_image_right)
        return hr_image_left, hr_image_right, lr_image_left, lr_image_right, lr2_image_left, lr2_image_right
    def __len__(self):
        return len(self.file_list)

class ValSetLoader(Dataset):
    def __init__(self, dataset_dir):
        super(ValSetLoader, self).__init__()
        self.dataset_dir = dataset_dir
        self.file_list = os.listdir(dataset_dir + '/patch_dataset_x4')

    def __getitem__(self, index):
        hr_image_left = Image.open(self.dataset_dir + '/patch_dataset_x4/' + self.file_list[index] + '/hr0.png')
        hr_image_right = Image.open(self.dataset_dir + '/patch_dataset_x4/' + self.file_list[index] + '/hr1.png')
        lr_image_left = Image.open(self.dataset_dir + '/patch_dataset_x4/' + self.file_list[index] + '/lr0.png')
        lr_image_right = Image.open(self.dataset_dir + '/patch_dataset_x4/' + self.file_list[index] + '/lr1.png')
        hr_image_left = np.array(hr_image_left, dtype=np.float32)
        hr_image_right = np.array(hr_image_right, dtype=np.float32)
        lr_image_left = np.array(lr_image_left, dtype=np.float32)
        lr_image_right = np.array(lr_image_right, dtype=np.float32)
        hr_image_left = ToTensor()(hr_image_left)
        hr_image_right = ToTensor()(hr_image_right)
        lr_image_left = ToTensor()(lr_image_left)
        lr_image_right = ToTensor()(lr_image_right)
        return hr_image_left, hr_image_right, lr_image_left, lr_image_right

    def __len__(self):
        return len(self.file_list)

class TestSetLoader(Dataset):
    def __init__(self, dataset_dir, scale_factor):
        super(TestSetLoader, self).__init__()
        self.dataset_dir = dataset_dir
        self.scale_factor = scale_factor
        self.file_list = os.listdir(dataset_dir + '/hr')
    def __getitem__(self, index):
        hr_image_left  = Image.open(self.dataset_dir + '/hr/' + self.file_list[index] + '/hr0.png')
        lr_image_left  = Image.open(self.dataset_dir + '/lr_x' + str(self.scale_factor) + '/' + self.file_list[index] + '/lr0.png')
        lr_image_right = Image.open(self.dataset_dir + '/lr_x' + str(self.scale_factor) + '/' + self.file_list[index] + '/lr1.png')
        hr_image_left = np.array(hr_image_left, dtype=np.float32)
        w, h, c = hr_image_left.shape
        lr_image_left_x4 = np.array(lr_image_left.resize((h, w), Image.BICUBIC), dtype=np.float32)
        lr_image_left = np.array(lr_image_left, dtype=np.float32)
        lr_image_right = np.array(lr_image_right, dtype=np.float32)
        hr_image_left, lr_image_left, lr_image_right, lr_image_left_x4 = ndarray2tensor()(hr_image_left,lr_image_left,
                                                                           lr_image_right, lr_image_left_x4)
        return hr_image_left, lr_image_left, lr_image_right, lr_image_left_x4
    def __len__(self):
        return len(self.file_list)

def rgb2y(img):
    img_r = img[:, 0, :, :]
    img_g = img[:, 1, :, :]
    img_b = img[:, 2, :, :]
    image_y = torch.round(0.257 * torch.unsqueeze(img_r, 1) + 0.504 * torch.unsqueeze(img_g, 1) + 0.098 * torch.unsqueeze(img_b, 1) + 16)
    return image_y

class Compose(object):
    def __init__(self, co_transforms):
        self.co_transforms = co_transforms
    def __call__(self, hr_image_left, hr_image_right, lr_image_left, lr_image_right, lr_image_left2, lr_image_right2):
        for transform in self.co_transforms:
            hr_image_left, hr_image_right, lr_image_left, lr_image_right, lr_image_left2, lr_image_right2 = transform(hr_image_left, hr_image_right, lr_image_left, lr_image_right, lr_image_left2, lr_image_right2)
        return hr_image_left, hr_image_right, lr_image_left, lr_image_right, lr_image_left2, lr_image_right2

class random_crop(object):
    def __init__(self, crop_size, upscale_factor):
        self.crop_size = crop_size
        self.upscale_factor = upscale_factor
    def __call__(self, hr_image_left, hr_image_right, lr_image_left, lr_image_right):
        lr_image_left = np.array(lr_image_left, dtype=np.float32)
        lr_image_right = np.array(lr_image_right, dtype=np.float32)
        hr_image_left = np.array(hr_image_left, dtype=np.float32)
        hr_image_right = np.array(hr_image_right, dtype=np.float32)
        h, w, _ = lr_image_left.shape
        start_x_input = random.randint(1, h-self.crop_size[0]-1)
        start_y_input = random.randint(1, w-self.crop_size[1]-1)
        start_x_target = start_x_input * self.upscale_factor
        start_y_target = start_y_input * self.upscale_factor

        lr_image_left = lr_image_left[start_x_input: start_x_input + self.crop_size[0], start_y_input: start_y_input + self.crop_size[1], :]
        lr_image_right = lr_image_right[start_x_input: start_x_input + self.crop_size[0],
                        start_y_input: start_y_input + self.crop_size[1], :]
        hr_image_left = hr_image_left[start_x_target: start_x_target + self.crop_size[0] * self.upscale_factor,
                        start_y_target: start_y_target + self.crop_size[1] * self.upscale_factor, :]
        hr_image_right = hr_image_right[start_x_target: start_x_target + self.crop_size[0] * self.upscale_factor,
                        start_y_target: start_y_target + self.crop_size[1] * self.upscale_factor, :]
        return hr_image_left, hr_image_right, lr_image_left, lr_image_right

class augumentation(object):
    def __call__(self, hr_image_left, hr_image_right, lr_image_left, lr_image_right):
        if random.random()<0.5: # flip horizonly
            lr_image_left = lr_image_left[:, ::-1, :]
            lr_image_right = lr_image_right[:, ::-1, :]
            hr_image_left = hr_image_left[:, ::-1, :]
            hr_image_right = hr_image_right[:, ::-1, :]
        if random.random()<0.5: #flip vertically
            lr_image_left = lr_image_left[::-1, :, :]
            lr_image_right = lr_image_right[::-1, :, :]
            hr_image_left = hr_image_left[::-1, :, :]
            hr_image_right = hr_image_right[::-1, :, :]
        """"no rotation
        if random.random()<0.5:
            lr_image_left = lr_image_left.transpose(1, 0, 2)
            lr_image_right = lr_image_right.transpose(1, 0, 2)
            hr_image_left = hr_image_left.transpose(1, 0, 2)
            hr_image_right = hr_image_right.transpose(1, 0, 2)
        """
        return hr_image_left, hr_image_right, lr_image_left, lr_image_right

class ndarray2tensor(object):
    def __init__(self):
        self.totensor = ToTensor()
    def __call__(self, hr_image_left, hr_image_right, lr_image_left, lr_image_right):
        lr_image_left = self.totensor(lr_image_left.copy())
        lr_image_right = self.totensor(lr_image_right.copy())
        hr_image_left = self.totensor(hr_image_left.copy())
        hr_image_right = self.totensor(hr_image_right.copy())
        return hr_image_left, hr_image_right, lr_image_left, lr_image_right

class L1Loss(object):
    def __call__(self, input, target):
        return torch.abs(input - target).mean()