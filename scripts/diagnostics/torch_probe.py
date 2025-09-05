import sys
info = {}
try:
    import torch
    info["torch"] = torch.__version__
    info["cuda_available"] = torch.cuda.is_available()
    if info["cuda_available"]:
        info["device_name"] = torch.cuda.get_device_name(0)
except Exception as e:
    info["error"] = repr(e)
print(info)
sys.exit(0 if "torch" in info else 1)
