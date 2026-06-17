"""GPU runtime helpers."""

import torch


def cuda_summary() -> dict[str, str | int | bool]:
    """Return a compact CUDA availability summary."""
    available = torch.cuda.is_available()
    summary: dict[str, str | int | bool] = {
        "cuda_available": available,
        "device_count": torch.cuda.device_count(),
        "torch_version": torch.__version__,
    }

    if available:
        summary["device_name"] = torch.cuda.get_device_name(0)

    return summary
