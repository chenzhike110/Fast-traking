import torch
import torch.nn as nn
from .module_base import ModuleBase
from .common_block import conv_bn_relu

class TinyConv(nn.Module):
    r"""
    TinyNet
    Customized, extremely pruned ConvNet

    Hyper-parameters
    ----------------
    pretrain_model_path: string
        Path to pretrained backbone parameter file,
        Parameter to be loaded in _update_params_
    """
    # default_hyper_params = {"pretrain_model_path": ""}

    def __init__(self):
        super(TinyConv, self).__init__()

        self.conv1 = conv_bn_relu(3, 32, stride=2, kszie=3, pad=0)
        self.pool1 = nn.MaxPool2d(3, stride=2, padding=0, ceil_mode=True)

        self.conv2a = conv_bn_relu(32, 64, stride=1, kszie=1, pad=0)
        self.conv2b = conv_bn_relu(64, 64, stride=2, kszie=7, pad=0, groups=64)

        self.conv3a = conv_bn_relu(64, 64, stride=1, kszie=3, pad=0)
        self.conv3b = conv_bn_relu(64,
                                   64,
                                   stride=1,
                                   kszie=1,
                                   pad=0,
                                   has_relu=False)

        # initialization
        for m in self.modules():
            if isinstance(m, nn.Conv2d) or isinstance(m, nn.Linear):
                import scipy.stats as stats
                stddev = m.stddev if hasattr(m, 'stddev') else 0.1
                X = stats.truncnorm(-2, 2, scale=stddev)
                values = torch.as_tensor(X.rvs(m.weight.numel()),
                                         dtype=m.weight.dtype)
                values = values.view(m.weight.size())
                with torch.no_grad():
                    m.weight.copy_(values)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)

    def forward(self, x):
        x = self.conv1(x)
        x = self.pool1(x)

        x = self.conv2a(x)
        x = self.conv2b(x)

        x = self.conv3a(x)
        x = self.conv3b(x)

        return x
    
    def update_params(self, path=None):
        if path != None:
            try:
                state_dict = torch.load(
                    path,
                    map_location=torch.device("cuda"))
            except:
                state_dict = torch.load(
                    path,
                    map_location=torch.device("cpu"))
            self.load_state_dict(state_dict, strict=False)